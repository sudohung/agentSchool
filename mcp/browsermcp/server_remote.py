"""
Playwright MCP 服务器 - 支持远程连接

支持多种连接方式:
- stdio (本地命令行)
- http (远程浏览器/客户端) - 推荐
- sse (Server-Sent Events)
- streamable-http (流式 HTTP)
"""

from fastmcp import FastMCP
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import base64
from typing import Optional, List, Dict
import os
import argparse

# 创建 MCP 服务器实例
mcp = FastMCP("playwright-browser-mcp")

# 全局浏览器上下文 (保持状态)
_playwright = None
_browser = None
_pages = {}
_use_existing_browser = False  # 标记是否使用现有浏览器
_cdp_url = "http://127.0.0.1:9222"  # 默认 CDP URL

def get_browser(headless: bool = True):
    """获取或创建浏览器实例"""
    global _playwright, _browser, _use_existing_browser, _cdp_url

    if _browser is None:
        _playwright = sync_playwright().start()

        if _use_existing_browser:
            # 连接到已有浏览器实例（通过 CDP）
            _browser = _playwright.chromium.connect_over_cdp(_cdp_url)
            print(f" 已连接到现有浏览器实例 (CDP: {_cdp_url})")
        else:
            # 启动新的浏览器
            _browser = _playwright.chromium.launch(headless=headless)

    return _browser


def normalize_page_id(page_id: Optional[str]) -> Optional[str]:
    """标准化 page_id，接受整数或字符串"""
    if page_id is None:
        return None
    return str(page_id)


@mcp.tool()
def connect_to_existing_browser(cdp_url: str = "http://127.0.0.1:9222") -> Dict:
    """
    连接到已存在的浏览器实例

    参数:
        cdp_url: Chrome DevTools Protocol 地址 (默认: http://127.0.0.1:9222)

    返回:
        连接结果
    """
    global _browser, _playwright, _use_existing_browser

    try:
        # 如果已有浏览器连接，先关闭
        if _browser:
            try:
                _browser.close()
            except:
                pass
            _browser = None

        if _playwright:
            try:
                _playwright.stop()
            except:
                pass
            _playwright = None

        # 启动 Playwright 并连接到现有浏览器
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.connect_over_cdp(cdp_url)
        _use_existing_browser = True

        return {
            "success": True,
            "message": f"✅ 已成功连接到浏览器: {cdp_url}",
            "cdp_url": cdp_url,
            "contexts_count": len(_browser.contexts)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ 连接失败，请确保浏览器已启动并启用了远程调试"
        }


@mcp.tool()
def list_browser_contexts() -> Dict:
    """
    列出浏览器中的所有上下文和页面

    返回:
        上下文和页面列表
    """
    global _browser

    if _browser is None:
        return {"success": False, "error": "未连接到浏览器"}

    try:
        contexts_info = []
        for context in _browser.contexts:
            context_info = {
                "context_id": str(id(context)),
                "pages": []
            }
            for page in context.pages:
                context_info["pages"].append({
                    "page_id": str(id(page)),
                    "title": page.title(),
                    "url": page.url
                })
            contexts_info.append(context_info)

        return {
            "success": True,
            "contexts_count": len(contexts_info),
            "contexts": contexts_info,
            "message": f"找到 {len(contexts_info)} 个浏览器上下文"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def attach_to_existing_page(context_id: str, page_index: int = 0) -> Dict:
    """
    附加到现有浏览器中的页面

    参数:
        context_id: 浏览器上下文ID
        page_index: 页面索引（默认0，第一个页面）

    返回:
        页面信息
    """
    global _browser, _pages

    if _browser is None:
        return {"success": False, "error": "未连接到浏览器"}

    try:
        # 查找指定的上下文
        target_context = None
        for context in _browser.contexts:
            if str(id(context)) == context_id:
                target_context = context
                break

        if target_context is None:
            return {"success": False, "error": f"未找到上下文ID: {context_id}"}

        # 获取指定页面
        if page_index >= len(target_context.pages):
            return {"success": False, "error": f"页面索引 {page_index} 超出范围"}

        page = target_context.pages[page_index]
        page_id = str(id(page))
        _pages[page_id] = page

        return {
            "success": True,
            "page_id": page_id,
            "title": page.title(),
            "url": page.url,
            "message": f"✅ 已附加到页面: {page.title()}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def open_page(url: str, headless: bool = True) -> Dict:
    """
    打开网页并返回页面信息（关键：返回的 page_id 必须在后续操作中使用以保持会话）

    参数:
        url: 要打开的网页地址
        headless: 是否无头模式运行 (默认True)

    返回:
        页面信息字典,包含标题、URL、状态和 page_id（用于后续操作）
    """
    try:
        browser = get_browser(headless=headless)
        page = browser.new_page()
        page.goto(url, wait_until="load", timeout=30000)

        page_info = {
            "success": True,
            "title": page.title(),
            "url": page.url,
            "status": "loaded",
            "page_id": str(id(page))
        }

        # 保存页面引用
        _pages[page_info["page_id"]] = page

        return page_info
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }


@mcp.tool()
def get_page_info(page_id: Optional[str] = None) -> Dict:
    """
    获取页面详细信息

    参数:
        page_id: 页面ID，为空则返回所有活动页面信息

    返回:
        页面详细信息
    """
    try:
        if page_id:
            if page_id not in _pages:
                return {"success": False, "error": f"未找到页面ID: {page_id}"}

            page = _pages[page_id]
            return {
                "success": True,
                "page_id": page_id,
                "title": page.title(),
                "url": page.url,
                "status": "active"
            }
        else:
            pages_info = []
            for pid, page in _pages.items():
                try:
                    pages_info.append({
                        "page_id": pid,
                        "title": page.title(),
                        "url": page.url,
                        "status": "active"
                    })
                except:
                    pass

            return {
                "success": True,
                "count": len(pages_info),
                "pages": pages_info
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def close_page(page_id: Optional[str] = None) -> Dict:
    """
    关闭指定页面或所有页面

    参数:
        page_id: 要关闭的页面ID,为空则关闭所有页面

    返回:
        关闭结果
    """
    try:
        if page_id:
            if page_id in _pages:
                _pages[page_id].close()
                del _pages[page_id]
                return {"success": True, "message": f"页面 {page_id} 已关闭"}
            else:
                return {"success": False, "error": f"未找到页面ID: {page_id}"}
        else:
            count = len(_pages)
            for page in _pages.values():
                page.close()
            _pages.clear()
            return {"success": True, "message": f"已关闭 {count} 个页面"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def screenshot(
    page_id: Optional[str] = None,
    url: Optional[str] = None,
    path: str = "screenshot.png",
    full_page: bool = False,
    headless: bool = True
) -> Dict:
    """
    对网页进行截图

    参数:
        url: 要截图的网页地址 (如果提供了 page_id，则此参数可选)
        path: 保存路径 (默认screenshot.png)
        full_page: 是否截取完整页面 (默认False)
        headless: 是否无头模式运行
        page_id: 已有页面的ID，为空则创建新页面

    返回:
        截图结果,包含文件路径和base64数据
    """
    try:
        browser = get_browser(headless=headless)

        # 标准化 page_id（支持整数或字符串）
        if page_id is not None:
            page_id = str(page_id)

        # 使用已有页面或创建新页面
        if page_id and page_id in _pages:
            page = _pages[page_id]
        else:
            page = browser.new_page()
            if url:
                page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_timeout(1000)
            # 保存新页面引用
            page_id = str(id(page))
            _pages[page_id] = page

        page.screenshot(path=path, full_page=full_page)

        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return {
            "success": True,
            "path": path,
            "full_page": full_page,
            "base64": image_data,
            "page_id": page_id
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
def get_page_content(page_id: Optional[str] = None, url: Optional[str] = None, headless: bool = True) -> Dict:
    """
    获取网页的HTML内容和文本

    参数:
        page_id: 已有页面的ID，为空则创建新页面
        url: 网页地址 (如果提供了 page_id 且页面已打开某网址，此参数可选)
        headless: 是否无头模式运行

    返回:
        页面内容,包括HTML和纯文本
    """
    try:
        browser = get_browser(headless=headless)

        # 标准化 page_id（支持整数或字符串）
        if page_id is not None:
            page_id = str(page_id)

        # 使用已有页面或创建新页面
        if page_id and page_id in _pages:
            page = _pages[page_id]
        else:
            page = browser.new_page()
            if url:
                page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_timeout(1000)
            page_id = str(id(page))
            _pages[page_id] = page

        html = page.content()
        text = page.inner_text("body")

        return {
            "success": True,
            "url": page.url,
            "html": html,
            "text": text[:5000] + "..." if len(text) > 5000 else text,
            "page_id": page_id
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
def click_element(
    page_id: Optional[str] = None,
    selector: str = None,
    url: Optional[str] = None,
    headless: bool = True
) -> Dict:
    """
    点击页面中的指定元素

    参数:
        page_id: 已有页面的ID，为空则创建新页面
        selector: CSS选择器或文本选择器
        url: 网页地址 (如果提供了 page_id，此参数可选)
        headless: 是否无头模式运行

    返回:
        操作结果和当前页面信息
    """
    try:
        browser = get_browser(headless=headless)

        # 标准化 page_id（支持整数或字符串）
        if page_id is not None:
            page_id = str(page_id)

        # 使用已有页面或创建新页面
        if page_id and page_id in _pages:
            page = _pages[page_id]
        else:
            page = browser.new_page()
            if url:
                page.goto(url, wait_until="load", timeout=30000)
            page_id = str(id(page))
            _pages[page_id] = page

        # 如果页面没有打开网址，且提供了url，先导航
        if page.url == "about:blank" and url:
            page.goto(url, wait_until="load", timeout=30000)

        page.wait_for_selector(selector, timeout=10000)
        page.click(selector)
        page.wait_for_timeout(1000)

        result = {
            "success": True,
            "message": f"已成功点击元素: {selector}",
            "current_title": page.title(),
            "current_url": page.url,
            "page_id": page_id
        }

        return result
    except PlaywrightTimeout:
        return {"success": False, "error": f"超时: 未找到元素 {selector}", "page_id": page_id}
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
def fill_form(
    page_id: Optional[str] = None,
    selector: str = None,
    value: str = None,
    url: Optional[str] = None,
    headless: bool = True
) -> Dict:
    """
    在表单字段中输入文本

    参数:
        page_id: 已有页面的ID，为空则创建新页面
        selector: 表单字段的选择器
        value: 要输入的文本
        url: 网页地址 (如果提供了 page_id，此参数可选)
        headless: 是否无头模式运行

    返回:
        操作结果
    """
    try:
        browser = get_browser(headless=headless)

        # 标准化 page_id（支持整数或字符串）
        if page_id is not None:
            page_id = str(page_id)

        # 使用已有页面或创建新页面
        if page_id and page_id in _pages:
            page = _pages[page_id]
        else:
            page = browser.new_page()
            if url:
                page.goto(url, wait_until="load", timeout=30000)
            page_id = str(id(page))
            _pages[page_id] = page

        # 如果页面没有打开网址，且提供了url，先导航
        if page.url == "about:blank" and url:
            page.goto(url, wait_until="load", timeout=30000)

        page.wait_for_selector(selector, timeout=10000)
        page.fill(selector, value)

        result = {
            "success": True,
            "message": f"已在 {selector} 中输入文本",
            "value": value,
            "page_id": page_id
        }

        return result
    except PlaywrightTimeout:
        return {"success": False, "error": f"超时: 未找到元素 {selector}", "page_id": page_id}
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
def find_elements(
    page_id: Optional[str] = None,
    selector: str = None,
    url: Optional[str] = None,
    headless: bool = True
) -> Dict:
    """
    查找页面中的元素并返回信息

    参数:
        page_id: 已有页面的ID，为空则创建新页面
        selector: CSS选择器
        url: 网页地址 (如果提供了 page_id，此参数可选)
        headless: 是否无头模式运行

    返回:
        找到的元素列表及其信息
    """
    try:
        browser = get_browser(headless=headless)

        # 标准化 page_id（支持整数或字符串）
        if page_id is not None:
            page_id = str(page_id)

        # 使用已有页面或创建新页面
        if page_id and page_id in _pages:
            page = _pages[page_id]
        else:
            page = browser.new_page()
            if url:
                page.goto(url, wait_until="load", timeout=30000)
            page_id = str(id(page))
            _pages[page_id] = page

        # 如果页面没有打开网址，且提供了url，先导航
        if page.url == "about:blank" and url:
            page.goto(url, wait_until="load", timeout=30000)

        page.wait_for_selector(selector, timeout=10000)

        elements = page.query_selector_all(selector)
        results = []
        for i, element in enumerate(elements[:20]):
            text = element.inner_text() if element.inner_text() else ""
            attrs = {
                "tag": element.evaluate("el => el.tagName"),
                "text": text[:200],
                "visible": element.is_visible()
            }
            results.append(attrs)

        return {
            "success": True,
            "count": len(elements),
            "elements": results,
            "page_id": page_id
        }
    except PlaywrightTimeout:
        return {"success": False, "error": f"超时: 未找到元素 {selector}", "page_id": page_id}
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
def execute_javascript(
    page_id: Optional[str] = None,
    script: str = None,
    url: Optional[str] = None,
    headless: bool = True
) -> Dict:
    """
    在页面上下文中执行JavaScript代码

    参数:
        page_id: 已有页面的ID，为空则创建新页面
        script: 要执行的JavaScript代码
        url: 网页地址 (如果提供了 page_id，此参数可选)
        headless: 是否无头模式运行

    返回:
        脚本执行结果
    """
    try:
        browser = get_browser(headless=headless)

        # 标准化 page_id（支持整数或字符串）
        if page_id is not None:
            page_id = str(page_id)

        # 使用已有页面或创建新页面
        if page_id and page_id in _pages:
            page = _pages[page_id]
        else:
            page = browser.new_page()
            if url:
                page.goto(url, wait_until="load", timeout=30000)
            page_id = str(id(page))
            _pages[page_id] = page

        # 如果页面没有打开网址，且提供了url，先导航
        if page.url == "about:blank" and url:
            page.goto(url, wait_until="load", timeout=30000)

        result = page.evaluate(script)

        return {
            "success": True,
            "result": str(result) if result is not None else "undefined",
            "page_id": page_id
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
def navigate(
    page_id: Optional[str] = None,
    action: str = "go",
    url: Optional[str] = None,
    headless: bool = True
) -> Dict:
    """
    页面导航控制 (前进/后退/刷新/跳转)

    参数:
        page_id: 已有页面的ID，为空则创建新页面
        action: 操作类型 (go/forward/back/refresh)
        url: 目标网页地址 (action为"go"时必需)
        headless: 是否无头模式运行

    返回:
        导航结果
    """
    try:
        browser = get_browser(headless=headless)

        # 标准化 page_id（支持整数或字符串）
        if page_id is not None:
            page_id = str(page_id)

        # 使用已有页面或创建新页面
        if page_id and page_id in _pages:
            page = _pages[page_id]
        else:
            page = browser.new_page()
            page_id = str(id(page))
            _pages[page_id] = page

        # 执行导航操作
        if action == "go":
            if not url:
                return {"success": False, "error": "action为'go'时必须提供url参数", "page_id": page_id}
            page.goto(url, wait_until="load", timeout=30000)
        elif action == "forward":
            page.go_forward()
        elif action == "back":
            page.go_back()
        elif action == "refresh":
            page.reload()
        else:
            return {"success": False, "error": f"不支持的操作类型: {action}", "page_id": page_id}

        page.wait_for_timeout(1000)

        result = {
            "success": True,
            "action": action,
            "current_title": page.title(),
            "current_url": page.url,
            "page_id": page_id
        }

        return result
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
def get_page_title(page_id: Optional[str] = None, url: Optional[str] = None, headless: bool = True) -> Dict:
    """
    获取网页标题

    参数:
        page_id: 已有页面的ID，为空则创建新页面
        url: 网页地址 (如果提供了 page_id，此参数可选)
        headless: 是否无头模式运行

    返回:
        页面标题
    """
    try:
        browser = get_browser(headless=headless)

        # 标准化 page_id（支持整数或字符串）
        if page_id is not None:
            page_id = str(page_id)

        # 使用已有页面或创建新页面
        if page_id and page_id in _pages:
            page = _pages[page_id]
        else:
            page = browser.new_page()
            if url:
                page.goto(url, wait_until="load", timeout=30000)
            page_id = str(id(page))
            _pages[page_id] = page

        title = page.title()

        return {
            "success": True,
            "title": title,
            "url": page.url,
            "page_id": page_id
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
def list_active_pages() -> Dict:
    """
    列出所有活动的页面及其详细信息

    返回:
        活动页面列表及详细信息
    """
    pages_info = []
    for page_id, page in _pages.items():
        try:
            pages_info.append({
                "page_id": page_id,
                "title": page.title(),
                "url": page.url,
                "status": "active"
            })
        except:
            pass

    return {
        "success": True,
        "count": len(pages_info),
        "pages": pages_info,
        "message": f"当前有 {len(pages_info)} 个活动页面"
    }


@mcp.tool()
def clear_browser_data() -> Dict:
    """
    清除浏览器数据（Cookie、缓存、LocalStorage等）

    返回:
        清除结果
    """
    global _browser, _playwright, _pages
    try:
        # 关闭所有页面
        for page in _pages.values():
            try:
                page.close()
            except:
                pass
        _pages.clear()

        # 关闭浏览器并重新启动（清除所有数据）
        if _browser:
            try:
                _browser.close()
            except:
                pass
            _browser = None

        if _playwright:
            try:
                _playwright.stop()
            except:
                pass
            _playwright = None

        return {
            "success": True,
            "message": "浏览器数据已清除，所有页面已关闭。下次操作将创建新的浏览器实例。"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.prompt()
def browser_automation_prompt():
    """
    浏览器自动化助手 - 支持页面持久化和会话复用

    你可以使用以下工具来控制浏览器:
    - 打开网页、截图、获取内容
    - 点击元素、填写表单
    - 执行JavaScript、页面导航
    - 查找和操作页面元素
    - 保持页面会话（用于登录等需要持久化状态的操作）

    关键使用说明:
    1. 使用 open_page() 打开网页并获取 page_id
    2. 后续操作传入相同的 page_id 可以复用页面，保持登录状态和会话
    3. 使用 close_page() 关闭页面，或 clear_browser_data() 清除所有数据

    请描述你想要完成的浏览器操作。
    """
    return "你是一个强大的浏览器自动化助手，支持页面持久化和会话复用，可以帮助用户完成各种需要保持状态的网页操作任务（如登录、连续操作等）。"


def main():
    parser = argparse.ArgumentParser(description="Playwright MCP 服务器")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http", "sse", "streamable-http"],
        default="stdio",
        help="服务器模式: stdio(默认), http, sse, streamable-http"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP 服务器主机地址 (默认: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8500,
        help="HTTP 服务器端口 (默认: 8500)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="以无头模式运行浏览器（仅适用于启动新浏览器）"
    )
    parser.add_argument(
        "--use-existing",
        action="store_true",
        default=False,
        help="连接到已有浏览器实例（需要浏览器启用远程调试）"
    )
    parser.add_argument(
        "--cdp-url",
        default="http://127.0.0.1:9222",
        help="Chrome DevTools Protocol 地址 (默认: http://127.0.0.1:9222)"
    )

    args = parser.parse_args()

    # 设置全局标志（不立即连接）
    global _use_existing_browser
    _use_existing_browser = args.use_existing

    if _use_existing_browser:
        print("=" * 60)
        print(" 连接模式: 使用现有浏览器实例")
        print(f"   CDP 地址: {args.cdp_url}")
        print(f"   需要先手动启动浏览器并启用远程调试")
        print(f"   例如: chrome.exe --remote-debugging-port=9222")
        print("=" * 60)
        print()

        # 存储CDP URL供后续使用
        global _cdp_url
        _cdp_url = args.cdp_url
    else:
        print("=" * 60)
        print(" 连接模式: 启动新浏览器实例")
        print("=" * 60)
        print()

    print("=" * 60)
    print(" Playwright MCP 服务器启动中...")
    print("=" * 60)
    print(f" 模式: {args.mode}")
    print(f" 可用工具:")
    print(f"   - connect_to_existing_browser: 连接到现有浏览器")
    print(f"   - list_browser_contexts: 列出浏览器上下文")
    print(f"   - attach_to_existing_page: 附加到现有页面")
    print(f"   - open_page: 打开网页（返回 page_id）")
    print(f"   - screenshot: 截图（支持复用页面）")
    print(f"   - get_page_content: 获取页面内容（支持复用页面）")
    print(f"   - click_element: 点击元素（支持复用页面）")
    print(f"   - fill_form: 填写表单（支持复用页面）")
    print(f"   - find_elements: 查找元素（支持复用页面）")
    print(f"   - execute_javascript: 执行JS（支持复用页面）")
    print(f"   - navigate: 页面导航（支持复用页面）")
    print(f"   - get_page_info: 获取页面信息")
    print(f"   - close_page: 关闭页面")
    print(f"   - list_active_pages: 列出活动页面")
    print(f"   - clear_browser_data: 清除浏览器数据")
    print()

    if args.mode == "stdio":
        print("=" * 60)
        print(" Stdio 模式启动")
        print("   适合 Claude Desktop 本地使用")
        print("   使用 CTRL+C 停止服务器")
        print("=" * 60)
        print()
        mcp.run(transport="stdio")

    elif args.mode in ["http", "sse", "streamable-http"]:
        print("=" * 60)
        print(" HTTP 服务器启动")
        print(f"   地址: http://{args.host}:{args.port}")
        print(f"   模式: {args.mode}")
        print(f"   可从其他设备连接此地址")
        print(f"   使用 CTRL+C 停止服务器")
        print("=" * 60)
        print()
        mcp.run(
            transport=args.mode,
            host=args.host,
            port=args.port,
            show_banner=True
        )


if __name__ == "__main__":
    main()

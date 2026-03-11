"""
Playwright Browser MCP Server
- SSE transport for agent integration
- Connect to existing browser via CDP
- Session persistence (keep login state, cookies, etc.)
"""

import asyncio
import base64
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from fastmcp import FastMCP
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BrowserSession:
    browser: Browser
    playwright: Playwright
    contexts: Dict[str, BrowserContext] = field(default_factory=dict)
    pages: Dict[str, Page] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_connected_to_existing: bool = False

session: Optional[BrowserSession] = None
CDP_URL = "http://127.0.0.1:9222"

async def get_or_create_session(connect_existing: bool = False, cdp_url: str = CDP_URL) -> BrowserSession:
    global session
    if session is None:
        playwright = await async_playwright().start()
        
        if connect_existing:
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            logger.info(f"Connected to existing browser via CDP: {cdp_url}")
            is_connected = True
        else:
            browser = await playwright.chromium.launch(headless=False)
            logger.info("Launched new browser instance")
            is_connected = False
        
        session = BrowserSession(
            browser=browser,
            playwright=playwright,
            is_connected_to_existing=is_connected
        )
    return session

async def close_session():
    global session
    if session:
        for page in session.pages.values():
            try:
                await page.close()
            except:
                pass
        for ctx in session.contexts.values():
            try:
                await ctx.close()
            except:
                pass
        try:
            if not session.is_connected_to_existing:
                await session.browser.close()
        except:
            pass
        try:
            await session.playwright.stop()
        except:
            pass
        session = None
        logger.info("Browser session closed")


@asynccontextmanager
async def server_lifespan(app):
    logger.info("Server starting up...")
    yield
    logger.info("Server shutting down...")
    await close_session()


mcp = FastMCP(
    "playwright-browser-mcp",
    lifespan=server_lifespan
)


@mcp.tool()
async def connect_to_existing_browser(cdp_url: str = "http://127.0.0.1:9222") -> Dict:
    """
    Connect to an existing browser instance via Chrome DevTools Protocol.
    
    Args:
        cdp_url: Chrome DevTools Protocol URL (default: http://127.0.0.1:9222)
    
    Returns:
        Connection result with browser info
    """
    global session, CDP_URL
    
    try:
        await close_session()
        CDP_URL = cdp_url
        session = await get_or_create_session(connect_existing=True, cdp_url=cdp_url)
        
        contexts_info = []
        for ctx in session.browser.contexts:
            ctx_id = str(uuid.uuid4())
            session.contexts[ctx_id] = ctx
            pages_info = []
            for page in ctx.pages:
                page_id = str(uuid.uuid4())
                session.pages[page_id] = page
                pages_info.append({
                    "page_id": page_id,
                    "title": await page.title(),
                    "url": page.url
                })
            contexts_info.append({
                "context_id": ctx_id,
                "pages": pages_info
            })
        
        return {
            "success": True,
            "message": f"Connected to browser via CDP: {cdp_url}",
            "cdp_url": cdp_url,
            "contexts": contexts_info,
            "total_pages": len(session.pages)
        }
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure browser is started with --remote-debugging-port=9222"
        }


@mcp.tool()
async def list_browser_contexts() -> Dict:
    """
    List all browser contexts and their pages.
    
    Returns:
        List of contexts with their pages
    """
    if session is None:
        return {"success": False, "error": "No browser session. Call connect_to_existing_browser or open_page first."}
    
    contexts_info = []
    for ctx_id, ctx in session.contexts.items():
        pages_info = []
        for page in ctx.pages:
            page_id = next((pid for pid, p in session.pages.items() if p == page), None)
            if page_id is None:
                page_id = str(uuid.uuid4())
                session.pages[page_id] = page
            try:
                pages_info.append({
                    "page_id": page_id,
                    "title": await page.title(),
                    "url": page.url
                })
            except:
                pages_info.append({
                    "page_id": page_id,
                    "title": "Unknown",
                    "url": "Unknown"
                })
        contexts_info.append({
            "context_id": ctx_id,
            "pages_count": len(pages_info),
            "pages": pages_info
        })
    
    return {
        "success": True,
        "contexts_count": len(contexts_info),
        "contexts": contexts_info
    }


@mcp.tool()
async def attach_to_existing_page(context_id: str, page_index: int = 0) -> Dict:
    """
    Attach to an existing page in a browser context.
    
    Args:
        context_id: Browser context ID from list_browser_contexts
        page_index: Page index within the context (default: 0)
    
    Returns:
        Page info with page_id for subsequent operations
    """
    if session is None:
        return {"success": False, "error": "No browser session"}
    
    if context_id not in session.contexts:
        return {"success": False, "error": f"Context not found: {context_id}"}
    
    ctx = session.contexts[context_id]
    pages = ctx.pages
    
    if page_index >= len(pages):
        return {"success": False, "error": f"Page index {page_index} out of range. Context has {len(pages)} pages."}
    
    page = pages[page_index]
    page_id = str(uuid.uuid4())
    session.pages[page_id] = page
    
    return {
        "success": True,
        "page_id": page_id,
        "title": await page.title(),
        "url": page.url,
        "message": f"Attached to page: {await page.title()}"
    }


@mcp.tool()
async def open_page(url: str, headless: bool = False) -> Dict:
    """
    Open a new page and navigate to URL. Returns page_id for session persistence.
    
    Args:
        url: URL to navigate to
        headless: Run browser in headless mode (default: False for visibility)
    
    Returns:
        Page info including page_id (IMPORTANT: use this page_id for subsequent operations to maintain session)
    """
    try:
        sess = await get_or_create_session(connect_existing=False)
        page = await sess.browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        page_id = str(uuid.uuid4())
        sess.pages[page_id] = page
        
        return {
            "success": True,
            "page_id": page_id,
            "title": await page.title(),
            "url": page.url,
            "message": "IMPORTANT: Save this page_id and use it in subsequent operations to maintain session state (cookies, login, etc.)"
        }
    except Exception as e:
        logger.error(f"Failed to open page: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_page(page_id: Optional[str] = None) -> Dict:
    """
    Get page information. If page_id is provided, returns that page's info; otherwise lists all pages.
    
    Args:
        page_id: Specific page ID, or None to list all pages
    
    Returns:
        Page information
    """
    if session is None:
        return {"success": False, "error": "No browser session"}
    
    if page_id:
        if page_id not in session.pages:
            return {"success": False, "error": f"Page not found: {page_id}"}
        
        page = session.pages[page_id]
        return {
            "success": True,
            "page_id": page_id,
            "title": await page.title(),
            "url": page.url
        }
    else:
        pages_info = []
        for pid, page in session.pages.items():
            try:
                pages_info.append({
                    "page_id": pid,
                    "title": await page.title(),
                    "url": page.url
                })
            except:
                pass
        return {
            "success": True,
            "pages_count": len(pages_info),
            "pages": pages_info
        }


@mcp.tool()
async def close_page(page_id: Optional[str] = None) -> Dict:
    """
    Close a specific page or all pages.
    
    Args:
        page_id: Page ID to close, or None to close all pages
    
    Returns:
        Close result
    """
    if session is None:
        return {"success": False, "error": "No browser session"}
    
    try:
        if page_id:
            if page_id not in session.pages:
                return {"success": False, "error": f"Page not found: {page_id}"}
            await session.pages[page_id].close()
            del session.pages[page_id]
            return {"success": True, "message": f"Page {page_id} closed"}
        else:
            count = len(session.pages)
            for page in list(session.pages.values()):
                await page.close()
            session.pages.clear()
            return {"success": True, "message": f"Closed {count} pages"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def screenshot(
    page_id: Optional[str] = None,
    url: Optional[str] = None,
    path: str = "screenshot.png",
    full_page: bool = False,
    selector: Optional[str] = None
) -> Dict:
    """
    Take a screenshot of a page or specific element.
    
    Args:
        page_id: Existing page ID (recommended for session persistence)
        url: URL to navigate if creating new page
        path: Screenshot save path
        full_page: Capture full scrollable page
        selector: CSS selector to screenshot specific element
    
    Returns:
        Screenshot result with base64 data
    """
    try:
        sess = await get_or_create_session()
        
        if page_id and page_id in sess.pages:
            page = sess.pages[page_id]
        elif url:
            page = await sess.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)
            page_id = str(uuid.uuid4())
            sess.pages[page_id] = page
        else:
            return {"success": False, "error": "Provide either page_id or url"}
        
        if selector:
            element = await page.wait_for_selector(selector, timeout=10000)
            if element:
                await element.screenshot(path=path)
            else:
                await page.screenshot(path=path, full_page=full_page)
        else:
            await page.screenshot(path=path, full_page=full_page)
        
        with open(path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
        
        return {
            "success": True,
            "path": path,
            "full_page": full_page,
            "base64": base64_data,
            "page_id": page_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_content(
    page_id: Optional[str] = None,
    url: Optional[str] = None,
    selector: Optional[str] = None
) -> Dict:
    """
    Get page content (HTML and text).
    
    Args:
        page_id: Existing page ID
        url: URL to navigate if creating new page
        selector: Get content from specific element only
    
    Returns:
        Page HTML and text content
    """
    try:
        sess = await get_or_create_session()
        
        if page_id and page_id in sess.pages:
            page = sess.pages[page_id]
        elif url:
            page = await sess.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)
            page_id = str(uuid.uuid4())
            sess.pages[page_id] = page
        else:
            return {"success": False, "error": "Provide either page_id or url"}
        
        html = await page.content()
        
        if selector:
            element = await page.query_selector(selector)
            text = await element.inner_text() if element else ""
        else:
            text = await page.inner_text("body")
        
        return {
            "success": True,
            "page_id": page_id,
            "url": page.url,
            "title": await page.title(),
            "html": html[:50000] if len(html) > 50000 else html,
            "text": text[:10000] if len(text) > 10000 else text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def click(
    page_id: str,
    selector: str,
    timeout: int = 10000
) -> Dict:
    """
    Click an element on the page.
    
    Args:
        page_id: Page ID (required for session persistence)
        selector: CSS selector or text selector
        timeout: Wait timeout in milliseconds
    
    Returns:
        Click result with updated page info
    """
    if session is None or page_id not in session.pages:
        return {"success": False, "error": f"Page not found: {page_id}"}
    
    try:
        page = session.pages[page_id]
        await page.wait_for_selector(selector, timeout=timeout)
        await page.click(selector)
        await page.wait_for_load_state("networkidle", timeout=30000)
        
        return {
            "success": True,
            "page_id": page_id,
            "message": f"Clicked: {selector}",
            "current_url": page.url,
            "title": await page.title()
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
async def type_text(
    page_id: str,
    selector: str,
    text: str,
    clear_first: bool = True,
    timeout: int = 10000
) -> Dict:
    """
    Type text into an input field.
    
    Args:
        page_id: Page ID (required for session persistence)
        selector: CSS selector for input field
        text: Text to type
        clear_first: Clear field before typing (default: True)
        timeout: Wait timeout in milliseconds
    
    Returns:
        Type result
    """
    if session is None or page_id not in session.pages:
        return {"success": False, "error": f"Page not found: {page_id}"}
    
    try:
        page = session.pages[page_id]
        element = await page.wait_for_selector(selector, timeout=timeout)
        if element is None:
            return {"success": False, "error": f"Element not found: {selector}", "page_id": page_id}
        
        if clear_first:
            await element.fill(text)
        else:
            await element.type(text)
        
        return {
            "success": True,
            "page_id": page_id,
            "message": f"Typed text into: {selector}",
            "text": text
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
async def find_elements(
    page_id: str,
    selector: str,
    timeout: int = 10000
) -> Dict:
    """
    Find elements on the page.
    
    Args:
        page_id: Page ID
        selector: CSS selector
        timeout: Wait timeout in milliseconds
    
    Returns:
        List of found elements with their properties
    """
    if session is None or page_id not in session.pages:
        return {"success": False, "error": f"Page not found: {page_id}"}
    
    try:
        page = session.pages[page_id]
        await page.wait_for_selector(selector, timeout=timeout)
        elements = await page.query_selector_all(selector)
        
        results = []
        for i, elem in enumerate(elements[:30]):
            try:
                text = await elem.inner_text()
                is_visible = await elem.is_visible()
                tag = await elem.evaluate("el => el.tagName")
                
                results.append({
                    "index": i,
                    "tag": tag,
                    "text": text[:200] if text else "",
                    "visible": is_visible
                })
            except:
                pass
        
        return {
            "success": True,
            "page_id": page_id,
            "selector": selector,
            "count": len(elements),
            "elements": results
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
async def execute_script(
    page_id: str,
    script: str
) -> Dict:
    """
    Execute JavaScript in the page context.
    
    Args:
        page_id: Page ID
        script: JavaScript code to execute
    
    Returns:
        Script execution result
    """
    if session is None or page_id not in session.pages:
        return {"success": False, "error": f"Page not found: {page_id}"}
    
    try:
        page = session.pages[page_id]
        result = await page.evaluate(script)
        
        return {
            "success": True,
            "page_id": page_id,
            "result": result
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
async def navigate(
    page_id: str,
    action: str = "goto",
    url: Optional[str] = None
) -> Dict:
    """
    Navigate within a page (goto, back, forward, refresh).
    
    Args:
        page_id: Page ID
        action: Navigation action (goto, back, forward, refresh)
        url: URL for goto action
    
    Returns:
        Navigation result
    """
    if session is None or page_id not in session.pages:
        return {"success": False, "error": f"Page not found: {page_id}"}
    
    try:
        page = session.pages[page_id]
        
        if action == "goto":
            if not url:
                return {"success": False, "error": "URL required for goto action"}
            await page.goto(url, wait_until="networkidle", timeout=60000)
        elif action == "back":
            await page.go_back(wait_until="networkidle", timeout=30000)
        elif action == "forward":
            await page.go_forward(wait_until="networkidle", timeout=30000)
        elif action == "refresh":
            await page.reload(wait_until="networkidle", timeout=30000)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        return {
            "success": True,
            "page_id": page_id,
            "action": action,
            "url": page.url,
            "title": await page.title()
        }
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
async def wait_for(
    page_id: str,
    selector: Optional[str] = None,
    timeout: int = 30000
) -> Dict:
    """
    Wait for an element or page state.
    
    Args:
        page_id: Page ID
        selector: CSS selector to wait for (or None to wait for network idle)
        timeout: Wait timeout in milliseconds
    
    Returns:
        Wait result
    """
    if session is None or page_id not in session.pages:
        return {"success": False, "error": f"Page not found: {page_id}"}
    
    try:
        page = session.pages[page_id]
        
        if selector:
            await page.wait_for_selector(selector, timeout=timeout)
            return {"success": True, "page_id": page_id, "message": f"Element found: {selector}"}
        else:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return {"success": True, "page_id": page_id, "message": "Page loaded"}
    except Exception as e:
        return {"success": False, "error": str(e), "page_id": page_id}


@mcp.tool()
async def get_cookies(page_id: Optional[str] = None) -> Dict:
    """
    Get cookies from the browser context.
    
    Args:
        page_id: Page ID (to determine context)
    
    Returns:
        List of cookies
    """
    if session is None:
        return {"success": False, "error": "No browser session"}
    
    try:
        if page_id and page_id in session.pages:
            page = session.pages[page_id]
            context = page.context
        else:
            context = session.browser.contexts[0] if session.browser.contexts else None
        
        if context is None:
            return {"success": False, "error": "No browser context"}
        
        cookies = await context.cookies()
        return {
            "success": True,
            "cookies_count": len(cookies),
            "cookies": cookies
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def set_cookies(page_id: Optional[str] = None, cookies: Optional[List[Dict[str, Any]]] = None) -> Dict:
    """
    Set cookies in the browser context.
    
    Args:
        page_id: Page ID (to determine context)
        cookies: List of cookie objects to set
    
    Returns:
        Result
    """
    if session is None:
        return {"success": False, "error": "No browser session"}
    
    if not cookies:
        return {"success": False, "error": "No cookies provided"}
    
    try:
        if page_id and page_id in session.pages:
            page = session.pages[page_id]
            context = page.context
        else:
            context = session.browser.contexts[0] if session.browser.contexts else None
        
        if context is None:
            return {"success": False, "error": "No browser context"}
        
        await context.add_cookies(cookies)  # type: ignore
        return {
            "success": True,
            "message": f"Set {len(cookies)} cookies"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def clear_browser_data() -> Dict:
    """
    Clear all browser data (cookies, cache, close all pages).
    
    Returns:
        Clear result
    """
    await close_session()
    return {
        "success": True,
        "message": "Browser session cleared. Next operation will start fresh."
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Playwright Browser MCP Server")
    parser.add_argument(
        "--mode",
        choices=["stdio", "sse", "http"],
        default="sse",
        help="Transport mode (default: sse)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8500,
        help="Server port (default: 8500)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print(" Playwright Browser MCP Server")
    print("=" * 60)
    print(f" Mode: {args.mode}")
    print(f" Host: {args.host}")
    print(f" Port: {args.port}")
    print()
    print(" Key Features:")
    print("  - Session persistence (maintain login state)")
    print("  - Connect to existing browser via CDP")
    print("  - SSE transport for agent integration")
    print()
    print(" To connect existing Chrome:")
    print("  chrome.exe --remote-debugging-port=9222")
    print()
    print(" Available Tools:")
    print("  - connect_to_existing_browser: Connect via CDP")
    print("  - open_page: Open new page (returns page_id)")
    print("  - get_page: Get page info")
    print("  - screenshot: Capture screenshot")
    print("  - get_content: Get HTML/text")
    print("  - click: Click element")
    print("  - type_text: Type in input")
    print("  - find_elements: Find elements")
    print("  - execute_script: Run JavaScript")
    print("  - navigate: goto/back/forward/refresh")
    print("  - wait_for: Wait for element")
    print("  - get/set_cookies: Cookie management")
    print("=" * 60)
    
    if args.mode == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport=args.mode,
            host=args.host,
            port=args.port
        )


if __name__ == "__main__":
    main()
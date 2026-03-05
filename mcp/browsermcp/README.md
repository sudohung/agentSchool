# Playwright Browser MCP Server

基于 Playwright 的浏览器控制 MCP 服务，支持连接现有浏览器、会话持久化、SSE 传输。

## 功能特性

- 🔗 **连接现有浏览器** - 通过 CDP 协议连接到已运行的 Chrome/Edge
- 💾 **会话持久化** - 复用 page_id 保持登录状态、Cookie 等
- 🌐 **SSE 传输** - 通过 Server-Sent Events 提供 MCP 接口
- 🛠️ **完整工具集** - 截图、点击、输入、导航等常用操作

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 启动浏览器（调试模式）

```bash
# 方式一：运行脚本
start_chrome_debug.bat

# 方式二：手动启动 Chrome
chrome.exe --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-debug-profile"
```

### 3. 启动 MCP 服务

```bash
# SSE 模式（推荐，用于 Agent）
python server.py --mode sse --port 8500

# SSE 模式（推荐，用于 Agent），连接现有浏览器
python server.py --mode sse --port 8500 --use-existing --cdp-url http://127.0.0.1:9222 

# HTTP 模式
python server.py --mode http --port 8500

# 标准输入模式（本地 CLI）
python server.py --mode stdio
```

## 使用方式

### Agent 调用示例

```python
# 1. 连接到现有浏览器
{
  "name": "connect_to_existing_browser",
  "arguments": {"cdp_url": "http://127.0.0.1:9222"}
}

# 2. 打开网页（获取 page_id）
{
  "name": "open_page",
  "arguments": {"url": "https://www.example.com", "headless": false}
}
# 返回: {"page_id": "abc-123-xxx", "title": "Example Domain", "url": "https://www.example.com"}

# 3. 使用 page_id 复用会话（保持登录状态）
{
  "name": "click",
  "arguments": {"page_id": "abc-123-xxx", "selector": "#login-btn"}
}

{
  "name": "type_text",
  "arguments": {"page_id": "abc-123-xxx", "selector": "input[name=username]", "text": "myuser"}
}

{
  "name": "screenshot",
  "arguments": {"page_id": "abc-123-xxx", "path": "screenshot.png"}
}

{
  "name": "get_content",
  "arguments": {"page_id": "abc-123-xxx"}
}
```

## 工具列表

| 工具 | 说明 | 必需参数 |
|------|------|----------|
| `connect_to_existing_browser` | 通过 CDP 连接现有浏览器 | `cdp_url` |
| `list_browser_contexts` | 列出浏览器上下文和页面 | - |
| `attach_to_existing_page` | 附加到现有页面 | `context_id`, `page_index` |
| `open_page` | 打开新页面，返回 page_id | `url` |
| `get_page` | 获取页面信息 | `page_id` (可选) |
| `close_page` | 关闭页面 | `page_id` (可选) |
| `screenshot` | 截图 | `page_id` 或 `url` |
| `get_content` | 获取页面 HTML/文本 | `page_id` 或 `url` |
| `click` | 点击元素 | `page_id`, `selector` |
| `type_text` | 输入文本 | `page_id`, `selector`, `text` |
| `find_elements` | 查找元素 | `page_id`, `selector` |
| `execute_script` | 执行 JavaScript | `page_id`, `script` |
| `navigate` | 页面导航 | `page_id`, `action` |
| `wait_for` | 等待元素/加载 | `page_id` |
| `get_cookies` | 获取 Cookie | `page_id` (可选) |
| `set_cookies` | 设置 Cookie | `cookies` |
| `clear_browser_data` | 清除所有浏览器数据 | - |

## 启动参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mode` | `sse` | 传输模式：`stdio`, `sse`, `http` |
| `--host` | `127.0.0.1` | 服务器地址 |
| `--port` | `8500` | 服务器端口 |
| `--use-existing` | false | 启动时连接现有浏览器 |
| `--cdp-url` | `http://127.0.0.1:9222` | CDP 地址 |

## 会话持久化

**关键**：每次 `open_page` 返回唯一的 `page_id`，后续所有操作必须传入相同的 `page_id` 才能复用会话。

```python
# ✅ 正确：使用 page_id 保持会话
open_page(url="https://example.com")  # 返回 page_id
click(page_id="abc-123", selector="button")  # 复用同一页面

# ❌ 错误：每次创建新页面，会话丢失
click(url="https://example.com", selector="button")  # 新页面，无登录状态
```

## MCP 客户端配置

### Claude Desktop

```json
{
  "mcpServers": {
    "playwright-browser": {
      "command": "python",
      "args": ["server.py", "--mode", "stdio"]
    }
  }
}
```

### 其他 Agent（HTTP/SSE）

```json
{
  "mcpServers": {
    "playwright-browser": {
      "url": "http://127.0.0.1:8500/sse"
    }
  }
}
```

## 常见问题

### Q: 连接现有浏览器失败

确保 Chrome 已启动并启用远程调试：
```bash
chrome.exe --remote-debugging-port=9222
```

### Q: 如何保持登录状态

每次操作都使用同一个 `page_id`，Playwright 会保持页面的 Cookie 和 Session。

### Q: 如何关闭浏览器

```python
clear_browser_data()  # 关闭所有页面和浏览器
```

## 项目结构

```
browsermcp/
├── server.py              # MCP 服务端
├── requirements.txt       # 依赖
├── start_chrome_debug.bat # 启动 Chrome 调试模式
└── README.md             # 本文档
```

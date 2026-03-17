# Java SDK vs Python SDK vs OpenAPI 对比检查

## 检查方法

1. 提取 OpenAPI 所有端点定义
2. 提取 Python SDK 所有 API 方法
3. 提取 Java SDK 所有 API 方法
4. 对比端点路径、HTTP 方法、参数、返回值

## 检查清单

### Session API

| 端点 | HTTP | OpenAPI | Python SDK | Java SDK | 状态 |
|------|------|---------|------------|----------|------|
| /session | GET | ✅ | list() | list() | ✅ |
| /session | POST | ✅ | create() | create() | ✅ |
| /session/{id} | GET | ✅ | get() | get() | ✅ |
| /session/{id} | DELETE | ✅ | delete() | delete() | ✅ |
| /session/{id} | PATCH | ✅ | update() | update() | ✅ |
| /session/status | GET | ✅ | status() | status() | ✅ |
| /session/{id}/children | GET | ✅ | children() | children() | ✅ |
| /session/{id}/todo | GET | ✅ | todos() | todos() | ✅ |
| /session/{id}/abort | POST | ✅ | abort() | abort() | ✅ |
| /session/{id}/share | POST | ✅ | share() | share() | ✅ |
| /session/{id}/share | DELETE | ✅ | unshare() | unshare() | ✅ |
| /session/{id}/fork | POST | ✅ | fork() | fork() | ✅ |
| /session/{id}/diff | GET | ✅ | diff() | diff() | ✅ |
| /session/{id}/summarize | POST | ✅ | summarize() | summarize() | ✅ |
| /session/{id}/revert | POST | ✅ | revert() | revert() | ✅ |
| /session/{id}/unrevert | POST | ✅ | unrevert() | unrevert() | ✅ |
| /session/{id}/init | POST | ✅ | init() | init() | ✅ |

### Message API

| 端点 | HTTP | OpenAPI | Python SDK | Java SDK | 状态 |
|------|------|---------|------------|----------|------|
| /session/{id}/message | GET | ✅ | list() | list() | ✅ |
| /session/{id}/message/{id} | GET | ✅ | get() | get() | ✅ |
| /session/{id}/message | POST | ✅ | send() | send() | ✅ |
| /session/{id}/message | POST | ✅ | send_text() | sendText() | ✅ |
| /session/{id}/prompt_async | POST | ✅ | send_async() | sendAsync() | ✅ |
| /session/{id}/command | POST | ✅ | command() | command() | ✅ |
| /session/{id}/shell | POST | ✅ | shell() | shell() | ✅ |
| /session/{id}/message/{id} | DELETE | ✅ | delete() | delete() | ✅ |

### Permission API

| 端点 | HTTP | OpenAPI | Python SDK | Java SDK | 状态 |
|------|------|---------|------------|----------|------|
| /permission | GET | ✅ | list() | list() | ✅ |
| /permission/{id}/reply | POST | ✅ | reply() | reply() | ✅ |
| /session/{id}/permissions/{id} | POST | ✅ | respond() | respond() | ✅ |

### File API

| 端点 | HTTP | OpenAPI | Python SDK | Java SDK | 状态 |
|------|------|---------|------------|----------|------|
| /file | GET | ✅ | list() | list() | ✅ |
| /file/content | GET | ✅ | read() | read() | ✅ |
| /file/status | GET | ✅ | status() | status() | ✅ |
| /find | GET | ✅ | search_text() | searchText() | ✅ |
| /find/file | GET | ✅ | find_files() | findFiles() | ✅ |
| /find/symbol | GET | ✅ | find_symbols() | findSymbols() | ✅ |

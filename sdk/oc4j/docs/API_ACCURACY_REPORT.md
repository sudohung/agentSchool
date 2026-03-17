# Java SDK API 准确性检查报告

> 检查日期：2026-03-17  
> 对比基准：OpenAPI 规范 + Python SDK

---

## 一、总体统计

| 项目 | 数量 |
|------|------|
| OpenAPI 端点 | 104 |
| Java SDK 模块 | 18 |
| Java SDK 方法 | 85 |
| Python SDK 模块 | 18 |
| Python SDK 方法 | ~70 |

---

## 二、模块详细对比

### 1. SessionAPI (22 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| list() | GET /session | list() | ✅ |
| list(workspace, roots, start, search, limit) | GET /session | list() | ✅ |
| get(sessionId) | GET /session/{id} | get() | ✅ |
| create(title) | POST /session | create() | ✅ |
| create(title, parentId, permission) | POST /session | create() | ✅ |
| delete(sessionId) | DELETE /session/{id} | delete() | ✅ |
| update(sessionId, title) | PATCH /session/{id} | update() | ✅ |
| status() | GET /session/status | status() | ✅ |
| children(sessionId) | GET /session/{id}/children | children() | ✅ |
| todos(sessionId) | GET /session/{id}/todo | todos() | ✅ |
| abort(sessionId) | POST /session/{id}/abort | abort() | ✅ |
| share(sessionId) | POST /session/{id}/share | share() | ✅ |
| unshare(sessionId) | DELETE /session/{id}/share | unshare() | ✅ |
| fork(sessionId) | POST /session/{id}/fork | fork() | ✅ |
| fork(sessionId, messageId) | POST /session/{id}/fork | fork() | ✅ |
| diff(sessionId) | GET /session/{id}/diff | diff() | ✅ |
| diff(sessionId, messageId) | GET /session/{id}/diff | diff() | ✅ |
| summarize(sessionId, providerId, modelId) | POST /session/{id}/summarize | summarize() | ✅ |
| revert(sessionId, messageId) | POST /session/{id}/revert | revert() | ✅ |
| revert(sessionId, messageId, partId) | POST /session/{id}/revert | revert() | ✅ |
| unrevert(sessionId) | POST /session/{id}/unrevert | unrevert() | ✅ |
| init(sessionId, messageId, providerId, modelId) | POST /session/{id}/init | init() | ✅ |

**评估**: 完整且准确 ✅

---

### 2. MessageAPI (12 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| list(sessionId) | GET /session/{id}/message | list() | ✅ |
| list(sessionId, limit) | GET /session/{id}/message | list() | ✅ |
| get(sessionId, messageId) | GET /session/{id}/message/{id} | get() | ✅ |
| sendText(sessionId, text) | POST /session/{id}/message | send_text() | ✅ |
| sendText(sessionId, text, providerId, modelId, agent, noReply) | POST /session/{id}/message | send_text() | ✅ |
| send(sessionId, parts, ...) | POST /session/{id}/message | send() | ✅ |
| sendAsync(sessionId, parts, ...) | POST /session/{id}/prompt_async | send_async() | ✅ |
| command(sessionId, command) | POST /session/{id}/command | command() | ✅ |
| command(sessionId, command, arguments, ...) | POST /session/{id}/command | command() | ✅ |
| shell(sessionId, command) | POST /session/{id}/shell | shell() | ✅ |
| shell(sessionId, command, providerId, modelId, agent) | POST /session/{id}/shell | shell() | ✅ |
| delete(sessionId, messageId) | DELETE /session/{id}/message/{id} | delete() | ✅ |

**评估**: 完整且准确 ✅

---

### 3. PermissionAPI (3 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| list() | GET /permission | list() | ✅ |
| reply(requestId, reply, message) | POST /permission/{id}/reply | reply() | ✅ |
| respond(sessionId, permissionId, response) | POST /session/{id}/permissions/{id} | respond() | ✅ |

**评估**: 完整且准确 ✅

---

### 4. FileAPI (9 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| list(path) | GET /file | list() | ✅ |
| list() | GET /file | list() | ✅ |
| read(path) | GET /file/content | read() | ✅ |
| status() | GET /file/status | status() | ✅ |
| searchText(pattern, path) | GET /find | search_text() | ✅ |
| searchText(pattern) | GET /find | search_text() | ✅ |
| findFiles(query, type, limit) | GET /find/file | find_files() | ✅ |
| findFiles(query) | GET /find/file | find_files() | ✅ |
| findSymbols(query) | GET /find/symbol | find_symbols() | ✅ |

**评估**: 完整且准确 ✅

---

### 5. ProjectAPI (5 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| list() | GET /project | list() | ✅ |
| current() | GET /project/current | current() | ✅ |
| update(projectId, name, icon, commands) | PATCH /project/{id} | update() | ✅ |
| update(projectId, name) | PATCH /project/{id} | update() | ✅ |
| initGit() | POST /project/git/init | init_git() | ✅ |

**评估**: 完整且准确 ✅

---

### 6. ProviderAPI (5 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| list() | GET /provider | list() | ✅ |
| auth() | GET /provider/auth | auth() | ✅ |
| oauthAuthorize(providerId, method) | POST /provider/{id}/oauth/authorize | oauth_authorize() | ✅ |
| oauthAuthorize(providerId) | POST /provider/{id}/oauth/authorize | oauth_authorize() | ✅ |
| oauthCallback(providerId, method, code) | POST /provider/{id}/oauth/callback | oauth_callback() | ✅ |

**评估**: 完整且准确 ✅

---

### 7. ConfigAPI (3 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| get() | GET /config | get() | ✅ |
| update(config) | PATCH /config | update() | ✅ |
| providers() | GET /config/providers | providers() | ✅ |

**评估**: 完整且准确 ✅

---

### 8. QuestionAPI (4 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| list() | GET /question | list() | ✅ |
| reply(requestId, answer) | POST /question/{id}/reply | reply() | ✅ |
| reject(requestId, reason) | POST /question/{id}/reject | reject() | ✅ |
| reject(requestId) | POST /question/{id}/reject | reject() | ✅ |

**评估**: 完整且准确 ✅

---

### 9. MCPAPI (9 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| status() | GET /mcp | status() | ✅ |
| add(name, config) | POST /mcp | add() | ✅ |
| authStart(name, method) | POST /mcp/{name}/auth | auth_start() | ✅ |
| authStart(name) | POST /mcp/{name}/auth | auth_start() | ✅ |
| authRemove(name) | DELETE /mcp/{name}/auth | auth_remove() | ✅ |
| authCallback(name, code, state) | POST /mcp/{name}/auth/callback | auth_callback() | ✅ |
| connect(name, timeout) | POST /mcp/{name}/connect | connect() | ✅ |
| connect(name) | POST /mcp/{name}/connect | connect() | ✅ |
| disconnect(name) | POST /mcp/{name}/disconnect | disconnect() | ✅ |

**评估**: 完整且准确 ✅

---

### 10. GlobalAPI (4 方法) ✅

| Java 方法 | OpenAPI 端点 | Python SDK | 状态 |
|-----------|-------------|------------|------|
| health() | GET /global/health | health_check() | ✅ |
| config() | GET /global/config | config.get() | ✅ |
| updateConfig(config) | PATCH /global/config | config.update() | ✅ |
| dispose() | POST /global/dispose | dispose() | ✅ |

**评估**: 完整且准确 ✅

---

### 11. 其他 API (各 1-2 方法) ✅

| API | 方法 | OpenAPI 端点 | 状态 |
|-----|------|-------------|------|
| AgentAPI | list() | GET /agent | ✅ |
| CommandAPI | list() | GET /command | ✅ |
| PathAPI | get() | GET /path | ✅ |
| VcsAPI | get() | GET /vcs | ✅ |
| LSPAPI | status() | GET /lsp | ✅ |
| InstanceAPI | dispose() | POST /instance/dispose | ✅ |
| ToolAPI | listIds(), list() | GET /experimental/tool/ids, /tool | ✅ |
| FormatterAPI | status() | GET /formatter | ✅ |

**评估**: 完整且准确 ✅

---

## 三、参数和返回值检查

### 返回值类型对比

| API | Python 返回值 | Java 返回值 | 状态 |
|-----|--------------|------------|------|
| SessionAPI.list() | List[Session] | List<Session> | ✅ |
| MessageAPI.list() | List[MessageWithParts] | List<MessageWithParts> | ✅ |
| PermissionAPI.list() | List[PermissionRequest] | List<PermissionRequest> | ✅ |
| GlobalAPI.health() | dict | Map<String, Object> | ✅ |
| ConfigAPI.get() | Config | Map<String, Object> | ⚠️ |

### 参数命名对比

| API | Python 参数 | Java 参数 | 状态 |
|-----|------------|----------|------|
| SessionAPI.get() | session_id | sessionId | ✅ (命名约定不同) |
| MessageAPI.send() | session_id | sessionId | ✅ (命名约定不同) |
| PermissionAPI.reply() | request_id | requestId | ✅ (命名约定不同) |

---

## 四、发现的问题

### ⚠️ 轻微问题

1. **ConfigAPI 返回值**
   - Python: 强类型 `Config` 对象
   - Java: 弱类型 `Map<String, Object>`
   - 建议：创建 Config 模型类

2. **部分 API 使用 Map<String, Object>**
   - 原因：Java 模型类不完整
   - 影响：类型安全性降低
   - 建议：补充完整的数据模型

### ❌ 缺失功能

1. **

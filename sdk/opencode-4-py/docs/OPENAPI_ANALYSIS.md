# OpenCode API 完整分析报告

> 基于 OpenCode Server v1.2.24 OpenAPI 规范

## 一、API 端点总览（按模块分类）

### 1. Global 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/global/health` | GET | `global.health` | 获取服务器健康状态 |
| `/global/event` | GET | `global.event` | 订阅全局SSE事件流 |
| `/global/config` | GET | `global.config.get` | 获取全局配置 |
| `/global/config` | PATCH | `global.config.update` | 更新全局配置 |
| `/global/dispose` | POST | `global.dispose` | 释放所有实例资源 |

### 2. Auth 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/auth/{providerID}` | PUT | `auth.set` | 设置认证凭据 |
| `/auth/{providerID}` | DELETE | `auth.remove` | 删除认证凭据 |

**Path参数:** `providerID` (string, required)

### 3. Session 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/session` | GET | `session.list` | 列出所有会话 |
| `/session` | POST | `session.create` | 创建新会话 |
| `/session/status` | GET | `session.status` | 获取会话状态 |
| `/session/{sessionID}` | GET | `session.get` | 获取指定会话 |
| `/session/{sessionID}` | DELETE | `session.delete` | 删除会话 |
| `/session/{sessionID}` | PATCH | `session.update` | 更新会话属性 |
| `/session/{sessionID}/children` | GET | `session.children` | 获取子会话列表 |
| `/session/{sessionID}/todo` | GET | `session.todo` | 获取会话Todo列表 |
| `/session/{sessionID}/init` | POST | `session.init` | 初始化会话(生成AGENTS.md) |
| `/session/{sessionID}/fork` | POST | `session.fork` | Fork会话 |
| `/session/{sessionID}/abort` | POST | `session.abort` | 中止会话 |
| `/session/{sessionID}/share` | POST | `session.share` | 分享会话 |
| `/session/{sessionID}/share` | DELETE | `session.unshare` | 取消分享会话 |
| `/session/{sessionID}/diff` | GET | `session.diff` | 获取消息变更diff |
| `/session/{sessionID}/summarize` | POST | `session.summarize` | 压缩/总结会话 |
| `/session/{sessionID}/revert` | POST | `session.revert` | 回退消息 |
| `/session/{sessionID}/unrevert` | POST | `session.unrevert` | 恢复回退的消息 |

#### Session 详细参数

**`/session` GET 参数:**
| 参数名 | 位置 | 类型 | 必填 | 描述 |
|--------|------|------|------|------|
| directory | query | string | 否 | 按项目目录过滤 |
| workspace | query | string | 否 | 工作空间ID |
| roots | query | boolean | 否 | 仅返回根会话 |
| start | query | number | 否 | 过滤更新时间戳之后的会话 |
| search | query | string | 否 | 按标题搜索 |
| limit | query | number | 否 | 返回数量限制 |

**`/session` POST 请求体:**
```json
{
  "parentID": "string (pattern: ^ses.*)",
  "title": "string",
  "permission": "PermissionRuleset"
}
```

### 4. Message 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/session/{sessionID}/message` | GET | `session.messages` | 获取会话所有消息 |
| `/session/{sessionID}/message` | POST | `session.prompt` | 发送消息(流式响应) |
| `/session/{sessionID}/message/{messageID}` | GET | `session.message` | 获取单条消息 |
| `/session/{sessionID}/message/{messageID}` | DELETE | `session.deleteMessage` | 删除消息 |
| `/session/{sessionID}/message/{messageID}/part/{partID}` | DELETE | `part.delete` | 删除消息部分 |
| `/session/{sessionID}/message/{messageID}/part/{partID}` | PATCH | `part.update` | 更新消息部分 |
| `/session/{sessionID}/prompt_async` | POST | `session.prompt_async` | 异步发送消息 |
| `/session/{sessionID}/command` | POST | `session.command` | 发送命令 |
| `/session/{sessionID}/shell` | POST | `session.shell` | 执行Shell命令 |

#### Message 发送请求体 (`/session/{sessionID}/message` POST)

```json
{
  "messageID": "string (pattern: ^msg.*)",
  "model": {
    "providerID": "string",
    "modelID": "string"
  },
  "agent": "string",
  "noReply": "boolean",
  "format": "OutputFormat",
  "system": "string",
  "variant": "string",
  "parts": [
    { "type": "text", "text": "..." },
    { "type": "file", "mime": "...", "url": "..." },
    { "type": "agent", "name": "..." },
    { "type": "subtask", "prompt": "...", "description": "...", "agent": "..." }
  ]
}
```

### 5. File 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/file` | GET | `file.list` | 列出文件和目录 |
| `/file/content` | GET | `file.read` | 读取文件内容 |
| `/file/status` | GET | `file.status` | 获取Git文件状态 |
| `/find` | GET | `find.text` | 文本搜索 |
| `/find/file` | GET | `find.files` | 文件搜索 |
| `/find/symbol` | GET | `find.symbols` | 符号搜索(LSP) |

#### File 详细参数

**`/file` GET:**
| 参数名 | 位置 | 类型 | 必填 |
|--------|------|------|------|
| path | query | string | 是 |

**响应:** `FileNode[]`

**`/find/file` GET:**
| 参数名 | 位置 | 类型 | 必填 | 描述 |
|--------|------|------|------|------|
| query | query | string | 是 | 搜索模式 |
| dirs | query | string | 否 | "true"/"false" |
| type | query | string | 否 | "file"/"directory" |
| limit | query | integer | 否 | 1-200 |

### 6. Event (SSE) 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/global/event` | GET | `global.event` | 全局事件流(SSE) |
| `/event` | GET | `event.subscribe` | 项目级事件流(SSE) |

**响应类型:** `text/event-stream`

### 7. Project 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/project` | GET | `project.list` | 列出所有项目 |
| `/project/current` | GET | `project.current` | 获取当前项目 |
| `/project/git/init` | POST | `project.initGit` | 初始化Git仓库 |
| `/project/{projectID}` | PATCH | `project.update` | 更新项目 |

### 8. Config 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/config` | GET | `config.get` | 获取配置 |
| `/config` | PATCH | `config.update` | 更新配置 |
| `/config/providers` | GET | `config.providers` | 列出配置的Provider |

### 9. Provider 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/provider` | GET | `provider.list` | 列出所有Provider |
| `/provider/auth` | GET | `provider.auth` | 获取认证方法 |
| `/provider/{providerID}/oauth/authorize` | POST | `provider.oauth.authorize` | OAuth授权 |
| `/provider/{providerID}/oauth/callback` | POST | `provider.oauth.callback` | OAuth回调 |

### 10. MCP (Model Context Protocol) 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/mcp` | GET | `mcp.status` | 获取MCP状态 |
| `/mcp` | POST | `mcp.add` | 添加MCP服务器 |
| `/mcp/{name}/connect` | POST | `mcp.connect` | 连接MCP服务器 |
| `/mcp/{name}/disconnect` | POST | `mcp.disconnect` | 断开MCP服务器 |
| `/mcp/{name}/auth` | POST | `mcp.auth.start` | 启动MCP OAuth |
| `/mcp/{name}/auth` | DELETE | `mcp.auth.remove` | 移除MCP OAuth |

### 11. PTY 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/pty` | GET | `pty.list` | 列出PTY会话 |
| `/pty` | POST | `pty.create` | 创建PTY会话 |
| `/pty/{ptyID}` | GET | `pty.get` | 获取PTY会话 |
| `/pty/{ptyID}` | PUT | `pty.update` | 更新PTY会话 |
| `/pty/{ptyID}` | DELETE | `pty.remove` | 删除PTY会话 |
| `/pty/{ptyID}/connect` | GET | `pty.connect` | 连接PTY (WebSocket) |

### 12. Permission 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/permission` | GET | `permission.list` | 列出待处理的权限请求 |
| `/permission/{requestID}/reply` | POST | `permission.reply` | 回复权限请求 |
| `/session/{sessionID}/permissions/{permissionID}` | POST | `permission.respond` | 响应权限请求 |

### 13. Question 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/question` | GET | `question.list` | 列出待处理的问题 |
| `/question/{requestID}/reply` | POST | `question.reply` | 回答问题 |
| `/question/{requestID}/reject` | POST | `question.reject` | 拒绝问题 |

### 14. Experimental 模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/experimental/tool/ids` | GET | `tool.ids` | 列出工具ID |
| `/experimental/tool` | GET | `tool.list` | 列出工具详情 |
| `/experimental/workspace` | GET | `experimental.workspace.list` | 列出工作空间 |
| `/experimental/workspace` | POST | `experimental.workspace.create` | 创建工作空间 |
| `/experimental/worktree` | GET | `worktree.list` | 列出Worktree |
| `/experimental/worktree` | POST | `worktree.create` | 创建Worktree |

### 15. 其他模块

| 端点路径 | HTTP 方法 | 操作ID | 描述 |
|---------|----------|--------|------|
| `/path` | GET | `path.get` | 获取路径信息 |
| `/vcs` | GET | `vcs.get` | 获取VCS信息 |
| `/command` | GET | `command.list` | 列出可用命令 |
| `/log` | POST | `app.log` | 写入日志 |
| `/agent` | GET | `app.agents` | 列出可用Agent |
| `/skill` | GET | `app.skills` | 列出可用Skill |
| `/lsp` | GET | `lsp.status` | 获取LSP状态 |
| `/formatter` | GET | `formatter.status` | 获取Formatter状态 |
| `/tui/*` | POST/GET | `tui.*` | TUI相关操作 |

---

## 二、数据模型定义

### ID 前缀模式

所有ID都有前缀模式:
- Session ID: `^ses.*`
- Message ID: `^msg.*`
- Part ID: `^prt.*`
- Permission ID: `^per.*`
- Question ID: `^que.*`
- Pty ID: `^pty.*`
- Workspace ID: `^wrk.*`

### Session

```python
class Session:
    id: str                    # pattern: ^ses.*
    slug: str
    project_id: str
    workspace_id: Optional[str]
    directory: str
    parent_id: Optional[str]   # pattern: ^ses.*
    summary: Optional[SessionSummary]
    share: Optional[ShareInfo]
    title: str
    version: str
    time: TimeInfo
    permission: Optional[PermissionRuleset]
    revert: Optional[RevertInfo]

class SessionSummary:
    additions: int
    deletions: int
    files: int
    diffs: List[FileDiff]

class TimeInfo:
    created: int              # timestamp ms
    updated: int
    compacting: Optional[int]
    archived: Optional[int]
```

### Message

```python
class UserMessage:
    id: str
    session_id: str
    role: Literal["user"]
    time: TimeInfo
    format: Optional[OutputFormat]
    summary: Optional[MessageSummary]
    agent: str
    model: ModelRef
    system: Optional[str]
    tools: Optional[Dict[str, bool]]
    variant: Optional[str]

class AssistantMessage:
    id: str
    session_id: str
    role: Literal["assistant"]
    time: AssistantTimeInfo
    error: Optional[Error]
    parent_id: str
    model_id: str
    provider_id: str
    mode: str
    agent: str
    path: PathInfo
    summary: Optional[bool]
    cost: float
    tokens: TokenInfo
    structured: Optional[Any]
    variant: Optional[str]
    finish: Optional[str]

Message = Union[UserMessage, AssistantMessage]
```

### Part (消息部分)

```python
class TextPart:
    id: str
    session_id: str
    message_id: str
    type: Literal["text"]
    text: str
    synthetic: Optional[bool]
    ignored: Optional[bool]
    time: Optional[PartTime]
    metadata: Optional[Dict[str, Any]]

class FilePart:
    id: str
    session_id: str
    message_id: str
    type: Literal["file"]
    mime: str
    filename: Optional[str]
    url: str
    source: Optional[FilePartSource]

class ToolPart:
    id: str
    session_id: str
    message_id: str
    type: Literal["tool"]
    call_id: str
    tool: str
    state: ToolState
    metadata: Optional[Dict[str, Any]]

class ReasoningPart:
    id: str
    session_id: str
    message_id: str
    type: Literal["reasoning"]
    text: str
    metadata: Optional[Dict[str, Any]]
    time: PartTime

class SubtaskPart:
    id: str
    session_id: str
    message_id: str
    type: Literal["subtask"]
    prompt: str
    description: str
    agent: str
    model: Optional[ModelRef]
    command: Optional[str]

Part = Union[TextPart, FilePart, ToolPart, ReasoningPart, SubtaskPart, ...]
```

### ToolState

```python
class ToolStatePending:
    status: Literal["pending"]
    input: Dict[str, Any]
    raw: str

class ToolStateRunning:
    status: Literal["running"]
    input: Dict[str, Any]
    title: Optional[str]
    metadata: Optional[Dict[str, Any]]
    time: ToolTimeStart

class ToolStateCompleted:
    status: Literal["completed"]
    input: Dict[str, Any]
    output: str
    title: str
    metadata: Dict[str, Any]
    time: ToolTimeComplete
    attachments: Optional[List[FilePart]]

class ToolStateError:
    status: Literal["error"]
    input: Dict[str, Any]
    error: str
    metadata: Optional[Dict[str, Any]]
    time: ToolTimeComplete

ToolState = Union[ToolStatePending, ToolStateRunning, ToolStateCompleted, ToolStateError]
```

### Event (SSE)

```python
class GlobalEvent:
    directory: str
    payload: Event

# 主要事件类型
EventSessionCreated:
    type: Literal["session.created"]
    properties: Session

EventSessionUpdated:
    type: Literal["session.updated"]
    properties: Session

EventSessionDeleted:
    type: Literal["session.deleted"]
    properties: Session

EventSessionStatus:
    type: Literal["session.status"]
    properties: { session_id: str, status: SessionStatus }

EventMessageUpdated:
    type: Literal["message.updated"]
    properties: Message

EventMessagePartUpdated:
    type: Literal["message.part.updated"]
    properties: { part: Part, delta: Optional[str] }

EventPermissionAsked:
    type: Literal["permission.asked"]
    properties: PermissionRequest

EventQuestionAsked:
    type: Literal["question.asked"]
    properties: QuestionRequest

EventFileEdited:
    type: Literal["file.edited"]
    properties: { file: str }

EventTodoUpdated:
    type: Literal["todo.updated"]
    properties: { session_id: str, todos: List[Todo] }
```

### Provider & Model

```python
class Provider:
    id: str
    name: str
    source: Literal["env", "config", "custom", "api"]
    env: List[str]
    key: Optional[str]
    options: Dict[str, Any]
    models: Dict[str, Model]

class Model:
    id: str
    provider_id: str
    api: ApiInfo
    name: str
    family: Optional[str]
    capabilities: ModelCapabilities
    cost: ModelCost
    limit: ModelLimit
    status: Literal["alpha", "beta", "deprecated", "active"]
    options: Dict[str, Any]
    headers: Dict[str, str]
    release_date: str
    variants: Optional[Dict[str, Any]]

class ModelCapabilities:
    temperature: bool
    reasoning: bool
    attachment: bool
    toolcall: bool
    input: Modalities
    output: Modalities
```

### Config

```python
class Config:
    schema: Optional[str]
    log_level: Optional[Literal["DEBUG", "INFO", "WARN", "ERROR"]]
    model: Optional[str]              # format: provider/model
    small_model: Optional[str]
    default_agent: Optional[str]
    username: Optional[str]
    agent: Optional[Dict[str, AgentConfig]]
    provider: Optional[Dict[str, ProviderConfig]]
    mcp: Optional[Dict[str, McpConfig]]
    permission: Optional[PermissionConfig]
    tools: Optional[Dict[str, bool]]
    # ... more fields

class AgentConfig:
    model: Optional[str]
    temperature: Optional[float]
    top_p: Optional[float]
    prompt: Optional[str]
    disable: Optional[bool]
    description: Optional[str]
    mode: Optional[Literal["subagent", "primary", "all"]]
    color: Optional[str]
    steps: Optional[int]
    permission: Optional[PermissionConfig]
```

### Permission

```python
class PermissionRule:
    permission: str
    pattern: str
    action: Literal["allow", "deny", "ask"]

PermissionRuleset = List[PermissionRule]

class PermissionRequest:
    id: str                    # pattern: ^per.*
    session_id: str            # pattern: ^ses.*
    permission: str
    patterns: List[str]
    metadata: Dict[str, Any]
    always: List[str]
    tool: Optional[ToolRef]
```

### Question

```python
class QuestionRequest:
    id: str                    # pattern: ^que.*
    session_id: str
    questions: List[QuestionInfo]
    tool: Optional[ToolRef]

class QuestionInfo:
    question: str              # complete question
    header: str                # short label, max 30 chars
    options: List[QuestionOption]
    multiple: Optional[bool]   # allow multi-select
    custom: Optional[bool]     # allow custom answer

class QuestionOption:
    label: str                 # 1-5 words
    description: str           # option explanation

QuestionAnswer = List[str]
```

### File

```python
class FileNode:
    name: str
    path: str                  # relative path
    absolute: str              # absolute path
    type: Literal["file", "directory"]
    ignored: bool

class FileDiff:
    file: str
    before: str
    after: str
    additions: int
    deletions: int
    status: Optional[Literal["added", "deleted", "modified"]]

class File:
    path: str
    added: int
    removed: int
    status: Literal["added", "deleted", "modified"]
```

### Auth

```python
class OAuth:
    type: Literal["oauth"]
    refresh: str
    access: str
    expires: int
    account_id: Optional[str]
    enterprise_url: Optional[str]

class ApiAuth:
    type: Literal["api"]
    key: str

class WellKnownAuth:
    type: Literal["wellknown"]
    key: str
    token: str

Auth = Union[OAuth, ApiAuth, WellKnownAuth]
```

### OutputFormat

```python
class TextFormat:
    type: Literal["text"]

class JsonSchemaFormat:
    type: Literal["json_schema"]
    schema: Dict[str, Any]     # JSON Schema
    retry_count: Optional[int]

OutputFormat = Union[TextFormat, JsonSchemaFormat]
```

---

## 三、关键实现要点

### 1. SSE 事件流处理

`/global/event` 和 `/event` 返回 `text/event-stream`，需要实现异步迭代器:

```python
async def subscribe_events() -> AsyncIterator[Event]:
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", f"{base_url}/event") as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield parse_event(line[6:])
```

### 2. 消息流式响应

`POST /session/{sessionID}/message` 支持流式响应:

```python
async def send_message_stream(
    session_id: str,
    parts: List[PartInput]
) -> AsyncIterator[MessagePartDelta]:
    async with client.stream("POST", f"/session/{session_id}/message", json={...}):
        async for line in response.aiter_lines():
            yield parse_delta(line)
```

### 3. 通用查询参数

大多数API都支持:
- `directory`: 项目目录过滤
- `workspace`: 工作空间ID

### 4. 文件上传

FilePart 支持通过 `source` 字段指定文件来源:
```python
{
    "type": "file",
    "mime": "text/plain",
    "url": "file:///path/to/file",
    "source": {
        "type": "file",
        "path": "src/main.py",
        "text": { "value": "...", "start": 0, "end": 100 }
    }
}
```

### 5. 结构化输出

支持 JSON Schema 格式的结构化输出:
```python
result = client.message.send(
    session_id="ses_xxx",
    parts=[{"type": "text", "text": "Extract info"}],
    format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {...}
        }
    }
)
```
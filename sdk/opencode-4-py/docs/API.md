# OpenCode HTTP API 文档

## 概述

OpenCode Server 通过 HTTP API 暴露所有功能，支持 OpenAPI 3.1 规范。

- 默认端口: `4096`
- 默认主机: `127.0.0.1`
- OpenAPI 文档: `http://<hostname>:<port>/doc`

## 认证

设置环境变量 `OPENCODE_SERVER_PASSWORD` 启用 HTTP Basic Auth:
- 用户名: `OPENCODE_SERVER_USERNAME` (默认: `opencode`)
- 密码: `OPENCODE_SERVER_PASSWORD`

---

## API 端点

### Global (全局)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/global/health` | 健康检查，返回 `{ healthy: true, version: string }` |
| GET | `/global/event` | 全局事件 SSE 流 |

### Project (项目)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/project` | 列出所有项目 |
| GET | `/project/current` | 获取当前项目 |

### Path & VCS (路径与版本控制)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/path` | 获取当前路径信息 |
| GET | `/vcs` | 获取 VCS 信息 (分支等) |

### Instance (实例)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/instance/dispose` | 销毁当前实例 |

### Config (配置)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/config` | 获取配置 |
| PATCH | `/config` | 更新配置 |
| GET | `/config/providers` | 列出提供商和默认模型 |

### Provider (提供商)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/provider` | 列出所有提供商 |
| GET | `/provider/auth` | 获取认证方法 |
| POST | `/provider/{id}/oauth/authorize` | OAuth 授权 |
| POST | `/provider/{id}/oauth/callback` | OAuth 回调 |

### Sessions (会话) - 核心功能

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/session` | 列出所有会话 |
| POST | `/session` | 创建新会话 |
| GET | `/session/status` | 获取所有会话状态 |
| GET | `/session/:id` | 获取会话详情 |
| DELETE | `/session/:id` | 删除会话 |
| PATCH | `/session/:id` | 更新会话属性 |
| GET | `/session/:id/children` | 获取子会话 |
| GET | `/session/:id/todo` | 获取待办列表 |
| POST | `/session/:id/init` | 分析应用并创建 AGENTS.md |
| POST | `/session/:id/fork` | 分叉会话 |
| POST | `/session/:id/abort` | 中止运行中的会话 |
| POST | `/session/:id/share` | 分享会话 |
| DELETE | `/session/:id/share` | 取消分享 |
| GET | `/session/:id/diff` | 获取会话差异 |
| POST | `/session/:id/summarize` | 总结会话 |
| POST | `/session/:id/revert` | 撤回消息 |
| POST | `/session/:id/unrevert` | 恢复撤回的消息 |
| POST | `/session/:id/permissions/:permissionID` | 响应权限请求 |

### Messages (消息)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/session/:id/message` | 列出会话消息 |
| POST | `/session/:id/message` | 发送消息并等待响应 |
| GET | `/session/:id/message/:messageID` | 获取消息详情 |
| POST | `/session/:id/prompt_async` | 异步发送消息 (不等待) |
| POST | `/session/:id/command` | 执行斜杠命令 |
| POST | `/session/:id/shell` | 运行 shell 命令 |

### Commands (命令)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/command` | 列出所有命令 |

### Files (文件)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/find?pattern=<pat>` | 搜索文件内容 |
| GET | `/find/file?query=<q>` | 按名称查找文件 |
| GET | `/find/symbol?query=<q>` | 查找工作区符号 |
| GET | `/file?path=<path>` | 列出文件和目录 |
| GET | `/file/content?path=<p>` | 读取文件内容 |
| GET | `/file/status` | 获取追踪文件状态 |

### Tools (工具 - 实验性)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/experimental/tool/ids` | 列出工具 ID |
| GET | `/experimental/tool?provider=<p>&model=<m>` | 列出工具 JSON Schema |

### LSP, Formatters & MCP

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/lsp` | LSP 服务器状态 |
| GET | `/formatter` | 格式化器状态 |
| GET | `/mcp` | MCP 服务器状态 |
| POST | `/mcp` | 动态添加 MCP 服务器 |

### Agents (代理)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/agent` | 列出所有可用代理 |

### Logging (日志)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/log` | 写入日志条目 |

### TUI (终端界面控制)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/tui/append-prompt` | 追加文本到提示 |
| POST | `/tui/open-help` | 打开帮助对话框 |
| POST | `/tui/open-sessions` | 打开会话选择器 |
| POST | `/tui/open-themes` | 打开主题选择器 |
| POST | `/tui/open-models` | 打开模型选择器 |
| POST | `/tui/submit-prompt` | 提交当前提示 |
| POST | `/tui/clear-prompt` | 清除提示 |
| POST | `/tui/execute-command` | 执行命令 |
| POST | `/tui/show-toast` | 显示 toast 通知 |

### Auth (认证)

| 方法 | 路径 | 描述 |
|------|------|------|
| PUT | `/auth/:id` | 设置认证凭据 |

### Events (事件)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/event` | SSE 事件流 |

---

## 核心数据类型

### Session (会话)
```python
class Session:
    id: str
    project_id: str
    directory: str
    parent_id: Optional[str]
    title: str
    version: str
    time: TimeInfo
    summary: Optional[SessionSummary]
    share: Optional[ShareInfo]
    revert: Optional[RevertInfo]
```

### Message (消息)
```python
class UserMessage:
    id: str
    session_id: str
    role: Literal["user"]
    time: TimeInfo
    agent: str
    model: ModelRef
    system: Optional[str]
    tools: Optional[Dict[str, bool]]

class AssistantMessage:
    id: str
    session_id: str
    role: Literal["assistant"]
    time: TimeInfo
    parent_id: str
    model_id: str
    provider_id: str
    mode: str
    cost: float
    tokens: TokenInfo
    error: Optional[Error]
```

### Part (消息部分)
```python
# 支持的类型:
- TextPart      # 文本内容
- ReasoningPart # 推理过程
- FilePart      # 文件附件
- ToolPart      # 工具调用
- StepStartPart # 步骤开始
- StepFinishPart # 步骤结束
- SnapshotPart  # 快照
- PatchPart     # 补丁
- AgentPart     # 代理引用
- SubtaskPart   # 子任务
```

### Provider (提供商)
```python
class Provider:
    id: str
    name: str
    source: Literal["env", "config", "custom", "api"]
    env: List[str]
    key: Optional[str]
    options: Dict[str, Any]
    models: Dict[str, Model]
```

### Model (模型)
```python
class Model:
    id: str
    provider_id: str
    name: str
    capabilities: ModelCapabilities
    cost: ModelCost
    limit: ModelLimit
    status: Literal["alpha", "beta", "deprecated", "active"]
```

### Config (配置)
```python
class Config:
    theme: Optional[str]
    model: Optional[str]
    small_model: Optional[str]
    agent: Optional[Dict[str, AgentConfig]]
    provider: Optional[Dict[str, ProviderConfig]]
    mcp: Optional[Dict[str, McpConfig]]
    permission: Optional[PermissionConfig]
    # ... 更多字段
```

---

## 事件类型 (SSE)

```python
# 服务器事件
"server.connected"
"server.instance.disposed"

# 会话事件
"session.created"
"session.updated"
"session.deleted"
"session.status"
"session.idle"
"session.compacted"
"session.diff"
"session.error"

# 消息事件
"message.updated"
"message.removed"
"message.part.updated"
"message.part.removed"

# 权限事件
"permission.updated"
"permission.replied"

# 文件事件
"file.edited"
"file.watcher.updated"

# 其他
"todo.updated"
"command.executed"
"lsp.updated"
"vcs.branch.updated"
```

---

## 使用示例

### 创建客户端并发送消息

```python
from opencode_4_py import OpenCodeClient

client = OpenCodeClient(base_url="http://localhost:4096")

# 创建会话
session = client.session.create(title="My Session")

# 发送消息
result = client.session.prompt(
    session_id=session.id,
    parts=[{"type": "text", "text": "Hello!"}]
)

print(result.info)
print(result.parts)
```

### 监听事件

```python
for event in client.events.subscribe():
    print(f"Event: {event.type}")
    print(f"Data: {event.properties}")
```

### 文件操作

```python
# 搜索文件内容
results = client.find.text(pattern="function.*opencode")

# 按名称查找文件
files = client.find.files(query="*.py", type="file")

# 读取文件
content = client.file.read(path="src/main.py")
```
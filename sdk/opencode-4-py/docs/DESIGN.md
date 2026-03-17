# OpenCode Python SDK 设计文档

## 1. 项目目标

为 OpenCode Server 提供类型安全的 Python SDK，支持:
- 同步和异步客户端
- 完整的 API 覆盖
- SSE 事件流支持
- 自动重试和错误处理
- 结构化输出支持

## 2. 项目结构

```
src/opencode_4_py/
├── __init__.py          # 公共 API 导出
├── client.py            # 主客户端类
├── async_client.py      # 异步客户端类
├── config.py            # 客户端配置
├── errors.py            # 自定义异常
├── models/              # 数据模型
│   ├── __init__.py
│   ├── session.py       # Session 相关模型
│   ├── message.py       # Message 相关模型
│   ├── provider.py      # Provider/Model 模型
│   ├── config.py        # Config 模型
│   ├── event.py         # Event 模型
│   └── common.py        # 通用模型
├── api/                 # API 端点实现
│   ├── __init__.py
│   ├── global_.py       # Global API
│   ├── project.py       # Project API
│   ├── session.py       # Session API
│   ├── message.py       # Message API
│   ├── file.py          # File API
│   ├── provider.py      # Provider API
│   ├── config.py        # Config API
│   ├── agent.py         # Agent API
│   ├── tui.py           # TUI API
│   └── event.py         # Event API
└── utils/               # 工具函数
    ├── __init__.py
    ├── http.py          # HTTP 客户端封装
    └── sse.py           # SSE 流处理
```

## 3. 核心类设计

### 3.1 客户端配置

```python
@dataclass
class ClientConfig:
    base_url: str = "http://localhost:4096"
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
```

### 3.2 主客户端

```python
class OpenCodeClient:
    """同步客户端"""
    
    def __init__(self, config: Optional[ClientConfig] = None): ...
    
    # API 模块
    @property
    def session(self) -> SessionAPI: ...
    @property
    def message(self) -> MessageAPI: ...
    @property
    def project(self) -> ProjectAPI: ...
    @property
    def file(self) -> FileAPI: ...
    @property
    def provider(self) -> ProviderAPI: ...
    @property
    def config(self) -> ConfigAPI: ...
    @property
    def agent(self) -> AgentAPI: ...
    @property
    def tui(self) -> TuiAPI: ...
    @property
    def event(self) -> EventAPI: ...
    
    # 便捷方法
    def health_check(self) -> HealthResponse: ...
    def close(self) -> None: ...
```

### 3.3 异步客户端

```python
class AsyncOpenCodeClient:
    """异步客户端"""
    
    async def __aenter__(self) -> "AsyncOpenCodeClient": ...
    async def __aexit__(self, *args) -> None: ...
    
    # API 模块 (异步版本)
    @property
    def session(self) -> AsyncSessionAPI: ...
    # ... 其他 API 模块
```

## 4. API 模块设计

### 4.1 Session API

```python
class SessionAPI:
    def list(self) -> List[Session]: ...
    def get(self, session_id: str) -> Session: ...
    def create(self, title: Optional[str] = None, parent_id: Optional[str] = None) -> Session: ...
    def delete(self, session_id: str) -> bool: ...
    def update(self, session_id: str, title: str) -> Session: ...
    def abort(self, session_id: str) -> bool: ...
    def share(self, session_id: str) -> Session: ...
    def unshare(self, session_id: str) -> Session: ...
    def fork(self, session_id: str, message_id: Optional[str] = None) -> Session: ...
    def get_children(self, session_id: str) -> List[Session]: ...
    def get_todos(self, session_id: str) -> List[Todo]: ...
    def get_diff(self, session_id: str, message_id: Optional[str] = None) -> List[FileDiff]: ...
    def summarize(self, session_id: str, provider_id: str, model_id: str) -> bool: ...
    def revert(self, session_id: str, message_id: str, part_id: Optional[str] = None) -> bool: ...
    def unrevert(self, session_id: str) -> bool: ...
    def respond_permission(self, session_id: str, permission_id: str, response: str, remember: bool = False) -> bool: ...
```

### 4.2 Message API

```python
class MessageAPI:
    def list(self, session_id: str, limit: Optional[int] = None) -> List[MessageWithParts]: ...
    def get(self, session_id: str, message_id: str) -> MessageWithParts: ...
    def send(
        self,
        session_id: str,
        parts: List[PartInput],
        model: Optional[ModelRef] = None,
        agent: Optional[str] = None,
        system: Optional[str] = None,
        tools: Optional[Dict[str, bool]] = None,
        no_reply: bool = False,
    ) -> MessageWithParts: ...
    def send_async(self, session_id: str, parts: List[PartInput], ...) -> None: ...
    def execute_command(
        self,
        session_id: str,
        command: str,
        arguments: Optional[str] = None,
        model: Optional[ModelRef] = None,
        agent: Optional[str] = None,
    ) -> MessageWithParts: ...
    def run_shell(
        self,
        session_id: str,
        command: str,
        model: Optional[ModelRef] = None,
        agent: Optional[str] = None,
    ) -> MessageWithParts: ...
```

### 4.3 File API

```python
class FileAPI:
    def list(self, path: str) -> List[FileNode]: ...
    def read(self, path: str) -> FileContent: ...
    def get_status(self) -> List[File]: ...
    
    # 搜索
    def search_text(self, pattern: str) -> List[TextSearchResult]: ...
    def find_files(self, query: str, type: Optional[str] = None, limit: int = 100) -> List[str]: ...
    def find_symbols(self, query: str) -> List[Symbol]: ...
```

### 4.4 Event API

```python
class EventAPI:
    def subscribe(self) -> Iterator[Event]: ...
    def subscribe_async(self) -> AsyncIterator[Event]: ...
```

## 5. 数据模型

### 5.1 使用 Pydantic v2

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class Session(BaseModel):
    id: str = Field(..., alias="sessionID")  # 支持 JSON 字段别名
    project_id: str = Field(..., alias="projectID")
    directory: str
    parent_id: Optional[str] = Field(None, alias="parentID")
    title: str
    version: str
    time: TimeInfo
    summary: Optional[SessionSummary] = None
    share: Optional[ShareInfo] = None
    
    class Config:
        populate_by_name = True
```

### 5.2 联合类型处理

```python
from typing import Union, Annotated
from pydantic import Field, Tag

Message = Annotated[Union[UserMessage, AssistantMessage], Field(discriminator="role")]

Part = Annotated[
    Union[TextPart, FilePart, ToolPart, ReasoningPart, ...],
    Field(discriminator="type")
]
```

## 6. 错误处理

```python
class OpenCodeError(Exception):
    """基础异常"""

class ConnectionError(OpenCodeError):
    """连接错误"""

class AuthenticationError(OpenCodeError):
    """认证错误"""

class NotFoundError(OpenCodeError):
    """资源不存在"""

class ValidationError(OpenCodeError):
    """验证错误"""

class APIError(OpenCodeError):
    """API 错误"""
    def __init__(self, message: str, status_code: int, response_body: str):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)
```

## 7. SSE 事件流

```python
class SSEClient:
    def __init__(self, url: str, headers: Dict[str, str]): ...
    
    def __iter__(self) -> Iterator[Event]: ...
    
    async def __aiter__(self) -> AsyncIterator[Event]: ...
    
    def close(self) -> None: ...
```

## 8. 依赖

```
pydantic>=2.0        # 数据验证和序列化
httpx>=0.25.0        # HTTP 客户端 (支持同步和异步)
typing-extensions    # 类型扩展
```

## 9. 开发计划

### Phase 1: 基础架构
- [ ] 数据模型定义
- [ ] HTTP 客户端封装
- [ ] 错误处理
- [ ] 配置管理

### Phase 2: 核心 API
- [ ] Session API
- [ ] Message API
- [ ] File API
- [ ] Provider API

### Phase 3: 高级功能
- [ ] SSE 事件流
- [ ] 异步客户端
- [ ] 结构化输出
- [ ] 自动重试

### Phase 4: 完善与测试
- [ ] 单元测试
- [ ] 集成测试
- [ ] 文档
- [ ] 示例代码
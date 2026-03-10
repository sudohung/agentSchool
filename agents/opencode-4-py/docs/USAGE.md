# OpenCode Python SDK 使用指南

## 安装

```bash
pip install opencode-4-py
```

依赖:
- httpx >= 0.25.0
- pydantic >= 2.0.0
- typing-extensions >= 4.0.0

## 快速开始

### 1. 基本使用

```python
from opencode_4_py import OpenCodeClient

# 创建客户端
client = OpenCodeClient()

# 检查服务器健康状态
health = client.health_check()
print(f"服务器版本：{health['version']}")

# 使用上下文管理器
with OpenCodeClient() as client:
    health = client.health_check()
    print(f"健康状态：{health}")
```

### 2. 配置连接

```python
from opencode_4_py import OpenCodeClient, ClientConfig

# 自定义配置
config = ClientConfig(
    base_url="http://127.0.0.1:4096",
    username="opencode",
    password="your-password",  # 如果设置了 OPENCODE_SERVER_PASSWORD
    timeout=60.0,
)

client = OpenCodeClient(config=config)
```

### 3. 会话管理

```python
from opencode_4_py import OpenCodeClient

with OpenCodeClient() as client:
    # 创建会话
    session = client.session.create(title="我的第一个会话")
    print(f"创建会话：{session.id}")
    
    # 获取会话列表
    sessions = client.session.list()
    for s in sessions:
        print(f"会话：{s.title} ({s.id})")
    
    # 获取会话详情
    session = client.session.get(session_id="ses_xxx")
    print(f"会话标题：{session.title}")
    
    # 更新会话
    session = client.session.update(
        session_id="ses_xxx",
        title="新标题"
    )
    
    # 删除会话
    client.session.delete(session_id="ses_xxx")
```

### 4. 发送消息

```python
from opencode_4_py import OpenCodeClient

with OpenCodeClient() as client:
    # 创建会话
    session = client.session.create()
    
    # 发送文本消息
    result = client.message.send_text(
        session_id=session.id,
        text="请帮我写一个 Python 函数，计算斐波那契数列",
    )
    
    # 打印响应
    for part in result.parts:
        if part.type == "text":
            print(part.text)
        elif part.type == "tool":
            print(f"工具调用：{part.tool} - {part.state.status}")
```

### 5. 使用模型和代理

```python
from opencode_4_py import OpenCodeClient, ModelRef

with OpenCodeClient() as client:
    session = client.session.create()
    
    # 指定模型
    model = ModelRef(
        provider_id="anthropic",
        model_id="claude-3-5-sonnet-20241022"
    )
    
    result = client.message.send_text(
        session_id=session.id,
        text="Hello!",
        model=model,
        agent="build",  # 使用 build 代理
    )
```

### 6. 执行命令

```python
from opencode_4_py import OpenCodeClient

with OpenCodeClient() as client:
    session = client.session.create()
    
    # 执行斜杠命令
    result = client.message.command(
        session_id=session.id,
        command="/test",
        arguments="src/main.py",
    )
    
    # 执行 Shell 命令
    result = client.message.shell(
        session_id=session.id,
        command="ls -la",
        agent="build",
    )
```

### 7. 监听事件 (SSE)

```python
from opencode_4_py import OpenCodeClient

with OpenCodeClient() as client:
    # 订阅全局事件
    print("订阅全局事件...")
    for event in client.event.subscribe_global():
        print(f"事件类型：{event.type}")
        print(f"事件数据：{event.properties}")
        
        # 可以在这里添加退出条件
        if event.type == "session.created":
            break
```

### 8. 异步客户端

```python
import asyncio
from opencode_4_py import AsyncOpenCodeClient

async def main():
    async with AsyncOpenCodeClient() as client:
        # 健康检查
        health = await client.health_check()
        print(f"服务器版本：{health['version']}")
        
        # 创建会话
        session = await client.session.create(title="异步会话")
        
        # 发送消息
        result = await client.message.send_text(
            session_id=session.id,
            text="Hello from async!",
        )
        
        # 打印响应
        for part in result.parts:
            if part.type == "text":
                print(part.text)

asyncio.run(main())
```

### 9. 高级会话操作

```python
from opencode_4_py import OpenCodeClient

with OpenCodeClient() as client:
    session = client.session.create(title="主会话")
    
    # 获取待办事项
    todos = client.session.todos(session_id=session.id)
    for todo in todos:
        print(f"[{todo.priority}] {todo.content} - {todo.status}")
    
    # 获取子会话
    children = client.session.children(session_id=session.id)
    
    # 分叉会话
    forked = client.session.fork(
        session_id=session.id,
        message_id="msg_xxx"
    )
    
    # 分享会话
    shared = client.session.share(session_id=session.id)
    print(f"分享链接：{shared.share.url}")
    
    # 获取会话差异
    diffs = client.session.diff(session_id=session.id)
    for diff in diffs:
        print(f"文件：{diff.file}")
        print(f"新增：{diff.additions}, 删除：{diff.deletions}")
```

### 10. 错误处理

```python
from opencode_4_py import (
    OpenCodeClient,
    OpenCodeError,
    ConnectionError,
    NotFoundError,
    APIError,
)

try:
    client = OpenCodeClient()
    session = client.session.get(session_id="invalid_id")
except ConnectionError as e:
    print(f"连接失败：{e}")
except NotFoundError as e:
    print(f"资源不存在：{e}")
except APIError as e:
    print(f"API 错误：{e.status_code} - {e.message}")
except OpenCodeError as e:
    print(f"SDK 错误：{e}")
```

## 数据模型

### Session

```python
session.id           # 会话 ID (ses_xxx)
session.title        # 会话标题
session.directory    # 项目目录
session.parent_id    # 父会话 ID
session.time.created # 创建时间戳
session.time.updated # 更新时间戳
```

### Message

```python
result.info.id            # 消息 ID
result.info.session_id    # 会话 ID
result.info.role          # "user" 或 "assistant"
result.info.model         # 模型信息
result.info.tokens.input  # 输入 token 数
result.info.tokens.output # 输出 token 数
result.info.cost          # 成本
```

### Part

```python
part.id          # Part ID
part.type        # "text", "file", "tool", "reasoning" 等
part.text        # 文本内容 (TextPart)
part.tool        # 工具名称 (ToolPart)
part.state       # 工具状态 (ToolPart)
```

## 最佳实践

### 1. 使用上下文管理器

```python
# 推荐：自动关闭连接
with OpenCodeClient() as client:
    # 使用客户端
    pass

# 不推荐：需要手动关闭
client = OpenCodeClient()
# ... 使用客户端
client.close()
```

### 2. 复用会话

```python
# 创建一次会话，多次使用
session = client.session.create()

# 在同一会话中发送多条消息
client.message.send_text(session_id=session.id, text="问题 1")
client.message.send_text(session_id=session.id, text="问题 2")
```

### 3. 处理长消息

```python
result = client.message.send_text(
    session_id=session.id,
    text="长消息...",
)

# 流式处理响应
for part in result.parts:
    if part.type == "text":
        print(part.text, end="", flush=True)
```

### 4. 使用结构化输出

```python
result = client.message.send(
    session_id=session.id,
    parts=[{"type": "text", "text": "提取公司信息"}],
    format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "founded": {"type": "number"}
            },
            "required": ["company"]
        }
    }
)

# 访问结构化输出
print(result.info.structured)
```

## API 参考

### OpenCodeClient

| 方法 | 描述 |
|------|------|
| `health_check()` | 检查服务器健康状态 |
| `close()` | 关闭连接 |

### Session API

| 方法 | 描述 |
|------|------|
| `list()` | 列出会话 |
| `get(session_id)` | 获取会话 |
| `create(title, parent_id)` | 创建会话 |
| `delete(session_id)` | 删除会话 |
| `update(session_id, title)` | 更新会话 |
| `abort(session_id)` | 中止会话 |
| `share(session_id)` | 分享会话 |
| `fork(session_id, message_id)` | 分叉会话 |
| `todos(session_id)` | 获取待办 |
| `children(session_id)` | 获取子会话 |

### Message API

| 方法 | 描述 |
|------|------|
| `list(session_id, limit)` | 列出消息 |
| `get(session_id, message_id)` | 获取消息 |
| `send(session_id, parts, ...)` | 发送消息 |
| `send_text(session_id, text, ...)` | 发送文本消息 |
| `command(session_id, command, ...)` | 执行命令 |
| `shell(session_id, command, ...)` | 执行 Shell |

### Event API

| 方法 | 描述 |
|------|------|
| `subscribe_global()` | 订阅全局事件 |
| `subscribe()` | 订阅项目事件 |

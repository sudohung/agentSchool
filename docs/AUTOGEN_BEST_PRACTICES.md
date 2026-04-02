# AutoGen 最佳使用实践

> 版本: v0.4+ (2026)
> 基于微软官方文档整理

## 目录

- [1. 概述](#1-概述)
- [2. 核心架构理解](#2-核心架构理解)
- [3. Agent 设计最佳实践](#3-agent-设计最佳实践)
- [4. 模型配置](#4-模型配置)
- [5. 工具使用](#5-工具使用)
- [6. 代码执行](#6-代码执行)
- [7. MCP 集成](#7-mcp-集成)
- [8. 记忆管理](#8-记忆管理)
- [9. 会话管理与隔离](#9-会话管理与隔离)
- [10. 多Agent协作模式](#10-多agent协作模式)
- [11. 性能优化](#11-性能优化)
- [12. 生产部署](#12-生产部署)
- [13. 常见问题与解决方案](#13-常见问题与解决方案)

---

## 1. 概述

### AutoGen 两套 API

| API | 适用场景 | 复杂度 |
|-----|---------|--------|
| **AgentChat** | 快速开发、预置模式 | 低 |
| **Core** | 事件驱动、分布式、自定义 | 高 |

**推荐**: 新项目从 AgentChat 开始，需要精细控制时再迁移到 Core API。

### 版本说明

- v0.4+ (2026): 全新架构，支持分布式运行时
- v0.2: 旧版本，功能更简单

---

## 2. 核心架构理解

### 2.1 事件驱动模型

AutoGen 基于 Actor 模型，Agent 通过异步消息通信：

```
┌─────────┐     Message     ┌─────────┐
│ Agent A │ ──────────────► │ Agent B │
│         │ ◄────────────── │         │
└─────────┘    Response     └─────────┘
```

### 2.2 运行时环境

| 环境 | 说明 | 适用场景 |
|------|------|---------|
| `SingleThreadedAgentRuntime` | 单线程异步 | 本地开发、测试 |
| `GrpcRuntime` | gRPC 分布式 | 生产部署 |

---

## 3. Agent 设计最佳实践

### 3.1 使用 AgentChat (推荐)

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 创建模型客户端
model_client = OpenAIChatCompletionClient(model="gpt-4o")

# 创建 Agent
agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    system_message="你是一个专业的代码审查专家。",
    tools=[my_tool_function]
)
```

### 3.2 System Prompt 设计

```python
# ❌ 错误示例: 过于模糊
system_message = "你是助手"

# ✅ 正确示例: 明确角色、能力和边界
system_message = """
你是一个Python代码审查专家。

职责:
1. 检查代码质量和性能问题
2. 提供具体的改进建议
3. 验证代码是否符合PEP8规范

限制:
- 只审查Python代码
- 不执行未知的外部脚本
"""
```

### 3.3 Agent 描述

为每个Agent提供清晰的描述，以便其他Agent或Manager理解其能力：

```python
agent = AssistantAgent(
    name="writer",
    description="负责创建和修改文本内容，擅长技术文档写作",
    ...
)
```

---

## 4. 模型配置

### 4.1 OpenAI 兼容模型

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

# OpenAI
client = OpenAIChatCompletionClient(
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2000
)

# DeepSeek (OpenAI 兼容)
client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key="sk-xxx"
)

# 通义千问
client = OpenAIChatCompletionClient(
    model="qwen-turbo",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-xxx"
)
```

### 4.2 Anthropic Claude

```python
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

client = AnthropicChatCompletionClient(
    model="claude-3-5-sonnet-20241022",
    api_key="sk-ant-xxx"
)
```

### 4.3 本地模型 (Ollama)

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

client = OpenAIChatCompletionClient(
    model="llama3.2",
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Ollama不需要真实key
)
```

### 4.4 缓存响应

```python
from autogen_ext.models.cache import ChatCompletionCache
from autogen_ext.cache_store.diskcache import DiskCacheStore
from diskcache import Cache

# 使用 DiskCache 缓存
openai_client = OpenAIChatCompletionClient(model="gpt-4o")
cache_store = DiskCacheStore(Cache("./cache_dir"))
cached_client = ChatCompletionCache(openai_client, cache_store)

# 相同请求将返回缓存结果
response1 = await cached_client.create([UserMessage(...)])
response2 = await cached_client.create([UserMessage(...)])  # 来自缓存
```

---

## 5. 工具使用

### 5.1 基本工具注册

```python
from autogen_core.tools import FunctionTool

def get_weather(city: str, date: str) -> str:
    """获取指定城市和日期的天气信息"""
    return f"{city}在{date}的天气是晴天"

# 创建工具
weather_tool = FunctionTool(get_weather, description="获取天气信息")

# 注册到Agent
agent = AssistantAgent(
    name="assistant",
    tools=[weather_tool]
)
```

### 5.2 异步工具

```python
import aiohttp
from autogen_core.tools import FunctionTool

async def search_web(query: str) -> str:
    """搜索网页"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.search?q={query}") as resp:
            return await resp.text()

search_tool = FunctionTool(search_web, description="搜索网页")
```

### 5.3 HTTP API 工具

```python
from autogen_ext.tools import HttpTool

# 定义REST API调用
api_tool = HttpTool(
    name="get_stock",
    description="获取股票价格",
    scheme="https",
    host="api.example.com",
    path="/stock/{ticker}",
    method="GET",
    path_parameters_schema={
        "type": "object",
        "properties": {
            "ticker": {"type": "string"}
        }
    }
)
```

### 5.4 LangChain 工具集成

```python
from langchain.tools import WikipediaQueryRun
from autogen_ext.tools.langchain import LangChainToolAdapter

# 将LangChain工具包装为AutoGen工具
langchain_tool = WikipediaQueryRun(...)
autogen_tool = LangChainToolAdapter(langchain_tool)
```

---

## 6. 代码执行

### 6.1 Docker 隔离执行 (推荐)

```python
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool

# 创建Docker代码执行器
code_executor = DockerCommandLineCodeExecutor(
    timeout=60,
    work_dir="./workspace"
)
await code_executor.start()

# 创建代码执行工具
code_tool = PythonCodeExecutionTool(code_executor)

# 注册到Agent
agent = AssistantAgent(
    name="coder",
    tools=[code_tool]
)
```

### 6.2 本地执行 (谨慎使用)

```python
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

# ⚠️ 仅在受信任环境中使用
executor = LocalCommandLineCodeExecutor(
    timeout=30,
    work_dir="./sandbox"
)
```

### 6.3 最佳实践

- 生产环境务必使用 Docker 隔离
- 设置合理的超时时间
- 限制工作目录范围
- 不要执行用户直接提供的代码

---

## 7. MCP 集成

### 7.1 安装

```bash
pip install -U "autogen-ext[mcp]"
```

### 7.2 STDIO 方式

```python
from autogen_ext.tools import mcp_server_tools, StdioServerParams

# 配置 MCP 服务器
mcp_server = StdioServerParams(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "./data"]
)

# 获取工具
tools = await mcp_server_tools(mcp_server)

# 注册到Agent
agent = AssistantAgent(
    name="file_manager",
    tools=tools
)
```

### 7.3 HTTP 方式

```python
from autogen_ext.tools import mcp_server_tools, StreamableHttpServerParams

mcp_server = StreamableHttpServerParams(
    url="http://localhost:3000/mcp"
)

tools = await mcp_server_tools(mcp_server)
```

### 7.4 推荐的 MCP 服务器

| 服务器 | 功能 |
|--------|------|
| `@modelcontextprotocol/server-filesystem` | 文件系统操作 |
| `@modelcontextprotocol/server-github` | GitHub API |
| `@modelcontextprotocol/server-slack` | Slack 集成 |
| `@modelcontextprotocol/server-postgres` | PostgreSQL 查询 |

---

## 8. 记忆管理

### 8.1 Memory 协议概述

AutoGen 定义了 `Memory` 协议，支持多种记忆存储实现：

| 方法 | 说明 |
|------|------|
| `add()` | 添加记忆条目 |
| `query()` | 检索相关记忆 |
| `update_context()` | 将记忆注入Agent上下文 |
| `clear()` | 清空记忆 |
| `close()` | 释放资源 |

### 8.2 短期记忆 (对话历史)

```python
from autogen_core.model_context import BufferedChatCompletionContext

# 保留最近10条消息
model_context = BufferedChatCompletionContext(buffer_size=10)

agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    model_context=model_context
)
```

### 8.3 长期记忆 - ListMemory

`ListMemory` 是最简单的记忆实现，按时间顺序维护记忆：

```python
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

# 创建记忆存储
user_memory = ListMemory()

# 添加记忆
await user_memory.add(MemoryContent(
    content="用户偏好使用公制单位",
    mime_type=MemoryMimeType.TEXT
))

await user_memory.add(MemoryContent(
    content="用户的饮食是素食主义",
    mime_type=MemoryMimeType.TEXT
))

# 注册到Agent
agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    tools=[get_weather],
    memory=[user_memory]
)
```

**记忆检索时机**: 在每次 `agent.run()` 时，自动在 LLM 调用前执行检索，结果注入为 `SystemMessage`：

```python
# Agent内部自动执行的流程:
# 1. 用户输入 -> 2. 记忆检索 -> 3. 注入上下文 -> 4. LLM推理 -> 5. 输出

# 检索后注入的 SystemMessage 示例:
"""
Relevant memory content (in chronological order):
1. 用户偏好使用公制单位
2. 用户的饮食是素食主义
"""
```

### 8.4 长期记忆 - ChromaDB 向量存储

使用向量数据库实现语义检索：

```python
from autogen_ext.memory.chromadb import (
    ChromaDBVectorMemory,
    PersistentChromaDBVectorMemoryConfig,
    SentenceTransformerEmbeddingFunctionConfig
)

# 创建向量记忆存储
chroma_memory = ChromaDBVectorMemory(
    config=PersistentChromaDBVectorMemoryConfig(
        collection_name="user_preferences",
        persistence_path="./chroma_db",
        k=3,  # 返回 top-k 结果
        score_threshold=0.4,  # 最低相似度阈值
        embedding_function_config=SentenceTransformerEmbeddingFunctionConfig(
            model_name="all-MiniLM-L6-v2"
        )
    )
)

# 添加记忆 (带元数据)
await chroma_memory.add(MemoryContent(
    content="用户喜欢Python编程",
    mime_type=MemoryMimeType.TEXT,
    metadata={"category": "preference", "type": "language"}
))

# 注册到Agent
agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    memory=[chroma_memory]
)
```

### 8.5 长期记忆 - Redis 存储

生产环境推荐使用 Redis：

```python
from autogen_ext.memory.redis import RedisMemory, RedisMemoryConfig

redis_memory = RedisMemory(
    config=RedisMemoryConfig(
        redis_url="redis://localhost:6379",
        index_name="chat_history",
        prefix="memory"
    )
)

agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    memory=[redis_memory]
)
```

### 8.6 长期记忆 - Mem0 集成

```python
from autogen_ext.memory.mem0 import Mem0Memory

mem0_memory = Mem0Memory(
    is_cloud=True,
    limit=5  # 最多检索5条记忆
)

agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    memory=[mem0_memory]
)
```

### 8.7 RAG 实现

完整的 RAG (检索增强生成) 模式：

```python
import re
import aiohttp
import aiofiles
from typing import List
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType

class SimpleDocumentIndexer:
    """文档索引器 - 用于RAG"""
    
    def __init__(self, memory: Memory, chunk_size: int = 1500):
        self.memory = memory
        self.chunk_size = chunk_size
    
    async def _fetch_content(self, source: str) -> str:
        if source.startswith(("http://", "https://")):
            async with aiohttp.ClientSession() as session:
                async with session.get(source) as response:
                    return await response.text()
        else:
            async with aiofiles.open(source, "r", encoding="utf-8") as f:
                return await f.read()
    
    def _split_text(self, text: str) -> List[str]:
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size].strip())
        return chunks
    
    async def index_documents(self, sources: List[str]) -> int:
        total_chunks = 0
        for source in sources:
            content = await self._fetch_content(content)
            chunks = self._split_text(content)
            for i, chunk in enumerate(chunks):
                await self.memory.add(MemoryContent(
                    content=chunk,
                    mime_type=MemoryMimeType.TEXT,
                    metadata={"source": source, "chunk_index": i}
                ))
            total_chunks += len(chunks)
        return total_chunks

# 使用RAG
rag_memory = ChromaDBVectorMemory(
    config=PersistentChromaDBVectorMemoryConfig(
        collection_name="knowledge_base",
        persistence_path="./rag_db",
        k=3,
        score_threshold=0.4
    )
)

# 索引文档
indexer = SimpleDocumentIndexer(memory=rag_memory)
await indexer.index_documents([
    "https://example.com/docs/intro.html",
    "./local_docs/guide.md"
])

# 创建RAG Agent
rag_agent = AssistantAgent(
    name="rag_assistant",
    model_client=model_client,
    memory=[rag_memory]
)
```

### 8.8 记忆存储选型

| 存储类型 | 适用场景 | 特点 |
|---------|---------|------|
| `ListMemory` | 简单场景、调试 | 按时间顺序，无语义检索 |
| `ChromaDBVectorMemory` | 语义检索 | 本地部署，支持相似度搜索 |
| `RedisMemory` | 生产环境 | 高性能，支持分布式 |
| `Mem0Memory` | 外部记忆服务 | 云端/本地，高级分析 |

---

## 9. 会话管理与隔离

### 9.1 Agent 身份与生命周期

每个 Agent 实例由 **Agent ID** 唯一标识：

```
Agent ID = (Agent Type, Agent Key)
           ─────────    ────────
           注册时定义    运行时生成
```

```python
# Agent Type: 注册时定义的类型
# Agent Key: 运行时生成的实例标识

# 例如: ("code_reviewer", "review_001")
#       ("code_reviewer", "review_002")  # 不同会话实例
```

**生命周期**: 当消息送达时，Runtime 自动创建或获取 Agent 实例。

### 9.2 状态保存与加载

#### Agent 状态

```python
from autogen_agentchat.agents import AssistantAgent

agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    system_message="你是一个帮助助手"
)

# 运行一次对话
response = await agent.on_messages(
    [TextMessage(content="写一首关于湖的诗", source="user")],
    CancellationToken()
)

# 保存状态
agent_state = await agent.save_state()
print(agent_state)
# {
#   'type': 'AssistantAgentState',
#   'version': '1.0.0',
#   'llm_messages': [
#     {'content': '写一首关于湖的诗', 'source': 'user', 'type': 'UserMessage'},
#     {'content': '...', 'source': 'assistant', 'type': 'AssistantMessage'}
#   ]
# }

# 创建新Agent并加载状态
new_agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    system_message="你是一个帮助助手"
)
await new_agent.load_state(agent_state)

# 新Agent能记住之前的对话
response = await new_agent.on_messages(
    [TextMessage(content="你刚才写的诗最后一句是什么?", source="user")],
    CancellationToken()
)
# 回复: "最后一句是: Nature's mirror, where dreams and serenity lie."
```

#### Team 状态

```python
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination

team = RoundRobinGroupChat(
    agents=[agent1, agent2],
    termination_condition=MaxMessageTermination(max_messages=5)
)

# 运行团队任务
stream = team.run_stream(task="写一篇关于AI的文章")
await Console(stream)

# 保存团队状态 (包含所有Agent)
team_state = await team.save_state()
# {
#   'type': 'TeamState',
#   'agent_states': {
#     'agent1/uuid': {...},
#     'agent2/uuid': {...},
#     'manager/uuid': {...}
#   }
# }

# 创建新团队并加载状态
new_team = RoundRobinGroupChat(
    agents=[new_agent1, new_agent2],
    termination_condition=MaxMessageTermination(max_messages=5)
)
await new_team.load_state(team_state)
```

### 9.3 状态持久化 (文件/数据库)

```python
import json

# 保存到文件
with open("session_state.json", "w") as f:
    json.dump(team_state, f)

# 从文件加载
with open("session_state.json", "r") as f:
    team_state = json.load(f)

# 加载到新团队
await new_team.load_state(team_state)
```

### 9.4 多租户会话隔离方案

```python
import json
from pathlib import Path
from datetime import datetime

class SessionManager:
    """会话管理器 - 实现多租户隔离"""
    
    def __init__(self, storage_dir="./sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def _get_session_path(self, user_id: str, session_id: str) -> Path:
        return self.storage_dir / f"{user_id}_{session_id}.json"
    
    async def save_session(self, user_id: str, session_id: str, team_state: dict):
        """保存会话状态"""
        path = self._get_session_path(user_id, session_id)
        with open(path, "w") as f:
            json.dump({
                "user_id": user_id,
                "session_id": session_id,
                "updated_at": datetime.now().isoformat(),
                "state": team_state
            }, f, ensure_ascii=False, indent=2)
    
    async def load_session(self, user_id: str, session_id: str) -> dict:
        """加载会话状态"""
        path = self._get_session_path(user_id, session_id)
        if not path.exists():
            return None
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("state")
    
    async def list_sessions(self, user_id: str) -> list:
        """列出用户的所有会话"""
        pattern = f"{user_id}_*.json"
        sessions = []
        for path in self.storage_dir.glob(pattern):
            with open(path, "r") as f:
                data = json.load(f)
                sessions.append({
                    "session_id": data["session_id"],
                    "updated_at": data["updated_at"]
                })
        return sessions
    
    async def delete_session(self, user_id: str, session_id: str):
        """删除会话"""
        path = self._get_session_path(user_id, session_id)
        if path.exists():
            path.unlink()

# 使用示例
session_mgr = SessionManager("./user_sessions")

# 保存不同用户的会话 (完全隔离)
await session_mgr.save_session("user_a", "session_1", team_state_a)
await session_mgr.save_session("user_b", "session_1", team_state_b)

# 加载特定用户的会话
state = await session_mgr.load_session("user_a", "session_1")
if state:
    await team.load_session("user_a", "session_1")
```

### 9.5 运行时隔离

```python
from autogen_core import SingleThreadedAgentRuntime

# 方式1: 同一Runtime，不同Agent Key (会话级隔离)
runtime = SingleThreadedAgentRuntime()
# ("reviewer", "session_001") 和 ("reviewer", "session_002") 状态隔离

# 方式2: 不同Runtime (完全隔离)
runtime_a = SingleThreadedAgentRuntime()
runtime_b = SingleThreadedAgentRuntime()  # 完全独立
```

### 9.6 会话隔离架构总结

```
用户请求
    │
    ├──► Session A (user_1, session_1)
    │    ┌─────────────────────────┐
    │    │ Agent State: {...}      │
    │    │ Message History: [...]  │
    │    │ Model Context: [...]    │
    │    └─────────────────────────┘
    │
    └──► Session B (user_2, session_1)
         ┌─────────────────────────┐
         │ Agent State: {...}      │
         │ Message History: [...]  │
         │ Model Context: [...]    │
         └─────────────────────────┘
```

**关键设计点**:
- Agent Key 驱动隔离: 相同Type不同Key = 不同实例
- 状态可序列化: `save_state()`/`load_state()` 支持持久化
- 无状态端点友好: 每次请求可从存储加载状态
- Team 级状态: 团队状态包含所有成员状态

---

## 10. 多Agent协作模式

### 9.1 Selector Group Chat (推荐)

```python
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination

# 创建Agent
writer = AssistantAgent(name="Writer", ...)
editor = AssistantAgent(name="Editor", ...)
researcher = AssistantAgent(name="Researcher", ...)

# 终止条件
termination = TextMentionTermination("APPROVED")

# 创建团队
team = SelectorGroupChat(
    [writer, editor, researcher],
    model_client=model_client,
    termination_condition=termination,
    selector_prompt="根据任务选择最合适的Agent: {roles}"
)

# 运行
result = await team.run(task="写一篇关于AI的文章")
```

### 10.2 Swarm (工具驱动)

```python
from autogen_agentchat.teams import Swarm

team = Swarm(
    agents=[triage_agent, sales_agent, support_agent],
    termination_condition=termination
)
```

### 10.3 顺序工作流

```python
from autogen_agentchat.teams import RoundRobinGroupChat

team = RoundRobinGroupChat(
    agents=[researcher, writer, reviewer],
    termination_condition=termination
)
```

### 10.4 Human-in-the-Loop

```python
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console

# 终止条件: 等待用户输入APPROVE
termination = TextMentionTermination("APPROVE")

team = SelectorGroupChat(
    agents=[agent1, agent2],
    termination_condition=termination,
    allow_repeated_speaker=True
)

# 流式输出，人类可在控制台干预
stream = team.run_stream(task="...")
await Console(stream)
```

---

## 11. 性能优化

### 11.1 流式输出

```python
# AgentChat 流式输出
async for message in agent.run_stream(task="..."):
    print(message)
```

### 11.2 并发执行

```python
import asyncio

# 并发执行多个Agent任务
results = await asyncio.gather(
    agent1.run(task="任务1"),
    agent2.run(task="任务2"),
    agent3.run(task="任务3")
)
```

### 11.3 Token 使用监控

```python
import logging
from autogen_core import EVENT_LOGGER_NAME

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(EVENT_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
```

---

## 12. 生产部署

### 12.1 分布式运行时

```python
from autogen_core import GrpcRuntime

# 使用 gRPC 运行时部署分布式Agent
runtime = GrpcRuntime(...)
```

### 12.2 配置管理

```python
# 使用环境变量管理API Key
import os
os.environ["OPENAI_API_KEY"] = "sk-xxx"

# 不要硬编码密钥！
```

### 12.3 错误处理

```python
try:
    result = await agent.run(task="...")
except Exception as e:
    logger.error(f"Agent执行失败: {e}")
    # 实施降级策略
```

---

## 13. 常见问题与解决方案

### Q1: Agent 不调用工具？

**原因**: 工具描述不清晰或模型不支持

**解决**:
```python
# 确保工具描述明确
tool = FunctionTool(
    my_func,
    description="明确描述工具的功能和使用场景"
)

# 强制使用工具
completion = await model_client.create(
    messages=messages,
    tools=[tool],
    extra_create_args={"tool_choice": "required"}  # 强制调用
)
```

### Q2: Group Chat 循环不停？

**原因**: 缺少终止条件

**解决**:
```python
from autogen_agentchat.conditions import (
    TextMentionTermination,
    MaxMessageTermination,
    FunctionCallTermination
)

# 组合多个终止条件
termination = (
    TextMentionTermination("DONE") |
    MaxMessageTermination(max_messages=20)
)
```

### Q3: 如何切换不同模型？

**解决**:
```python
# 为不同Agent指定不同模型
writer = AssistantAgent(
    name="Writer",
    model_client=OpenAIChatCompletionClient(model="gpt-4o")
)

reviewer = AssistantAgent(
    name="Reviewer",
    model_client=AnthropicChatCompletionClient(model="claude-3-5-sonnet")
)
```

### Q4: 中文支持问题？

**解决**:
```python
# 在System Message中明确指定语言
system_message = """
你是一个中文AI助手。请始终使用中文回复。
回答要简洁、准确、专业。
"""
```

---

## 附录: 快速参考

### 安装

```bash
pip install -U "autogen-agentchat" "autogen-ext[openai]"

# 带 MCP 支持
pip install -U "autogen-agentchat" "autogen-ext[openai,mcp]"
```

### 最小示例

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")
    
    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        system_message="你是一个专业的Python开发者。"
    )
    
    result = await agent.run(task="解释Python装饰器")
    print(result.messages[-1].content)
    
    await model_client.close()

asyncio.run(main())
```

### 官方资源

- GitHub: https://github.com/microsoft/autogen
- 文档: https://microsoft.github.io/autogen/
- Discord: https://aka.ms/autogen-discord

---

## 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-04-01 | v1.0 | 初始版本，基于v0.4+文档 |
| 2026-04-01 | v1.1 | 新增记忆管理详细章节、会话管理与隔离章节 |

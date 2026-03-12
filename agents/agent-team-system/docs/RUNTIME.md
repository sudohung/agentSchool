# Agent Team System - 运行时说明

> 基于 Ralph Loop 哲学的 AI Agent 团队协作系统运行时实现

---

## 🏗️ 运行时架构

```
┌─────────────────────────────────────────────────────────┐
│                  Agent Team Runtime                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Team Runner                         │   │
│  │  - 协调多 Agent 执行                               │   │
│  │  - 注入依赖 (Document Hub, Request Board)        │   │
│  │  - 控制 Ralph Loop 迭代                            │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │         Agent Instances (12 种角色)               │   │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       │   │
│  │  │  PM │ │ Arch│ │ TL  │ │ Dev │ │ QA  │  ...  │   │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘       │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │        Ralph Loop 执行引擎                        │   │
│  │                                                   │   │
│  │  R - Read Documents (阅读文档)                    │   │
│  │  ↓                                                │   │
│  │  A - Act on Requests (响应诉求)                   │   │
│  │  ↓                                                │   │
│  │  L - Leverage Expertise (调用 AI)                 │   │
│  │  ↓                                                │   │
│  │  P - Produce Document (产出文档)                  │   │
│  │  ↓                                                │   │
│  │  H - Help Requests (发布诉求)                     │   │
│  │  ↓                                                │   │
│  │  Check Completion (检查完成度)                    │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │         外部服务集成                              │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  OpenCode SDK (HTTP Client)                     │   │
│  │  - Session API: 会话管理                         │   │
│  │  - Message API: AI 对话                           │   │
│  │  - File API: 文件读写                            │   │
│  │  - Event API: SSE 事件流                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 基本使用

```python
import asyncio
from agent.roles import ProductManagerAgent, SystemArchitectAgent
from agent.opencode_integration import TeamRunner, OpenCodeIntegration

async def main():
    # 1. 创建 Agent
    agents = [
        ProductManagerAgent(),
        SystemArchitectAgent(),
    ]
    
    # 2. 创建团队运行器
    opencode = OpenCodeIntegration(base_url="http://localhost:4096")
    runner = TeamRunner(agents, opencode)
    
    # 3. 初始化
    await runner.initialize()
    
    # 4. 运行团队
    await runner.run(max_iterations=10)
    
    # 5. 关闭
    await runner.close()

asyncio.run(main())
```

### 2. 自定义 Agent 团队

```python
from agent.roles import (
    ProductManagerAgent,
    SystemArchitectAgent,
    TechLeadAgent,
    BackendDeveloperAgent,
    QAAgent,
)

# 根据项目需求选择 Agent
agents = [
    ProductManagerAgent(),  # 需求分析
    SystemArchitectAgent(), # 架构设计
    TechLeadAgent(),        # 技术方案
    BackendDeveloperAgent(),# 后端开发
    QAAgent(),              # 测试
]
```

### 3. 直接使用 Agent

```python
from agent.roles import ProductManagerAgent

async def use_agent():
    agent = ProductManagerAgent()
    
    # 手动注入依赖
    agent.document_hub = DocumentStore()
    agent.request_board = RequestBoard()
    agent.client = OpenCodeClient()
    
    # 执行 Ralph Loop
    result = await agent.execute_ralph_loop()
    
    print(f"产出文档：{result['document_produced']}")
```

---

## 📋 核心组件

### Team Runner (团队运行器)

**功能**:
- ✅ 协调多 Agent 并行执行
- ✅ 自动注入依赖
- ✅ 控制 Ralph Loop 迭代
- ✅ 完成度检查
- ✅ 生成最终报告

**API**:
```python
class TeamRunner:
    def __init__(self, agents: List[Agent], opencode: OpenCodeIntegration)
    async def initialize(self)  # 初始化
    async def run(self, max_iterations: int = 50)  # 运行
    async def close(self)  # 关闭
```

### OpenCode Integration (OpenCode 集成)

**功能**:
- ✅ 连接 OpenCode Server
- ✅ 创建和管理会话
- ✅ 发送消息获取 AI 响应
- ✅ 文件读写
- ✅ 断开连接

**API**:
```python
class OpenCodeIntegration:
    def __init__(self, base_url: str = "http://localhost:4096")
    async def connect(self) -> bool
    async def create_session(title: str) -> Session
    async def send_message(agent_role: str, text: str) -> Any
    async def read_file(path: str) -> str
    async def write_file(path: str, content: str) -> bool
    async def disconnect(self)
```

### Agent Base (Agent 基类)

**Ralph Loop 核心能力**:
```python
class Agent(ABC):
    @abstractmethod
    async def read_documents(self) -> List[Document]  # R - 阅读
    
    @abstractmethod
    async def act_on_requests(self) -> List[Request]  # A - 响应
    
    @abstractmethod
    async def leverage_expertise(self) -> Any  # L - 发挥能力
    
    @abstractmethod
    async def produce_document(self, work_result: Any) -> Document  # P - 产出
    
    @abstractmethod
    async def help_requests(self) -> List[Request]  # H - 发布诉求
```

---

## 🔄 Ralph Loop 执行流程

```
Iteration 1:
┌────────────────────────────────────────┐
│  PM: R → A → L → P → H                 │
│  Arch: R → A → L → P → H               │
│  TL: R → A → L → P → H                 │
│  Dev: R → A → L → P → H                │
│  QA: R → A → L → P → H                 │
└────────────────────────────────────────┘
              ↓
┌────────────────────────────────────────┐
│  Check Completion                      │
│  - 文档数量 >= 10?                     │
│  - 需求覆盖率 >= 90%?                  │
│  - 质量分数 >= 0.7?                    │
└────────────────────────────────────────┘
              ↓
         Yes → 完成
         No → Iteration 2
```

---

## 📊 运行时状态

### Agent 状态

| 状态 | 描述 | 转换条件 |
|------|------|---------|
| `IDLE` | 空闲 | 初始状态 |
| `WORKING` | 工作中 | 有文档或诉求 |
| `WAITING` | 等待 | 需要协作 |
| `BLOCKED` | 阻塞 | 遇到问题 |
| `DONE` | 完成 | 任务完成 |

### Ralph Loop 状态

| 状态 | 描述 |
|------|------|
| `IDLE` | 未启动 |
| `RUNNING` | 运行中 |
| `PAUSED` | 已暂停 |
| `STOPPED` | 已停止 |
| `COMPLETED` | 已完成 |
| `FAILED` | 失败 |

---

## 🔧 配置

### Team Runner 配置

```python
runner = TeamRunner(
    agents=agents,
    opencode=OpenCodeIntegration(
        base_url="http://localhost:4096",
    ),
)

# 运行配置
await runner.run(
    max_iterations=50,  # 最大迭代次数
)
```

### Agent 配置

```python
agent = ProductManagerAgent(
    session=session,
    client=client,
    config=AgentConfig(
        role="Product Manager",
        expertise=["需求分析", "产品规划"],
        temperature=0.7,
        max_iterations=50,
    ),
)
```

---

## 📝 使用场景

### 场景 1: 需求驱动开发

```python
agents = [
    ProductManagerAgent(),  # 分析需求
    SystemArchitectAgent(), # 设计架构
    BackendDeveloperAgent(),# 实现功能
    QAAgent(),              # 测试验证
]
```

### 场景 2: 代码审查

```python
agents = [
    CodeReviewerAgent(),    # 审查代码
    BackendDeveloperAgent(),# 修复问题
]
```

### 场景 3: 文档生成

```python
agents = [
    DocWriterAgent(),       # 编写文档
    TechLeadAgent(),        # 提供技术信息
]
```

---

## ⚠️ 限制和已知问题

1. **需要 OpenCode Server**
   - 必须运行 OpenCode Server (默认端口 4096)
   - 需要配置正确的 base_url

2. **依赖注入**
   - 目前需要手动注入依赖
   - 未来会实现自动依赖注入

3. **持久化**
   - 文档存储是临时的
   - 未来会添加数据库支持

4. **监控**
   - 缺少详细的执行日志
   - 未来会添加监控系统

---

## 🚀 未来计划

- [ ] 自动依赖注入
- [ ] 持久化存储 (数据库)
- [ ] 监控和日志系统
- [ ] Web UI 界面
- [ ] Agent 热重载
- [ ] 更多 Agent 角色

---

## 📖 相关文档

- [设计文档](./docs/AGENT_FRAMEWORK_DESIGN.md)
- [TODO 清单](./docs/TODO.md)
- [测试报告](./tests/)

---

> 最后更新：2026-03-11
> 版本：0.1.0
> 状态：Phase 1 完成 ✅

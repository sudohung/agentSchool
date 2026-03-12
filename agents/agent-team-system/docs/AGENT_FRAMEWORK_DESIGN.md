# Agent 基础框架设计文档

> Agent Team System 核心组件设计
> 
> 版本：0.1.0
> 创建日期：2026-03-11
> 最后更新：2026-03-11

---

## 1. 概述

### 1.1 设计目标

构建一个**自主驱动的 Agent 基础框架**，支持：

- ✅ 动态创建专业 Agent 角色
- ✅ Ralph Loop 迭代工作能力
- ✅ 文档驱动的协作机制
- ✅ 诉求驱动的跨 Agent 协作
- ✅ Permission/Question 自动处理
- ✅ 与 OpenCode SDK 无缝集成

### 1.2 核心原则

| 原则 | 描述 |
|------|------|
| 🏢 **公司化运作** | Agent 间是平等同事关系 |
| 📄 **文档交付** | 工作成果 = 文档 |
| 💬 **诉求驱动** | 通过诉求触发协作 |
| 🔄 **Ralph Loop** | 持续迭代，挫折中前进 |
| 🙈 **用户无感知** | 内部循环用户看不到 |
| 🔐 **权限管控** | 自动处理权限/问题请求 |

### 1.3 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Agent 基础框架                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Agent Base  │  │Agent Roles  │  │Agent State  │     │
│  │   基类      │  │   角色库    │  │   状态机    │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│         └────────────────┼────────────────┘             │
│                          │                              │
│  ┌───────────────────────┼───────────────────────┐     │
│  │              Agent Core Abilities              │     │
│  │              (核心能力层)                       │     │
│  ├───────────────────────────────────────────────┤     │
│  │  📖 Read  │  ✍️ Write  │  💬 Request  │  👀 Review │  │
│  │  阅读文档  │  编写文档  │  发布诉求   │  审查文档  │  │
│  └───────────────────────────────────────────────┘     │
│                          │                              │
│  ┌───────────────────────┼───────────────────────┐     │
│  │         Permission/Question Handler            │     │
│  │         (权限/问题处理器)                       │     │
│  ├───────────────────────────────────────────────┤     │
│  │   缓存检查  │  自动规则  │  团队决策  │  用户   │     │
│  └───────────────────────────────────────────────┘     │
│                          │                              │
│  ┌───────────────────────┼───────────────────────┐     │
│  │              OpenCode SDK Integration          │     │
│  │              (SDK 集成层)                        │     │
│  ├───────────────────────────────────────────────┤     │
│  │   Session  │  Message  │  File  │  Event     │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Agent 基类设计

### 2.1 核心属性

```python
class Agent:
    """Agent 基类"""
    
    # 身份标识
    role: str                      # 角色名称
    expertise: List[str]           # 专业技能列表
    id: str                        # 唯一标识
    
    # 状态管理
    status: AgentStatus            # 当前状态
    state_machine: AgentStateMachine  # 状态机
    
    # 工作上下文
    session: Session               # 团队会话
    client: OpenCodeClient         # OpenCode 客户端
    coordinator: CoordinatorAgent  # 协调员引用
    
    # 记忆系统
    short_term_memory: Dict        # 短期记忆 (当前任务)
    long_term_memory: Dict         # 长期记忆 (历史经验)
    
    # 配置
    config: AgentConfig            # Agent 配置
```

### 2.2 Ralph Loop 核心能力

```python
class Agent(ABC):
    """Agent 基类 - Ralph Loop 能力"""
    
    @abstractmethod
    async def read_documents(self) -> List[Document]:
        """
        R - Read: 阅读共享文档中心的最新文档
        
        返回：相关文档列表
        """
        pass
    
    @abstractmethod
    async def act_on_requests(self) -> List[Request]:
        """
        A - Act: 响应其他 Agent 的诉求
        
        返回：已处理的诉求列表
        """
        pass
    
    @abstractmethod
    async def leverage_expertise(self) -> Any:
        """
        L - Leverage: 发挥专业能力执行工作
        
        返回：工作结果
        """
        pass
    
    @abstractmethod
    async def produce_document(self, work_result: Any) -> Document:
        """
        P - Produce: 产出文档作为工作成果
        
        返回：新文档
        """
        pass
    
    @abstractmethod
    async def help_requests(self) -> List[Request]:
        """
        H - Help: 发布诉求寻求其他 Agent 协作
        
        返回：新诉求列表
        """
        pass
```

### 2.3 权限/问题处理能力

```python
class Agent(ABC):
    """Agent 基类 - 权限/问题处理能力"""
    
    async def request_permission(
        self,
        type: PermissionType,
        resource: str,
        description: str,
        remember: bool = False,
    ) -> PermissionAction:
        """
        请求权限
        
        流程：
        1. 检查缓存 (remember 的选择)
        2. 检查自动规则
        3. 团队内部决策
        4. 批量询问用户
        
        返回：PermissionAction (ALLOW/DENY/ASK)
        """
        pass
    
    async def ask_question(
        self,
        question: str,
        header: str,
        options: List[QuestionOption],
        multiple: bool = False,
        custom: bool = True,
    ) -> QuestionResponse:
        """
        提出问题
        
        流程：
        1. 检查是否可以自动回答
        2. 团队内部讨论
        3. 批量询问用户
        
        返回：QuestionResponse
        """
        pass
    
    # ========== 便捷方法 ==========
    
    async def can_read_file(self, path: str) -> bool:
        """检查是否可以读取文件"""
        pass
    
    async def can_write_file(self, path: str) -> bool:
        """检查是否可以写入文件"""
        pass
    
    async def can_execute_command(self, command: str) -> bool:
        """检查是否可以执行命令"""
        pass
```

### 2.4 工具方法

```python
class Agent(ABC):
    """Agent 基类 - 工具方法"""
    
    async def send_message(self, text: str) -> Any:
        """通过 OpenCode SDK 发送消息获取 AI 响应"""
        result = await self.client.message.send_text(
            session_id=self.session.id,
            text=text,
            agent=self.role,
        )
        return result
    
    def update_status(self, status: AgentStatus):
        """更新 Agent 状态"""
        self.status = status
        self.state_machine.transition_to(status)
    
    def add_to_memory(self, key: str, value: Any, scope: str = "short"):
        """添加到记忆"""
        if scope == "short":
            self.short_term_memory[key] = value
        else:
            self.long_term_memory[key] = value
    
    def get_from_memory(self, key: str, scope: str = "short") -> Optional[Any]:
        """从记忆获取"""
        if scope == "short":
            return self.short_term_memory.get(key)
        return self.long_term_memory.get(key)
    
    async def notify_coordinator(self, event: str, data: Any):
        """通知协调员"""
        if self.coordinator:
            await self.coordinator.handle_event(event, data)
```

---

## 3. Agent 角色库

### 3.1 角色分类

```
Agent 角色库
├── 核心角色
│   ├── Product Manager (产品经理)
│   ├── System Architect (系统架构师)
│   └── Tech Lead (技术负责人)
├── 开发角色
│   ├── Frontend Developer (前端开发)
│   ├── Backend Developer (后端开发)
│   └── Full Stack Developer (全栈开发)
├── 质量角色
│   ├── QA Engineer (测试工程师)
│   └── Code Reviewer (代码审查员)
├── 支持角色
│   ├── Doc Writer (文档工程师)
│   ├── DevOps Engineer (运维工程师)
│   └── Security Engineer (安全工程师)
└── 协调角色
    └── Coordinator (协调员)
```

### 3.2 角色定义模板

```python
class AgentRole:
    """Agent 角色定义模板"""
    
    role_name: str           # 角色名称
    description: str         # 角色描述
    expertise: List[str]     # 专业技能
    responsibilities: List[str]  # 职责列表
    outputs: List[str]       # 产出文档类型
    collaborations: List[str]    # 协作对象
    permissions: List[PermissionType]  # 需要的权限
```

### 3.3 核心角色示例

```python
# Product Manager Agent
class ProductManagerAgent(Agent):
    """
    产品经理 Agent
    
    职责：需求分析、产品规划、优先级排序
    产出：PRD.md、用户故事、需求列表
    协作：所有角色
    """
    
    def __init__(self, session, client):
        super().__init__(
            role="Product Manager",
            expertise=["需求分析", "产品规划", "用户调研", "竞品分析"],
            session=session,
            client=client,
        )
    
    async def leverage_expertise(self):
        """执行需求分析工作"""
        # 实现需求分析逻辑
        pass
    
    async def produce_document(self, work_result: Any) -> Document:
        """产出 PRD 文档"""
        return Document(
            name="PRD.md",
            content=work_result,
            author=self.role,
            version=1,
            timestamp=0,
        )
    
    async def help_requests(self) -> List[Request]:
        """发布诉求：需要 Architect 评估技术可行性"""
        return [
            Request(
                id="req_001",
                from_agent=self.role,
                to_agent="System Architect",
                subject="请评估技术可行性",
                content="基于 PRD，请评估技术可行性和风险",
                priority="high",
                status="pending",
                timestamp=0,
            )
        ]


# System Architect Agent
class SystemArchitectAgent(Agent):
    """
    系统架构师 Agent
    
    职责：系统架构设计、技术选型
    产出：Architecture.md、技术栈文档
    """
    pass


# Coordinator Agent
class CoordinatorAgent(Agent):
    """
    协调员 Agent
    
    职责：
    - 收集所有 Permission/Question 请求
    - 判断是否需要用户介入
    - 批量向用户提问
    - 跟踪请求状态
    """
    
    def __init__(self, session, client):
        super().__init__(
            role="Coordinator",
            expertise=["团队协调", "冲突解决", "进度跟踪", "用户沟通"],
            session=session,
            client=client,
        )
        
        self.handler = PermissionQuestionHandler()
        self.request_log: List[Dict] = []
```

---

## 4. Agent 状态机

### 4.1 状态定义

```python
class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = "idle"              # 空闲
    WORKING = "working"        # 工作中
    WAITING = "waiting"        # 等待诉求/文档
    BLOCKED = "blocked"        # 被阻塞
    DONE = "done"              # 完成
```

### 4.2 状态转换

```
                    ┌─────────────────┐
                    │      IDLE       │
                    │     (空闲)      │
                    └────────┬────────┘
                             │ 有新文档或诉求
                             ▼
                    ┌─────────────────┐
                    │    WORKING      │
                    │     (工作中)    │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   WAITING    │ │   BLOCKED    │ │    DONE      │
    │   (等待)     │ │   (阻塞)     │ │   (完成)     │
    └──────┬───────┘ └──────┬───────┘ └──────────────┘
           │                │
           │ 诉求已响应      │ 问题已解决
           │                │
           └────────────────┴────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   WORKING    │
                    │   (继续工作)  │
                    └──────────────┘
```

### 4.3 状态机实现

```python
class AgentStateMachine:
    """Agent 状态机"""
    
    # 允许的状态转换
    transitions = [
        (IDLE, WORKING, "有新文档或诉求"),
        (WORKING, WAITING, "需要其他 Agent 协作"),
        (WAITING, WORKING, "诉求已响应"),
        (WORKING, BLOCKED, "遇到无法解决的问题"),
        (BLOCKED, WORKING, "问题已解决"),
        (WORKING, DONE, "任务完成"),
        (DONE, IDLE, "新任务到达"),
    ]
    
    def can_transition_to(self, target_state: AgentStatus) -> bool:
        """检查是否可以转换到目标状态"""
        pass
    
    def transition_to(self, target_state: AgentStatus, reason: str) -> bool:
        """执行状态转换"""
        pass
```

---

## 5. Permission/Question 处理机制

### 5.1 三层响应机制

```
┌─────────────────────────────────────────────────────────┐
│           Permission/Question 处理流程                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Agent 请求权限/提问                                     │
│       │                                                 │
│       ▼                                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Layer 1: 缓存检查                                │   │
│  │ - 检查 remember 的历史选择                        │   │
│  │ - 有缓存 → 直接返回                              │   │
│  └─────────────────────────────────────────────────┘   │
│       │ 无缓存                                         │
│       ▼                                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Layer 2: 自动规则                                │   │
│  │ - 匹配 auto_allow_patterns                       │   │
│  │ - 低风险操作自动允许                              │   │
│  └─────────────────────────────────────────────────┘   │
│       │ 不匹配                                         │
│       ▼                                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Layer 3: 团队内部决策                            │   │
│  │ - Coordinator 组织快速讨论                        │   │
│  │ - 有共识 → 返回决策                              │   │
│  └─────────────────────────────────────────────────┘   │
│       │ 无共识                                         │
│       ▼                                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Layer 4: 批量询问用户                            │   │
│  │ - 累积到一定数量                                 │   │
│  │ - 一次性发送给用户                               │   │
│  │ - 用户回答 → 更新缓存 → 返回 Agent               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.2 权限类型

```python
class PermissionType(Enum):
    """权限类型"""
    FILE_READ = "file_read"           # 读取文件
    FILE_WRITE = "file_write"         # 写入文件
    FILE_DELETE = "file_delete"       # 删除文件
    COMMAND_EXECUTE = "command_execute"  # 执行命令
    API_CALL = "api_call"             # API 调用
    EXTERNAL_ACCESS = "external_access"  # 外部访问
```

### 5.3 自动允许规则

```python
DEFAULT_AUTO_ALLOW_PATTERNS = [
    r"^read:.*\.md$",           # 允许读取 markdown 文件
    r"^read:.*\.txt$",          # 允许读取文本文件
    r"^read:.*\.json$",         # 允许读取 JSON 文件
    r"^read:.*\.py$",           # 允许读取 Python 文件
    r"^write:.*\.md$",          # 允许写入 markdown 文件
]
```

### 5.4 Coordinator 批量处理

```python
class CoordinatorAgent(Agent):
    """协调员 - 批量处理权限/问题"""
    
    async def batch_ask_user(self) -> List[Dict]:
        """
        批量向用户提问
        
        触发条件：
        - 待处理请求数量 >= 阈值 (默认 5)
        - 距离上次询问 >= 时间间隔 (默认 10 分钟)
        - Ralph Loop 迭代结束
        """
        pending = self.handler.get_pending_requests()
        
        if not pending["permissions"] and not pending["questions"]:
            return []
        
        # 构建批量问题文档
        batch_doc = self._build_batch_document(pending)
        
        # 发送给用户
        await self.client.message.send_text(
            session_id=self.session.id,
            text=batch_doc,
        )
        
        return pending
```

---

## 6. 与 OpenCode SDK 集成

### 6.1 Session 管理

```python
class Agent(ABC):
    """Agent - Session 管理"""
    
    async def initialize_session(self, title: str) -> Session:
        """初始化团队会话"""
        session = await self.client.session.create(title=title)
        return session
    
    async def get_session_messages(self, limit: int = 100) -> List[Message]:
        """获取会话消息"""
        messages = await self.client.message.list(
            session_id=self.session.id,
            limit=limit,
        )
        return messages
```

### 6.2 文档读写

```python
class Agent(ABC):
    """Agent - 文档读写"""
    
    async def read_document_from_session(self, path: str) -> str:
        """从会话读取文档"""
        content = await self.client.file.read(path=path)
        return content.content
    
    async def write_document_to_session(
        self,
        path: str,
        content: str,
    ):
        """写入文档到会话"""
        # 通过 message 间接写入
        await self.client.message.send_text(
            session_id=self.session.id,
            text=f"Save this to {path}:\n\n{content}",
        )
```

### 6.3 诉求发布

```python
class Agent(ABC):
    """Agent - 诉求发布"""
    
    async def post_request_to_board(
        self,
        to_agent: str,
        subject: str,
        content: str,
        priority: str = "medium",
    ):
        """发布诉求到看板"""
        await self.client.message.send_text(
            session_id=self.session.id,
            text=f"[REQUEST] To: {to_agent}\nSubject: {subject}\nPriority: {priority}\n\n{content}",
        )
```

---

## 7. 目录结构

```
src/
├── agent/
│   ├── __init__.py
│   ├── base.py              # Agent 基类
│   ├── config.py            # Agent 配置
│   ├── state.py             # Agent 状态机
│   ├── memory.py            # Agent 记忆系统
│   ├── registry.py          # Agent 注册表
│   ├── handler.py           # Permission/Question Handler
│   ├── permissions.py       # 权限/问题模型
│   └── roles/               # Agent 角色定义
│       ├── __init__.py
│       ├── coordinator.py   # Coordinator Agent
│       ├── pm.py            # Product Manager
│       ├── architect.py     # System Architect
│       ├── frontend.py      # Frontend Developer
│       ├── backend.py       # Backend Developer
│       ├── qa.py            # QA Engineer
│       ├── doc.py           # Doc Writer
│       └── devops.py        # DevOps Engineer
├── document_hub/
│   ├── __init__.py
│   ├── store.py             # 文档存储
│   ├── version.py           # 版本控制
│   └── notification.py      # 通知系统
├── request_board/
│   ├── __init__.py
│   ├── request.py           # 诉求模型
│   ├── board.py             # 看板管理
│   └── router.py            # 诉求路由
└── ralph_loop/
    ├── __init__.py
    ├── engine.py            # Ralph Loop 引擎
    ├── setback.py           # 挫折处理
    └── completion.py        # 完成度检查
```

---

## 8. 实现计划

| 阶段 | 内容 | 文件 | 预计时间 | 优先级 |
|------|------|------|----------|--------|
| 1 | Agent 基类 | `base.py` | 2 小时 | 🔴 高 |
| 2 | Agent 配置 | `config.py` | 1 小时 | 🔴 高 |
| 3 | Agent 状态机 | `state.py` | 1 小时 | 🔴 高 |
| 4 | 权限/问题模型 | `permissions.py` | 1 小时 | 🔴 高 |
| 5 | Permission Handler | `handler.py` | 2 小时 | 🔴 高 |
| 6 | Agent 注册表 | `registry.py` | 1 小时 | 🟡 中 |
| 7 | Coordinator Agent | `roles/coordinator.py` | 3 小时 | 🔴 高 |
| 8 | 核心角色实现 | `roles/*.py` | 4 小时 | 🟡 中 |
| 9 | 文档中心集成 | `document_hub/` | 3 小时 | 🟡 中 |
| 10 | 诉求看板集成 | `request_board/` | 3 小时 | 🟡 中 |
| 11 | 记忆系统 | `memory.py` | 2 小时 | 🟢 低 |
| 12 | 单元测试 | `tests/agent/` | 4 小时 | 🟡 中 |
| **总计** | | | **27 小时** | |

---

## 9. 测试策略

### 9.1 单元测试

```python
# tests/agent/test_base.py

class TestAgentBase:
    """Agent 基类测试"""
    
    def test_agent_initialization(self):
        """测试 Agent 初始化"""
        pass
    
    def test_ralph_loop_abilities(self):
        """测试 Ralph Loop 核心能力"""
        pass
    
    def test_permission_request(self):
        """测试权限请求"""
        pass
    
    def test_question_ask(self):
        """测试问题提问"""
        pass


# tests/agent/test_handler.py

class TestPermissionHandler:
    """Permission Handler 测试"""
    
    def test_auto_allow(self):
        """测试自动允许规则"""
        pass
    
    def test_cache_lookup(self):
        """测试缓存查找"""
        pass
    
    def test_team_decision(self):
        """测试团队决策"""
        pass
    
    def test_batch_ask_user(self):
        """测试批量询问用户"""
        pass
```

### 9.2 集成测试

```python
# tests/integration/test_agent_team.py

class TestAgentTeam:
    """Agent 团队集成测试"""
    
    def test_team_creation(self):
        """测试团队创建"""
        pass
    
    def test_ralph_loop_execution(self):
        """测试 Ralph Loop 执行"""
        pass
    
    def test_permission_flow(self):
        """测试权限流程"""
        pass
    
    def test_document_collaboration(self):
        """测试文档协作"""
        pass
```

---

## 10. 关键决策点

### 10.1 Agent 通信方式

| 选项 | 描述 | 选择 |
|------|------|------|
| 共享会话 | 所有 Agent 在同一个会话中 | ✅ 选择 |
| 独立会话 | 每个 Agent 独立会话 | ❌ |
| 混合模式 | 核心会话 + 私有会话 | ❌ |

### 10.2 权限处理策略

| 策略 | 描述 | 选择 |
|------|------|------|
| 全部问用户 | 所有权限都问用户 | ❌ |
| 自动允许 | 默认允许所有 | ❌ |
| 三层响应 | 缓存→规则→团队→用户 | ✅ 选择 |

### 10.3 Coordinator 角色

| 设计 | 描述 | 选择 |
|------|------|------|
| 专门角色 | 专门的 Coordinator Agent | ✅ 选择 |
| 轮流担任 | Agent 轮流担任协调员 | ❌ |
| 外部管理 | 外部系统管理 | ❌ |

---

## 11. 风险和挑战

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Agent 间通信效率低 | 高 | 中 | 优化诉求路由机制 |
| 权限请求过多打扰用户 | 高 | 中 | 批量处理 + 自动规则 |
| Ralph Loop 陷入死循环 | 高 | 低 | 设置最大迭代次数 |
| 文档冲突 | 中 | 中 | 实现文档锁机制 |
| Coordinator 单点故障 | 中 | 低 | 支持多 Coordinator |

---

## 12. 成功标准

- [ ] Agent 基类支持完整的 Ralph Loop 能力
- [ ] 11 种 Agent 角色全部实现
- [ ] Permission/Question 处理机制正常工作
- [ ] Coordinator 能够有效批量处理用户请求
- [ ] 与 OpenCode SDK 无缝集成
- [ ] 单元测试覆盖率 >= 80%
- [ ] 集成测试全部通过

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Agent | AI 驱动的智能体，扮演特定角色 |
| Ralph Loop | AI 持续迭代的技术哲学 (Read-Act-Leverage-Produce-Help) |
| Coordinator | 协调员 Agent，负责团队协调和用户沟通 |
| Permission | 权限请求，如读写文件、执行命令 |
| Question | 问题请求，需要用户决策 |
| Document Hub | 共享文档存储和协作空间 |
| Request Board | Agent 间协作请求管理系统 |

### B. 参考资源

- [OpenCode Python SDK](../opencode-4-py/)
- [Ralph Wiggum - 辛普森一家](https://simpsons.fandom.com/wiki/Ralph_Wiggum)
- [Agent 协作框架研究](待添加)

---

> 最后更新：2026-03-11
> 状态：草稿
> 审核：待审核

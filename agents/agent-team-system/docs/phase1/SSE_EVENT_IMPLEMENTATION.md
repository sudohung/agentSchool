# SSE 事件流 + 决策 Agent 实现总结

**实现日期**: 2026-03-16  
**实现状态**: ✅ 完成  
**实现范围**: 责任链模式事件处理 + DecisionAgent

---

## 📊 实现概览

| 组件 | 文件 | 代码行数 | 状态 |
|------|------|---------|------|
| 责任链框架 | `src/event/chain.py` | 280 行 | ✅ |
| 问题处理器 | `src/event/handlers/question.py` | 120 行 | ✅ |
| 权限处理器 | `src/event/handlers/permission.py` | 230 行 | ✅ |
| 默认处理器 | `src/event/handlers/default.py` | 100 行 | ✅ |
| 事件管理器 | `src/event/manager.py` | 180 行 | ✅ |
| 决策 Agent | `src/agent/roles/decision.py` | 430 行 | ✅ |
| **总计** | - | **~1340 行** | ✅ |

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenCode Server                           │
│  ┌─────────────┐                                            │
│  │ SSE Stream  │                                            │
│  └──────┬──────┘                                            │
└─────────┼───────────────────────────────────────────────────┘
          │ subscribe
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    SSEEventManager                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              EventHandlerChain (责任链)               │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │ Question    │→│ Permission  │→│ Default     │   │   │
│  │  │ Handler     │ │ Handler     │ │ Handler     │   │   │
│  │  └──────┬──────┘ └──────┬──────┘ └─────────────┘   │   │
│  └─────────┼───────────────┼───────────────────────────┘   │
└────────────┼───────────────┼───────────────────────────────┘
             │               │
             ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    DecisionAgent                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ analyze_question │    │analyze_permission│                │
│  └────────┬────────┘    └────────┬────────┘                │
│           │                      │                          │
│           ▼                      ▼                          │
│  ┌─────────────────────────────────────────────────┐       │
│  │              LLM Decision Making                 │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    OpenCode SDK                              │
│  question.answer() / permission.respond()                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 核心组件说明

### 1. 责任链框架 (`chain.py`)

```python
class EventHandler(ABC):
    """事件处理器基类"""
    
    def can_handle(self, event_type: SSEEventType) -> bool
    async def handle(self, event: SSEEvent, context: EventContext) -> EventResult
    def set_next(self, handler: EventHandler) -> EventHandler

class EventHandlerChain:
    """事件处理器链"""
    
    def add_handler(self, handler: EventHandler) -> EventHandlerChain
    async def process(self, event: SSEEvent) -> EventResult
```

### 2. 事件处理器

#### QuestionAskHandler
```python
class QuestionAskHandler(EventHandler):
    """问题询问事件处理器"""
    
    # 流程：
    # 1. 解析 question_asked 事件
    # 2. 调用 DecisionAgent.analyze_question()
    # 3. 通过 SDK 回答问题
```

#### PermissionAskHandler
```python
class PermissionAskHandler(EventHandler):
    """权限请求事件处理器"""
    
    # 自动规则：
    # - AUTO_ALLOW_PATTERNS: 安全操作自动允许
    # - AUTO_DENY_PATTERNS: 危险操作自动拒绝
    
    # 流程：
    # 1. 检查自动规则
    # 2. 如需决策，调用 DecisionAgent.analyze_permission()
    # 3. 通过 SDK 响应权限
```

#### DefaultHandler
```python
class DefaultHandler(EventHandler):
    """默认事件处理器 - 其他事件占位"""
    
    # 当前仅记录日志，为其他事件类型留空
```

### 3. DecisionAgent

```python
class DecisionAgent(Agent):
    """决策 Agent"""
    
    async def analyze_question(
        self, question, options, context
    ) -> str:
        """分析问题并生成回答"""
    
    async def analyze_permission(
        self, permission_type, resource, agent_role, context
    ) -> PermissionAnalysis:
        """分析权限请求并做出决策"""
    
    # 安全检查方法
    def _is_dangerous_operation(permission_type, resource) -> bool
    def _is_safe_operation(permission_type, resource) -> bool
```

### 4. SSEEventManager

```python
class SSEEventManager:
    """SSE 事件管理器"""
    
    async def start(self):
        """启动 SSE 事件监听"""
    
    async def stop(self):
        """停止 SSE 事件监听"""
    
    async def _sse_listener(self):
        """SSE 事件监听器"""
    
    async def _handle_raw_event(self, raw_event):
        """处理原始 SSE 事件"""
```

---

## 🔄 事件处理流程

### Question Asked 流程

```
1. Agent A 调用 SDK 需要用户输入
       ↓
2. OpenCode 产生 EventQuestionAsked
       ↓
3. SSE 推送到 SSEEventManager
       ↓
4. QuestionAskHandler.can_handle() = True
       ↓
5. QuestionAskHandler.handle()
   - 解析问题内容
   - 调用 DecisionAgent.analyze_question()
   - LLM 分析生成回答
   - SDK question.answer(answer)
       ↓
6. 事件处理完成 ✅
```

### Permission Asked 流程

```
1. Agent B 需要执行敏感操作
       ↓
2. OpenCode 产生 EventPermissionAsked
       ↓
3. SSE 推送到 SSEEventManager
       ↓
4. PermissionAskHandler.can_handle() = True
       ↓
5. PermissionAskHandler.handle()
   - 检查自动规则 (安全/危险模式)
   - 如需决策：
     - 调用 DecisionAgent.analyze_permission()
     - LLM 评估风险
   - SDK permission.respond(allow/deny)
       ↓
6. 事件处理完成 ✅
```

---

## 🎯 核心功能

### 1. 自动规则 (PermissionAskHandler)

```python
AUTO_ALLOW_PATTERNS = {
    ("file_read", "/src/"),    # 源代码读取
    ("file_read", "/docs/"),   # 文档读取
    ("command_execute", "git status"),  # 安全命令
}

AUTO_DENY_PATTERNS = {
    ("file_read", ".env"),     # 环境变量
    ("file_read", "credentials"),  # 凭证
    ("command_execute", "rm -rf /"),  # 危险命令
}
```

### 2. LLM 决策提示

#### 问题分析提示
```
You are the Decision Agent in an AI agent team.
Your role is to analyze questions and provide clear, actionable answers.

## Current Question
Question: {question}
Options: {options}

## Task
1. Analyze the question carefully
2. Consider the context and available information
3. Provide a clear, concise answer
```

#### 权限分析提示
```
You are the Decision Agent in an AI agent team.
Your role is to analyze permission requests and make security decisions.

## Permission Request
Type: {permission_type}
Resource: {resource}

## Response Format
DECISION: [ALLOW/DENY]
RISK_LEVEL: [low/medium/high]
CONFIDENCE: [0.0-1.0]
REASON: [Brief explanation]
```

---

## 📈 统计功能

```python
# SSEEventManager 统计
{
    "events_received": 10,
    "events_processed": 8,
    "questions_answered": 5,
    "permissions_handled": 3,
    "chain_stats": {
        "handlers_count": 3,
        "event_stats": {...}
    }
}

# DecisionAgent 决策历史
decision_agent.get_decision_history(decision_type="permission", limit=20)
```

---

## ✅ 验证结果

```
=== 测试导入 ===
✅ event 模块导入成功
✅ handlers 模块导入成功
✅ DecisionAgent 导入成功

=== 测试类实例化 ===
✅ 责任链创建成功: 3 个处理器

=== 统计 ===
事件类型数: 9
处理器数: 3
```

---

## 📂 文件结构

```
src/
├── event/
│   ├── __init__.py          # 模块入口
│   ├── chain.py             # 责任链框架
│   ├── manager.py           # SSE 事件管理器
│   └── handlers/
│       ├── __init__.py
│       ├── question.py      # 问题处理器
│       ├── permission.py    # 权限处理器
│       └── default.py       # 默认处理器
│
└── agent/
    └── roles/
        └── decision.py      # 决策 Agent
```

---

## 🎯 使用示例

```python
from event import SSEEventManager, create_sse_event_manager
from agent.roles.decision import DecisionAgent

# 1. 创建决策 Agent
decision_agent = DecisionAgent(
    session=session,
    client=opencode_client,
)

# 2. 创建 SSE 事件管理器
manager = await create_sse_event_manager(
    opencode_client=opencode_client,
    session_id=session.id,
    decision_agent=decision_agent,
)

# 3. 事件自动处理
# - question_asked -> DecisionAgent.analyze_question() -> SDK 回答
# - permission_asked -> DecisionAgent.analyze_permission() -> SDK 响应

# 4. 获取统计
stats = manager.get_statistics()
```

---

## 📝 TODO 更新

- [x] **事件流 (SSE)** ✅ 已完成
  - ✅ 责任链模式事件处理
  - ✅ QuestionAskHandler 实现
  - ✅ PermissionAskHandler 实现
  - ✅ DefaultHandler 占位
  - ✅ DecisionAgent 实现
  - ✅ SSEEventManager 整合

---

**实现人员**: Development Agent  
**审核状态**: ✅ 通过  
**版本**: v1.0  
**日期**: 2026-03-16
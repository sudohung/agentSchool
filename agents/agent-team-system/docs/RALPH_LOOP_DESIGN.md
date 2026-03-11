# Ralph Loop 引擎设计文档

> Agent Team System 核心组件设计
> 
> 版本：0.1.0
> 创建日期：2026-03-11
> 最后更新：2026-03-11

---

## 1. 概述

### 1.1 设计目标

构建一个**Ralph Loop 迭代引擎**，作为 Agent 团队持续工作的核心机制：

- ✅ 实现 Read-Act-Leverage-Produce-Help 循环
- ✅ 挫折检测和恢复机制
- ✅ 完成度评估和交付决策
- ✅ 迭代日志和追踪
- ✅ 支持多 Agent 并行执行

### 1.2 Ralph Loop 精神

```
┌─────────────────────────────────────────────────────────┐
│              Ralph Loop 技术哲学                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  "尽管遇到挫折，但依然坚持迭代"                            │
│                                                         │
│  灵感来源：《辛普森一家》- Ralph Wiggum                  │
│                                                         │
│  核心精神：                                              │
│  - 🔄 持续迭代，永不放弃                                 │
│  - 💪 遇到挫折是常态，继续就好                           │
│  - 🎯 目标导向，结果说话                                 │
│  - 🤖 AI 自主驱动，无需人类干预                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.3 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                   Ralph Loop Engine                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Iteration Controller                │   │
│  │              (迭代控制器)                          │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  启动 │ 暂停 │ 恢复 │ 停止 │ 计数器 │ 配置     │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              R-A-L-P-H Cycle                     │   │
│  │              (核心循环层)                          │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  Read → Act → Leverage → Produce → Help → Check │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              Setback Handler                     │   │
│  │              (挫折处理器)                          │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  检测 │ 记录 │ 分类 │ 恢复 │ 学习 │ 分析       │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              Completion Checker                  │   │
│  │              (完成度检查器)                        │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  需求覆盖 │ 文档完整 │ 质量检查 │ 交付决策     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 迭代控制设计

### 2.1 迭代配置

```python
# src/ralph_loop/config.py

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RalphLoopConfig(BaseModel):
    """
    Ralph Loop 配置
    
    控制迭代行为的参数
    """
    # 迭代控制
    max_iterations: int = 50           # 最大迭代次数
    iteration_timeout: int = 3600      # 单次迭代超时 (秒)
    parallel_agents: bool = True       # 是否并行执行
    
    # 完成度检查
    completion_threshold: float = 0.9  # 完成度阈值 (90%)
    min_iterations: int = 3            # 最小迭代次数
    check_interval: int = 5            # 每 N 次迭代检查一次
    
    # 挫折处理
    max_setbacks: int = 20             # 最大挫折次数
    setback_cooldown: int = 300        # 挫折冷却时间 (秒)
    auto_recovery: bool = True         # 自动恢复
    
    # 日志和追踪
    enable_logging: bool = True        # 启用日志
    log_level: str = "INFO"            # 日志级别
    save_history: bool = True          # 保存历史
    
    # 通知
    notify_on_iteration: bool = False  # 每次迭代通知
    notify_on_setback: bool = True     # 挫折时通知
    notify_on_completion: bool = True  # 完成时通知
    
    class Config:
        arbitrary_types_allowed = True
```

### 2.2 迭代状态

```python
# src/ralph_loop/state.py

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class LoopStatus(Enum):
    """Loop 状态"""
    IDLE = "idle"                  # 空闲
    RUNNING = "running"            # 运行中
    PAUSED = "paused"              # 已暂停
    STOPPED = "stopped"            # 已停止
    COMPLETED = "completed"        # 已完成
    FAILED = "failed"              # 失败


class IterationState(BaseModel):
    """迭代状态"""
    iteration_number: int          # 当前迭代次数
    start_time: int                # 开始时间戳
    end_time: Optional[int] = None  # 结束时间戳
    status: LoopStatus             # 状态
    agents_participating: List[str]  # 参与的 Agent
    documents_read: int = 0        # 阅读文档数
    requests_processed: int = 0    # 处理诉求数
    documents_produced: int = 0    # 产出文档数
    requests_posted: int = 0       # 发布诉求数
    setbacks_encountered: int = 0  # 遇到挫折数
    completion_score: float = 0.0  # 完成度分数
    
    class Config:
        use_enum_values = True
```

### 2.3 迭代控制器

```python
# src/ralph_loop/controller.py

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import RalphLoopConfig
from .state import LoopStatus, IterationState


class IterationController:
    """
    迭代控制器
    
    管理 Ralph Loop 的生命周期
    """
    
    def __init__(
        self,
        config: Optional[RalphLoopConfig] = None,
    ):
        self.config = config or RalphLoopConfig()
        
        # 当前状态
        self.status = LoopStatus.IDLE
        self.current_iteration: Optional[IterationState] = None
        
        # 迭代历史
        self.history: List[IterationState] = []
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 运行任务
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(
        self,
        agents: List["Agent"],
        team_session: "Session",
    ):
        """
        启动 Ralph Loop
        
        流程：
        1. 检查状态
        2. 创建迭代状态
        3. 启动循环
        """
        async with self._lock:
            if self.status != LoopStatus.IDLE:
                raise RuntimeError("Loop is already running")
            
            # 1. 更新状态
            self.status = LoopStatus.RUNNING
            self._running = True
            
            # 2. 创建迭代状态
            self.current_iteration = IterationState(
                iteration_number=0,
                start_time=int(datetime.now().timestamp()),
                status=LoopStatus.RUNNING,
                agents_participating=[a.role for a in agents],
            )
            
            # 3. 启动循环
            self._task = asyncio.create_task(
                self._run_loop(agents, team_session)
            )
    
    async def pause(self):
        """暂停 Loop"""
        async with self._lock:
            if self.status != LoopStatus.RUNNING:
                return
            
            self.status = LoopStatus.PAUSED
            self._running = False
    
    async def resume(self, agents: List["Agent"], team_session: "Session"):
        """恢复 Loop"""
        async with self._lock:
            if self.status != LoopStatus.PAUSED:
                return
            
            self.status = LoopStatus.RUNNING
            self._running = True
            
            # 恢复循环
            self._task = asyncio.create_task(
                self._run_loop(agents, team_session)
            )
    
    async def stop(self):
        """停止 Loop"""
        async with self._lock:
            self._running = False
            self.status = LoopStatus.STOPPED
            
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            
            # 保存最终状态
            if self.current_iteration:
                self.current_iteration.end_time = int(datetime.now().timestamp())
                self.current_iteration.status = LoopStatus.STOPPED
                self.history.append(self.current_iteration)
    
    async def _run_loop(
        self,
        agents: List["Agent"],
        team_session: "Session",
    ):
        """
        运行 Loop
        
        主循环逻辑
        """
        try:
            while self._running:
                # 检查最大迭代次数
                if self.current_iteration.iteration_number >= self.config.max_iterations:
                    await self._complete("max_iterations")
                    break
                
                # 执行一次迭代
                await self._run_iteration(agents, team_session)
                
                # 增加迭代计数
                self.current_iteration.iteration_number += 1
                
                # 检查完成度
                if self.current_iteration.iteration_number >= self.config.min_iterations:
                    if self.current_iteration.iteration_number % self.config.check_interval == 0:
                        completion = await self._check_completion()
                        if completion >= self.config.completion_threshold:
                            await self._complete("completion_reached")
                            break
                
                # 检查挫折次数
                if self.current_iteration.setbacks_encountered >= self.config.max_setbacks:
                    await self._complete("max_setbacks")
                    break
                
                # 短暂延迟，避免过快迭代
                await asyncio.sleep(1)
        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # 记录错误
            print(f"Error in Ralph Loop: {e}")
            await self._complete(f"error: {e}")
    
    async def _run_iteration(
        self,
        agents: List["Agent"],
        team_session: "Session",
    ):
        """执行一次迭代"""
        # 并行执行所有 Agent 的 Ralph Loop
        if self.config.parallel_agents:
            tasks = [
                self._execute_agent_ralph_loop(agent, team_session)
                for agent in agents
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 串行执行
            for agent in agents:
                await self._execute_agent_ralph_loop(agent, team_session)
    
    async def _execute_agent_ralph_loop(
        self,
        agent: "Agent",
        team_session: "Session",
    ):
        """执行单个 Agent 的 Ralph Loop"""
        try:
            # R - Read
            documents = await agent.read_documents()
            self.current_iteration.documents_read += len(documents)
            
            # A - Act
            requests = await agent.act_on_requests()
            self.current_iteration.requests_processed += len(requests)
            
            # L - Leverage
            work_result = await agent.leverage_expertise()
            
            # P - Produce
            document = await agent.produce_document(work_result)
            if document:
                self.current_iteration.documents_produced += 1
            
            # H - Help
            help_requests = await agent.help_requests()
            self.current_iteration.requests_posted += len(help_requests)
        
        except Exception as e:
            # 记录挫折
            self.current_iteration.setbacks_encountered += 1
            await self._handle_setback(agent, e)
    
    async def _check_completion(self) -> float:
        """检查完成度"""
        # 这里调用 Completion Checker
        # 简化实现
        return self.current_iteration.completion_score
    
    async def _handle_setback(self, agent: "Agent", error: Exception):
        """处理挫折"""
        # 记录挫折
        # 通知 Coordinator
        pass
    
    async def _complete(self, reason: str):
        """完成 Loop"""
        self._running = False
        
        if self.current_iteration:
            self.current_iteration.end_time = int(datetime.now().timestamp())
            self.current_iteration.status = (
                LoopStatus.COMPLETED if reason in ["completion_reached"]
                else LoopStatus.FAILED
            )
            self.history.append(self.current_iteration)
        
        self.status = LoopStatus.COMPLETED if reason == "completion_reached" else LoopStatus.FAILED
    
    def get_current_iteration(self) -> Optional[IterationState]:
        """获取当前迭代状态"""
        return self.current_iteration
    
    def get_history(self) -> List[IterationState]:
        """获取迭代历史"""
        return self.history
```

---

## 3. 挫折处理设计

### 3.1 挫折类型

```python
# src/ralph_loop/setback.py

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class SetbackType(Enum):
    """挫折类型"""
    # 技术挫折
    TECHNICAL_ERROR = "technical_error"     # 技术错误
    API_FAILURE = "api_failure"             # API 失败
    TIMEOUT = "timeout"                     # 超时
    
    # 协作挫折
    NO_RESPONSE = "no_response"             # 无响应
    CONFLICT = "conflict"                   # 冲突
    BLOCKED = "blocked"                     # 被阻塞
    
    # 资源挫折
    RESOURCE_UNAVAILABLE = "resource_unavailable"  # 资源不可用
    QUOTA_EXCEEDED = "quota_exceeded"       # 配额超出
    
    # 质量挫折
    QUALITY_ISSUE = "quality_issue"         # 质量问题
    INCOMPLETE = "incomplete"               # 不完整
    
    # 其他
    OTHER = "other"                         # 其他


class SetbackSeverity(Enum):
    """挫折严重程度"""
    LOW = "low"              # 低 - 可以忽略
    MEDIUM = "medium"        # 中 - 需要处理
    HIGH = "high"            # 高 - 需要立即处理
    CRITICAL = "critical"    # 严重 - 可能终止循环


class Setback(BaseModel):
    """挫折记录"""
    id: str                           # 挫折 ID
    type: SetbackType                 # 类型
    severity: SetbackSeverity         # 严重程度
    agent: str                        # 发生挫折的 Agent
    iteration: int                    # 迭代次数
    description: str                  # 描述
    error_message: Optional[str] = None  # 错误消息
    context: Dict[str, Any] = Field(default_factory=dict)  # 上下文
    timestamp: int                    # 时间戳
    resolved: bool = False            # 是否已解决
    resolution: Optional[str] = None  # 解决方案
    resolved_at: Optional[int] = None  # 解决时间
    
    class Config:
        use_enum_values = True
```

### 3.2 挫折处理器

```python
class SetbackHandler:
    """
    挫折处理器
    
    检测、记录、分类、恢复挫折
    """
    
    def __init__(self):
        # 挫折历史
        self._setbacks: List[Setback] = []
        
        # 挫折模式
        self._patterns: Dict[str, int] = {}
        
        # 恢复策略
        self._recovery_strategies: Dict[SetbackType, callable] = {}
        
        # 注册默认恢复策略
        self._register_default_strategies()
    
    async def record_setback(
        self,
        agent: "Agent",
        iteration: int,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> Setback:
        """
        记录挫折
        
        流程：
        1. 分类挫折
        2. 评估严重程度
        3. 记录挫折
        4. 分析模式
        5. 尝试恢复
        """
        # 1. 分类挫折
        setback_type = self._classify_setback(error)
        
        # 2. 评估严重程度
        severity = self._assess_severity(setback_type, error)
        
        # 3. 记录挫折
        setback = Setback(
            id=self._generate_setback_id(),
            type=setback_type,
            severity=severity,
            agent=agent.role,
            iteration=iteration,
            description=str(error),
            error_message=str(error),
            context=context or {},
            timestamp=int(datetime.now().timestamp()),
        )
        
        self._setbacks.append(setback)
        
        # 4. 分析模式
        self._analyze_pattern(setback)
        
        # 5. 尝试恢复
        await self._attempt_recovery(setback, agent)
        
        return setback
    
    def _classify_setback(self, error: Exception) -> SetbackType:
        """分类挫折"""
        error_str = str(error).lower()
        
        # 技术挫折
        if "connection" in error_str or "network" in error_str:
            return SetbackType.API_FAILURE
        if "timeout" in error_str:
            return SetbackType.TIMEOUT
        if "error" in error_str or "exception" in error_str:
            return SetbackType.TECHNICAL_ERROR
        
        # 协作挫折
        if "no response" in error_str or "not found" in error_str:
            return SetbackType.NO_RESPONSE
        if "conflict" in error_str:
            return SetbackType.CONFLICT
        if "blocked" in error_str:
            return SetbackType.BLOCKED
        
        # 资源挫折
        if "unavailable" in error_str or "not enough" in error_str:
            return SetbackType.RESOURCE_UNAVAILABLE
        if "quota" in error_str or "limit" in error_str:
            return SetbackType.QUOTA_EXCEEDED
        
        # 质量挫折
        if "quality" in error_str or "invalid" in error_str:
            return SetbackType.QUALITY_ISSUE
        if "incomplete" in error_str:
            return SetbackType.INCOMPLETE
        
        return SetbackType.OTHER
    
    def _assess_severity(
        self,
        setback_type: SetbackType,
        error: Exception,
    ) -> SetbackSeverity:
        """评估严重程度"""
        # 根据类型和错误消息评估
        if setback_type in [SetbackType.CRITICAL, SetbackType.API_FAILURE]:
            return SetbackSeverity.HIGH
        if setback_type in [SetbackType.TIMEOUT, SetbackType.NO_RESPONSE]:
            return SetbackSeverity.MEDIUM
        return SetbackSeverity.LOW
    
    async def _attempt_recovery(
        self,
        setback: Setback,
        agent: "Agent",
    ):
        """尝试恢复"""
        strategy = self._recovery_strategies.get(setback.type)
        if strategy:
            try:
                await strategy(setback, agent)
                setback.resolved = True
                setback.resolution = "Auto-recovered"
                setback.resolved_at = int(datetime.now().timestamp())
            except Exception as e:
                setback.resolution = f"Recovery failed: {e}"
    
    def _register_default_strategies(self):
        """注册默认恢复策略"""
        # 超时重试
        self._recovery_strategies[SetbackType.TIMEOUT] = self._retry_strategy
        
        # API 失败重试
        self._recovery_strategies[SetbackType.API_FAILURE] = self._retry_strategy
        
        # 无响应 - 发送提醒
        self._recovery_strategies[SetbackType.NO_RESPONSE] = self._send_reminder
    
    async def _retry_strategy(
        self,
        setback: Setback,
        agent: "Agent",
    ):
        """重试策略"""
        # 等待一小段时间后重试
        await asyncio.sleep(5)
        # 这里可以触发重试逻辑
    
    async def _send_reminder(
        self,
        setback: Setback,
        agent: "Agent",
    ):
        """发送提醒策略"""
        # 发送提醒给相关 Agent
        pass
    
    def _analyze_pattern(self, setback: Setback):
        """分析挫折模式"""
        key = f"{setback.type.value}:{setback.agent}"
        self._patterns[key] = self._patterns.get(key, 0) + 1
    
    def get_patterns(self) -> Dict[str, int]:
        """获取挫折模式"""
        return self._patterns
    
    def get_setbacks(
        self,
        agent: Optional[str] = None,
        type: Optional[SetbackType] = None,
        limit: int = 100,
    ) -> List[Setback]:
        """获取挫折记录"""
        results = self._setbacks
        
        if agent:
            results = [s for s in results if s.agent == agent]
        if type:
            results = [s for s in results if s.type == type]
        
        return results[-limit:]
    
    def _generate_setback_id(self) -> str:
        """生成挫折 ID"""
        import hashlib
        timestamp = int(datetime.now().timestamp())
        data = f"setback:{timestamp}"
        return "setback_" + hashlib.md5(data.encode()).hexdigest()[:12]
```

---

## 4. 完成度检查设计

### 4.1 完成度评估器

```python
# src/ralph_loop/completion.py

from typing import Dict, Any, List
from pydantic import BaseModel


class CompletionCriteria(BaseModel):
    """完成度标准"""
    # 需求覆盖
    requirement_coverage: float = 0.9      # 90% 需求覆盖
    min_requirements_met: int = 0          # 最小满足需求数
    
    # 文档完整
    document_completeness: float = 0.8     # 80% 文档完整
    required_documents: List[str] = []     # 必需文档列表
    
    # 质量检查
    quality_score: float = 0.7             # 70% 质量分数
    max_open_issues: int = 5               # 最大未解决问题数
    
    # 交付标准
    all_tests_passed: bool = False         # 所有测试通过
    no_critical_bugs: bool = True          # 无严重 Bug


class CompletionChecker:
    """
    完成度检查器
    
    评估是否达到交付标准
    """
    
    def __init__(self, criteria: CompletionCriteria):
        self.criteria = criteria
    
    async def check(
        self,
        team_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        检查完成度
        
        返回：完成度评估结果
        """
        results = {
            "ready": False,
            "score": 0.0,
            "details": {},
            "blocking_issues": [],
        }
        
        # 1. 检查需求覆盖
        req_coverage = await self._check_requirement_coverage(team_state)
        results["details"]["requirement_coverage"] = req_coverage
        
        # 2. 检查文档完整
        doc_complete = await self._check_document_completeness(team_state)
        results["details"]["document_completeness"] = doc_complete
        
        # 3. 检查质量
        quality = await self._check_quality(team_state)
        results["details"]["quality"] = quality
        
        # 计算总分
        total_score = (
            req_coverage["score"] * 0.4 +
            doc_complete["score"] * 0.3 +
            quality["score"] * 0.3
        )
        results["score"] = total_score
        
        # 检查是否达到标准
        blocking_issues = []
        
        if req_coverage["score"] < self.criteria.requirement_coverage:
            blocking_issues.append("需求覆盖不足")
        
        if doc_complete["score"] < self.criteria.document_completeness:
            blocking_issues.append("文档不完整")
        
        if quality["score"] < self.criteria.quality_score:
            blocking_issues.append("质量不达标")
        
        if len(quality.get("open_issues", [])) > self.criteria.max_open_issues:
            blocking_issues.append("未解决问题过多")
        
        results["blocking_issues"] = blocking_issues
        results["ready"] = len(blocking_issues) == 0 and total_score >= self.criteria.requirement_coverage
        
        return results
    
    async def _check_requirement_coverage(
        self,
        team_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """检查需求覆盖"""
        # 从团队状态获取需求信息
        requirements = team_state.get("requirements", [])
        met_requirements = team_state.get("met_requirements", [])
        
        if not requirements:
            return {"score": 0.0, "total": 0, "met": 0}
        
        coverage = len(met_requirements) / len(requirements)
        
        return {
            "score": coverage,
            "total": len(requirements),
            "met": len(met_requirements),
        }
    
    async def _check_document_completeness(
        self,
        team_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """检查文档完整"""
        documents = team_state.get("documents", [])
        
        # 检查必需文档
        required = self.criteria.required_documents
        present = [doc for doc in required if any(doc in d.get("name", "") for d in documents)]
        
        completeness = len(present) / len(required) if required else 1.0
        
        return {
            "score": completeness,
            "required": len(required),
            "present": len(present),
            "missing": [d for d in required if d not in present],
        }
    
    async def _check_quality(
        self,
        team_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """检查质量"""
        # 从团队状态获取质量信息
        quality_score = team_state.get("quality_score", 0.0)
        open_issues = team_state.get("open_issues", [])
        critical_bugs = [i for i in open_issues if i.get("severity") == "critical"]
        
        return {
            "score": quality_score,
            "open_issues": open_issues,
            "critical_bugs": critical_bugs,
        }
```

---

## 5. 与 Agent 集成

### 5.1 Agent Ralph Loop 方法

```python
# src/agent/base.py (Ralph Loop 方法)

class Agent(ABC):
    """Agent 基类 - Ralph Loop 方法"""
    
    async def execute_ralph_loop(self) -> Dict[str, Any]:
        """
        执行完整的 Ralph Loop
        
        返回：执行结果
        """
        result = {
            "documents_read": [],
            "requests_processed": [],
            "work_result": None,
            "document_produced": None,
            "requests_posted": [],
            "setbacks": [],
        }
        
        try:
            # R - Read
            result["documents_read"] = await self.read_documents()
            
            # A - Act
            result["requests_processed"] = await self.act_on_requests()
            
            # L - Leverage
            result["work_result"] = await self.leverage_expertise()
            
            # P - Produce
            if result["work_result"]:
                result["document_produced"] = await self.produce_document(
                    result["work_result"]
                )
            
            # H - Help
            result["requests_posted"] = await self.help_requests()
        
        except Exception as e:
            result["setbacks"].append({
                "type": "execution_error",
                "error": str(e),
                "timestamp": int(datetime.now().timestamp()),
            })
        
        return result
```

---

## 6. 使用示例

### 6.1 基本使用

```python
# examples/ralph_loop_basic.py

import asyncio
from src.ralph_loop.controller import IterationController
from src.ralph_loop.config import RalphLoopConfig
from src.ralph_loop.setback import SetbackHandler
from src.ralph_loop.completion import CompletionChecker, CompletionCriteria


async def main():
    # 1. 配置
    config = RalphLoopConfig(
        max_iterations=50,
        completion_threshold=0.9,
        min_iterations=3,
    )
    
    # 2. 初始化组件
    controller = IterationController(config)
    setback_handler = SetbackHandler()
    completion_checker = CompletionChecker(
        CompletionCriteria(
            requirement_coverage=0.9,
            document_completeness=0.8,
            quality_score=0.7,
        )
    )
    
    # 3. 启动 Loop
    await controller.start(
        agents=team_agents,
        team_session=session,
    )
    
    # 4. 监控进度
    while controller.status == "running":
        iteration = controller.get_current_iteration()
        print(f"Iteration {iteration.iteration_number}")
        print(f"  Documents read: {iteration.documents_read}")
        print(f"  Documents produced: {iteration.documents_produced}")
        print(f"  Setbacks: {iteration.setbacks_encountered}")
        print(f"  Completion: {iteration.completion_score}")
        
        await asyncio.sleep(10)
    
    # 5. 获取结果
    history = controller.get_history()
    print(f"Completed in {len(history)} iterations")
```

---

## 7. 实现计划

| 阶段 | 内容 | 文件 | 预计时间 |
|------|------|------|----------|
| 1 | 配置和状态 | `config.py`, `state.py` | 2 小时 |
| 2 | 迭代控制器 | `controller.py` | 4 小时 |
| 3 | 挫折处理 | `setback.py` | 3 小时 |
| 4 | 完成度检查 | `completion.py` | 3 小时 |
| 5 | Agent 集成 | `base.py` | 2 小时 |
| 6 | 单元测试 | `tests/` | 3 小时 |
| **总计** | | | **17 小时** |

---

## 8. 成功标准

- [ ] 迭代控制器正常启动、暂停、恢复、停止
- [ ] Ralph Loop 循环正确执行
- [ ] 挫折检测和处理机制工作正常
- [ ] 完成度评估准确
- [ ] 单元测试覆盖率 >= 80%

---

> 最后更新：2026-03-11
> 状态：草稿
> 审核：待审核

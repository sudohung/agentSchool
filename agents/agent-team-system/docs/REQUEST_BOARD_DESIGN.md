# 诉求看板 (Request Board) 设计文档

> Agent Team System 核心组件设计
> 
> 版本：0.1.0
> 创建日期：2026-03-11
> 最后更新：2026-03-11

---

## 1. 概述

### 1.1 设计目标

构建一个**诉求看板系统**，作为 Agent 间协作的核心机制：

- ✅ Agent 通过诉求触发跨 Agent 协作
- ✅ 支持多种诉求类型 (请求、通知、问题、评审)
- ✅ 诉求优先级和状态管理
- ✅ 智能路由到目标 Agent
- ✅ 诉求响应追踪和统计

### 1.2 核心原则

| 原则 | 描述 |
|------|------|
| 💬 **诉求驱动** | 所有协作通过诉求触发 |
| 🎯 **精准路由** | 诉求自动路由到合适的 Agent |
| 📊 **状态透明** | 诉求状态对所有 Agent 可见 |
| ⏰ **超时处理** | 未响应诉求自动升级 |
| 📈 **可追溯** | 完整记录诉求历史 |

### 1.3 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Request Board                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Request Models                      │   │
│  │              (诉求模型层)                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  Request │ Response │ Thread │ Attachment      │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              Request Board                       │   │
│  │              (看板管理层)                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  创建 │ 更新 │ 查询 │ 删除 │ 状态管理           │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              Router Service                      │   │
│  │              (路由服务层)                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  角色路由 │ 技能路由 │ 负载均衡 │ 优先级队列    │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              Notification Integration            │   │
│  │              (通知集成层)                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  新诉求通知 │ 状态更新 │ 超时提醒 │ @提及       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 诉求模型设计

### 2.1 诉求类型枚举

```python
# src/request_board/models.py

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class RequestType(Enum):
    """诉求类型"""
    # 协作请求
    COLLABORATION = "collaboration"    # 协作请求
    INFORMATION = "information"        # 信息查询
    REVIEW = "review"                  # 审查请求
    DECISION = "decision"              # 决策请求
    
    # 通知
    NOTIFICATION = "notification"      # 通知
    PROGRESS = "progress"              # 进度通知
    COMPLETION = "completion"          # 完成通知
    
    # 问题
    QUESTION = "question"              # 问题
    CLARIFICATION = "clarification"    # 澄清请求
    BLOCKER = "blocker"                # 阻塞问题
    
    # 其他
    OTHER = "other"                    # 其他
```

### 2.2 诉求优先级

```python
class RequestPriority(Enum):
    """诉求优先级"""
    LOW = "low"              # 低 - 可以等待
    NORMAL = "normal"        # 普通 - 正常处理
    HIGH = "high"            # 高 - 优先处理
    CRITICAL = "critical"    # 紧急 - 立即处理
```

### 2.3 诉求状态

```python
class RequestStatus(Enum):
    """诉求状态"""
    PENDING = "pending"          # 待处理
    RECEIVED = "received"        # 已接收
    PROCESSING = "processing"    # 处理中
    WAITING = "waiting"          # 等待更多信息
    RESOLVED = "resolved"        # 已解决
    CLOSED = "closed"            # 已关闭
    ESCALATED = "escalated"      # 已升级
    TIMEOUT = "timeout"          # 超时
```

### 2.4 诉求基础模型

```python
class Request(BaseModel):
    """
    诉求基础模型
    
    Agent 间协作的基本单位
    """
    # 基础信息
    id: str                           # 诉求 ID
    type: RequestType                 # 诉求类型
    priority: RequestPriority         # 优先级
    status: RequestStatus             # 状态
    
    # 参与方
    from_agent: str                   # 发送方 (Agent 角色)
    to_agent: str                     # 接收方 (Agent 角色/角色列表/"all")
    cc: List[str] = Field(default_factory=list)  # 抄送方
    
    # 内容
    subject: str                      # 主题
    content: str                      # 内容
    context: Dict[str, Any] = Field(default_factory=dict)  # 上下文信息
    
    # 时间
    created_at: int                   # 创建时间戳
    updated_at: int                   # 更新时间戳
    due_at: Optional[int] = None      # 截止时间戳
    
    # 响应
    response: Optional[str] = None    # 响应内容
    responded_at: Optional[int] = None  # 响应时间戳
    responded_by: Optional[str] = None  # 响应者
    
    # 元数据
    tags: List[str] = Field(default_factory=list)  # 标签
    related_requests: List[str] = Field(default_factory=list)  # 相关诉求 ID
    related_documents: List[str] = Field(default_factory=list)  # 相关文档 ID
    attachments: List[Dict[str, Any]] = Field(default_factory=list)  # 附件
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
```

### 2.5 诉求响应模型

```python
class RequestResponse(BaseModel):
    """诉求响应"""
    id: str                           # 响应 ID
    request_id: str                   # 关联诉求 ID
    from_agent: str                   # 响应者
    content: str                      # 响应内容
    timestamp: int                    # 时间戳
    action_taken: Optional[str] = None  # 采取的行动
    follow_up_requests: List[str] = Field(default_factory=list)  # 后续诉求
```

### 2.6 诉求线程模型

```python
class RequestThread(BaseModel):
    """诉求讨论线程"""
    id: str                           # 线程 ID
    request_id: str                   # 关联诉求 ID
    messages: List[Dict[str, Any]]    # 消息列表
    participants: List[str]           # 参与者
```

---

## 3. 看板管理设计

### 3.1 看板类

```python
# src/request_board/board.py

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import (
    Request,
    RequestType,
    RequestPriority,
    RequestStatus,
    RequestResponse,
)


class RequestBoard:
    """
    诉求看板类
    
    管理所有诉求的创建、查询、更新、删除
    """
    
    def __init__(self):
        # 诉求存储：request_id -> Request
        self._requests: Dict[str, Request] = {}
        
        # 按 Agent 索引：agent_role -> [request_id, ...]
        self._agent_index: Dict[str, List[str]] = {}
        
        # 按状态索引：status -> [request_id, ...]
        self._status_index: Dict[str, List[str]] = {}
        
        # 按类型索引：type -> [request_id, ...]
        self._type_index: Dict[str, List[str]] = {}
        
        # 响应存储：request_id -> [RequestResponse, ...]
        self._responses: Dict[str, List[RequestResponse]] = {}
        
        # 锁
        self._lock = asyncio.Lock()
    
    async def create_request(self, request: Request) -> str:
        """
        创建诉求
        
        流程：
        1. 验证诉求
        2. 生成 ID
        3. 存储诉求
        4. 更新索引
        5. 返回 ID
        
        返回：诉求 ID
        """
        async with self._lock:
            # 1. 验证诉求
            self._validate_request(request)
            
            # 2. 生成 ID (如果未提供)
            if not request.id:
                request.id = self._generate_request_id()
            
            # 3. 存储诉求
            self._requests[request.id] = request
            
            # 4. 更新索引
            self._update_indices(request)
            
            # 5. 返回 ID
            return request.id
    
    async def get_request(self, request_id: str) -> Optional[Request]:
        """获取诉求"""
        return self._requests.get(request_id)
    
    async def update_request(
        self,
        request_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        更新诉求
        
        可更新字段：
        - status
        - priority
        - content
        - response
        - due_at
        """
        async with self._lock:
            if request_id not in self._requests:
                return False
            
            request = self._requests[request_id]
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(request, key):
                    setattr(request, key, value)
            
            # 更新时间戳
            request.updated_at = int(datetime.now().timestamp())
            
            # 如果状态改变，更新索引
            if "status" in updates:
                self._update_status_index(request_id, updates["status"])
            
            return True
    
    async def delete_request(self, request_id: str) -> bool:
        """删除诉求"""
        async with self._lock:
            if request_id not in self._requests:
                return False
            
            request = self._requests[request_id]
            
            # 从存储移除
            del self._requests[request_id]
            
            # 从索引移除
            self._remove_from_indices(request)
            
            # 移除响应
            if request_id in self._responses:
                del self._responses[request_id]
            
            return True
    
    async def get_requests_for_agent(
        self,
        agent_role: str,
        status: Optional[RequestStatus] = None,
        priority: Optional[RequestPriority] = None,
        limit: int = 100,
    ) -> List[Request]:
        """
        获取指定 Agent 的诉求
        
        支持按状态、优先级过滤
        """
        request_ids = self._agent_index.get(agent_role, [])
        results = []
        
        for request_id in request_ids:
            request = self._requests.get(request_id)
            if not request:
                continue
            
            # 过滤
            if status and request.status != status.value:
                continue
            if priority and request.priority != priority.value:
                continue
            
            results.append(request)
            
            # 限制数量
            if len(results) >= limit:
                break
        
        return results
    
    async def get_pending_requests(
        self,
        agent_role: Optional[str] = None,
        limit: int = 50,
    ) -> List[Request]:
        """获取待处理诉求"""
        if agent_role:
            return await self.get_requests_for_agent(
                agent_role=agent_role,
                status=RequestStatus.PENDING,
                limit=limit,
            )
        
        # 获取所有待处理诉求
        request_ids = self._status_index.get(RequestStatus.PENDING.value, [])
        return [
            self._requests[rid]
            for rid in request_ids[:limit]
            if rid in self._requests
        ]
    
    async def add_response(
        self,
        request_id: str,
        response: RequestResponse,
    ) -> bool:
        """添加响应"""
        async with self._lock:
            if request_id not in self._requests:
                return False
            
            if request_id not in self._responses:
                self._responses[request_id] = []
            
            self._responses[request_id].append(response)
            
            # 更新诉求状态
            request = self._requests[request_id]
            request.status = RequestStatus.RESOLVED.value
            request.response = response.content
            request.responded_at = response.timestamp
            request.responded_by = response.from_agent
            
            return True
    
    async def get_responses(self, request_id: str) -> List[RequestResponse]:
        """获取诉求的所有响应"""
        return self._responses.get(request_id, [])
    
    async def search_requests(
        self,
        query: str,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        status: Optional[RequestStatus] = None,
        limit: int = 50,
    ) -> List[Request]:
        """搜索诉求"""
        results = []
        query_lower = query.lower()
        
        for request in self._requests.values():
            # 过滤条件
            if from_agent and request.from_agent != from_agent:
                continue
            if to_agent and request.to_agent != to_agent:
                continue
            if status and request.status != status.value:
                continue
            
            # 搜索
            if (
                query_lower in request.subject.lower() or
                query_lower in request.content.lower() or
                any(query_lower in tag.lower() for tag in request.tags)
            ):
                results.append(request)
            
            # 限制数量
            if len(results) >= limit:
                break
        
        return results
    
    def _validate_request(self, request: Request):
        """验证诉求"""
        if not request.from_agent:
            raise ValueError("from_agent is required")
        if not request.to_agent:
            raise ValueError("to_agent is required")
        if not request.subject:
            raise ValueError("subject is required")
        if not request.content:
            raise ValueError("content is required")
    
    def _generate_request_id(self) -> str:
        """生成诉求 ID"""
        import hashlib
        timestamp = int(datetime.now().timestamp())
        data = f"request:{timestamp}"
        return "req_" + hashlib.md5(data.encode()).hexdigest()[:12]
    
    def _update_indices(self, request: Request):
        """更新索引"""
        # Agent 索引 (发送方)
        if request.from_agent not in self._agent_index:
            self._agent_index[request.from_agent] = []
        self._agent_index[request.from_agent].append(request.id)
        
        # Agent 索引 (接收方)
        if request.to_agent not in self._agent_index:
            self._agent_index[request.to_agent] = []
        self._agent_index[request.to_agent].append(request.id)
        
        # 状态索引
        if request.status not in self._status_index:
            self._status_index[request.status] = []
        self._status_index[request.status].append(request.id)
        
        # 类型索引
        if request.type not in self._type_index:
            self._type_index[request.type] = []
        self._type_index[request.type].append(request.id)
    
    def _remove_from_indices(self, request: Request):
        """从索引移除"""
        # Agent 索引
        for agent in [request.from_agent, request.to_agent]:
            if agent in self._agent_index:
                if request.id in self._agent_index[agent]:
                    self._agent_index[agent].remove(request.id)
        
        # 状态索引
        if request.status in self._status_index:
            if request.id in self._status_index[request.status]:
                self._status_index[request.status].remove(request.id)
        
        # 类型索引
        if request.type in self._type_index:
            if request.id in self._type_index[request.type]:
                self._type_index[request.type].remove(request.id)
    
    def _update_status_index(
        self,
        request_id: str,
        new_status: str,
    ):
        """更新状态索引"""
        # 从旧状态移除
        for status, ids in self._status_index.items():
            if request_id in ids:
                ids.remove(request_id)
                break
        
        # 添加到新状态
        if new_status not in self._status_index:
            self._status_index[new_status] = []
        self._status_index[new_status].append(request_id)
```

---

## 4. 路由服务设计

### 4.1 路由策略

```python
# src/request_board/router.py

from enum import Enum
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod


class RoutingStrategy(Enum):
    """路由策略"""
    ROLE_BASED = "role_based"          # 基于角色
    SKILL_BASED = "skill_based"        # 基于技能
    LOAD_BALANCED = "load_balanced"    # 负载均衡
    PRIORITY_BASED = "priority_based"  # 优先级
    ROUND_ROBIN = "round_robin"        # 轮询


class RouterStrategy(ABC):
    """路由策略基类"""
    
    @abstractmethod
    async def route(
        self,
        request: "Request",
        available_agents: List[str],
    ) -> List[str]:
        """
        路由诉求到目标 Agent
        
        返回：目标 Agent 列表
        """
        pass


class RoleBasedRouter(RouterStrategy):
    """基于角色的路由"""
    
    async def route(
        self,
        request: "Request",
        available_agents: List[str],
    ) -> List[str]:
        """根据角色路由"""
        to_agent = request.to_agent
        
        # 如果是指定角色
        if to_agent in available_agents:
            return [to_agent]
        
        # 如果是广播
        if to_agent == "all":
            return available_agents
        
        # 如果是角色组
        if to_agent.startswith("group:"):
            group_name = to_agent.split(":")[1]
            return self._get_group_members(group_name, available_agents)
        
        return available_agents
    
    def _get_group_members(
        self,
        group_name: str,
        available_agents: List[str],
    ) -> List[str]:
        """获取组成员"""
        #  predefined 组映射
        groups = {
            "devs": ["Frontend Developer", "Backend Developer", "Full Stack Developer"],
            "quality": ["QA Engineer", "Code Reviewer"],
            "leadership": ["Product Manager", "System Architect", "Tech Lead"],
        }
        
        members = groups.get(group_name, [])
        return [a for a in available_agents if a in members]


class SkillBasedRouter(RouterStrategy):
    """基于技能的路由"""
    
    def __init__(self, agent_skills: Dict[str, List[str]]):
        """
        初始化
        
        agent_skills: {agent_role: [skills, ...]}
        """
        self.agent_skills = agent_skills
    
    async def route(
        self,
        request: "Request",
        available_agents: List[str],
    ) -> List[str]:
        """根据技能匹配路由"""
        required_skills = request.context.get("required_skills", [])
        
        if not required_skills:
            return available_agents
        
        # 计算技能匹配度
        scored_agents = []
        for agent in available_agents:
            skills = self.agent_skills.get(agent, [])
            match_count = sum(1 for s in required_skills if s in skills)
            scored_agents.append((agent, match_count))
        
        # 按匹配度排序
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        # 返回匹配的 Agent
        return [a for a, score in scored_agents if score > 0]


class LoadBalancedRouter(RouterStrategy):
    """负载均衡路由"""
    
    def __init__(self, request_board: "RequestBoard"):
        self.request_board = request_board
    
    async def route(
        self,
        request: "Request",
        available_agents: List[str],
    ) -> List[str]:
        """根据工作负载路由"""
        # 计算每个 Agent 的待处理诉求数量
        workloads = {}
        for agent in available_agents:
            pending = await self.request_board.get_pending_requests(
                agent_role=agent,
                limit=1000,
            )
            workloads[agent] = len(pending)
        
        # 选择工作负载最低的 Agent
        if not workloads:
            return available_agents
        
        min_workload = min(workloads.values())
        return [
            agent for agent, workload in workloads.items()
            if workload == min_workload
        ]
```

### 4.2 路由服务

```python
class RouterService:
    """
    路由服务类
    
    根据配置的路由策略将诉求路由到目标 Agent
    """
    
    def __init__(self, request_board: "RequestBoard"):
        self.request_board = request_board
        
        # 注册的路由策略
        self._strategies: Dict[RoutingStrategy, RouterStrategy] = {}
        
        # Agent 技能映射
        self._agent_skills: Dict[str, List[str]] = {}
        
        # 默认策略
        self.default_strategy = RoutingStrategy.ROLE_BASED
    
    def register_strategy(
        self,
        strategy: RoutingStrategy,
        router: RouterStrategy,
    ):
        """注册路由策略"""
        self._strategies[strategy] = router
    
    def register_agent_skills(
        self,
        agent_role: str,
        skills: List[str],
    ):
        """注册 Agent 技能"""
        self._agent_skills[agent_role] = skills
    
    async def route_request(
        self,
        request: "Request",
        strategy: Optional[RoutingStrategy] = None,
    ) -> List[str]:
        """
        路由诉求
        
        流程：
        1. 获取可用 Agent 列表
        2. 选择路由策略
        3. 执行路由
        4. 返回目标 Agent 列表
        """
        # 1. 获取可用 Agent
        available_agents = await self._get_available_agents()
        
        # 2. 选择策略
        strategy = strategy or self.default_strategy
        router = self._strategies.get(strategy)
        
        if not router:
            # 使用默认的角色路由
            router = RoleBasedRouter()
        
        # 3. 执行路由
        targets = await router.route(request, available_agents)
        
        # 4. 返回目标
        return targets
    
    async def _get_available_agents(self) -> List[str]:
        """获取可用 Agent 列表"""
        # 这里可以从 Agent Registry 获取
        # 暂时返回预定义列表
        return [
            "Product Manager",
            "System Architect",
            "Tech Lead",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "QA Engineer",
            "Code Reviewer",
            "Doc Writer",
            "DevOps Engineer",
            "Security Engineer",
            "Coordinator",
        ]
```

---

## 5. 超时和升级机制

### 5.1 超时配置

```python
# src/request_board/timeout.py

from typing import Dict, Optional
from enum import Enum


class TimeoutConfig:
    """超时配置"""
    
    # 默认超时时间 (秒)
    DEFAULT_TIMEOUT = {
        "low": 3600,        # 低优先级：1 小时
        "normal": 1800,     # 普通：30 分钟
        "high": 900,        # 高：15 分钟
        "critical": 300,    # 紧急：5 分钟
    }
    
    # 升级阈值 (秒)
    ESCALATION_THRESHOLD = {
        "low": 7200,        # 低优先级：2 小时未响应则升级
        "normal": 3600,     # 普通：1 小时
        "high": 1800,       # 高：30 分钟
        "critical": 600,    # 紧急：10 分钟
    }
    
    # 升级目标
    ESCALATION_TARGETS = {
        "low": "Coordinator",
        "normal": "Coordinator",
        "high": "Tech Lead",
        "critical": "Product Manager",
    }
    
    @classmethod
    def get_timeout(cls, priority: str) -> int:
        """获取超时时间"""
        return cls.DEFAULT_TIMEOUT.get(priority, cls.DEFAULT_TIMEOUT["normal"])
    
    @classmethod
    def get_escalation_threshold(cls, priority: str) -> int:
        """获取升级阈值"""
        return cls.ESCALATION_THRESHOLD.get(
            priority,
            cls.ESCALATION_THRESHOLD["normal"],
        )
    
    @classmethod
    def get_escalation_target(cls, priority: str) -> str:
        """获取升级目标"""
        return cls.ESCALATION_TARGETS.get(
            priority,
            cls.ESCALATION_TARGETS["normal"],
        )
```

### 5.2 超时监控

```python
class TimeoutMonitor:
    """
    超时监控类
    
    监控诉求超时并自动升级
    """
    
    def __init__(
        self,
        request_board: "RequestBoard",
        config: Optional[TimeoutConfig] = None,
    ):
        self.request_board = request_board
        self.config = config or TimeoutConfig()
        
        # 监控任务
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self):
        """启动监控"""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._check_timeouts()
                await asyncio.sleep(60)  # 每分钟检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in timeout monitor: {e}")
    
    async def _check_timeouts(self):
        """检查超时"""
        now = int(datetime.now().timestamp())
        
        # 获取所有待处理诉求
        pending = await self.request_board.get_pending_requests(limit=1000)
        
        for request in pending:
            # 检查是否超时
            age = now - request.created_at
            timeout = self.config.get_timeout(request.priority)
            
            if age > timeout:
                # 超时，升级诉求
                await self._escalate_request(request)
    
    async def _escalate_request(self, request: "Request"):
        """升级诉求"""
        # 获取升级目标
        escalation_target = self.config.get_escalation_target(request.priority)
        
        # 更新诉求
        await self.request_board.update_request(
            request_id=request.id,
            updates={
                "status": RequestStatus.ESCALATED.value,
                "to_agent": escalation_target,
                "content": f"[ESCALATED] {request.content}\n\n原接收方：{request.to_agent}\n升级原因：超时未响应",
            },
        )
        
        # 通知升级目标
        # (通过 Notification Service)
```

---

## 6. 与 Agent 集成

### 6.1 Agent 诉求方法

```python
# src/agent/base.py (增强版)

class Agent(ABC):
    """Agent 基类 - 诉求能力"""
    
    def __init__(
        self,
        role: str,
        expertise: List[str],
        session: Session,
        client: OpenCodeClient,
        config: Optional[AgentConfig] = None,
        coordinator: Optional["CoordinatorAgent"] = None,
        request_board: Optional["RequestBoard"] = None,
    ):
        # ... 其他初始化 ...
        self.request_board = request_board
    
    async def post_request(
        self,
        to_agent: str,
        subject: str,
        content: str,
        request_type: RequestType = RequestType.COLLABORATION,
        priority: RequestPriority = RequestPriority.NORMAL,
        context: Optional[Dict[str, Any]] = None,
        due_at: Optional[int] = None,
    ) -> str:
        """
        发布诉求
        
        返回：诉求 ID
        """
        request = Request(
            id="",  # 自动生成
            type=request_type,
            priority=priority,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent=to_agent,
            subject=subject,
            content=content,
            context=context or {},
            created_at=int(datetime.now().timestamp()),
            updated_at=int(datetime.now().timestamp()),
            due_at=due_at,
        )
        
        # 如果有 request_board，直接创建
        if self.request_board:
            request_id = await self.request_board.create_request(request)
        else:
            # 否则通过 Coordinator
            request_id = await self._post_via_coordinator(request)
        
        return request_id
    
    async def respond_to_request(
        self,
        request_id: str,
        response: str,
        action_taken: Optional[str] = None,
    ) -> bool:
        """
        响应诉求
        
        返回：是否成功
        """
        if not self.request_board:
            return False
        
        request_response = RequestResponse(
            id=self._generate_response_id(),
            request_id=request_id,
            from_agent=self.role,
            content=response,
            timestamp=int(datetime.now().timestamp()),
            action_taken=action_taken,
        )
        
        return await self.request_board.add_response(
            request_id,
            request_response,
        )
    
    async def get_my_requests(
        self,
        status: Optional[RequestStatus] = None,
        limit: int = 50,
    ) -> List[Request]:
        """获取我的诉求"""
        if not self.request_board:
            return []
        
        return await self.request_board.get_requests_for_agent(
            agent_role=self.role,
            status=status,
            limit=limit,
        )
    
    async def _post_via_coordinator(self, request: Request) -> str:
        """通过 Coordinator 发布诉求"""
        if self.coordinator:
            return await self.coordinator.collect_request(request)
        return ""
```

---

## 7. 使用示例

### 7.1 基本使用

```python
# examples/request_board_basic.py

import asyncio
from src.request_board.board import RequestBoard
from src.request_board.models import (
    Request,
    RequestType,
    RequestPriority,
    RequestStatus,
)


async def main():
    # 1. 初始化看板
    board = RequestBoard()
    
    # 2. 创建诉求
    request = Request(
        id="",
        type=RequestType.COLLABORATION,
        priority=RequestPriority.HIGH,
        status=RequestStatus.PENDING,
        from_agent="Product Manager",
        to_agent="System Architect",
        subject="请评估技术可行性",
        content="基于 PRD，请评估技术可行性和风险",
        created_at=int(__import__('time').time()),
        updated_at=int(__import__('time').time()),
    )
    
    # 3. 发布诉求
    request_id = await board.create_request(request)
    print(f"Request created: {request_id}")
    
    # 4. 查询诉求
    pending = await board.get_pending_requests(
        agent_role="System Architect",
    )
    print(f"Pending requests: {len(pending)}")
    
    # 5. 响应诉求
    from src.request_board.models import RequestResponse
    
    response = RequestResponse(
        id="resp_001",
        request_id=request_id,
        from_agent="System Architect",
        content="技术可行，建议使用微服务架构",
        timestamp=int(__import__('time').time()),
        action_taken="完成技术评估",
    )
    
    await board.add_response(request_id, response)
    print("Request responded")
    
    # 6. 搜索诉求
    results = await board.search_requests(
        query="技术",
        to_agent="System Architect",
    )
    print(f"Search results: {len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 8. 实现计划

| 阶段 | 内容 | 文件 | 预计时间 |
|------|------|------|----------|
| 1 | 诉求模型 | `models.py` | 2 小时 |
| 2 | 看板管理 | `board.py` | 4 小时 |
| 3 | 路由服务 | `router.py` | 3 小时 |
| 4 | 超时监控 | `timeout.py` | 2 小时 |
| 5 | Agent 集成 | `base.py` | 2 小时 |
| 6 | 单元测试 | `tests/` | 3 小时 |
| **总计** | | | **16 小时** |

---

## 9. 成功标准

- [ ] 诉求创建、查询、更新、删除功能正常
- [ ] 路由服务支持多种策略
- [ ] 超时监控和自动升级工作正常
- [ ] Agent 可以发布和响应诉求
- [ ] 单元测试覆盖率 >= 80%

---

> 最后更新：2026-03-11
> 状态：草稿
> 审核：待审核

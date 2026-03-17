"""路由服务 - 完整的诉求路由策略."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """路由策略"""
    ROLE_BASED = "role_based"
    SKILL_BASED = "skill_based"
    LOAD_BALANCED = "load_balanced"
    PRIORITY_BASED = "priority_based"
    ROUND_ROBIN = "round_robin"
    SMART = "smart"


@dataclass
class RoutingContext:
    """路由上下文"""
    request: Any
    available_agents: List[str]
    agent_skills: Dict[str, List[str]]
    agent_workloads: Dict[str, int]
    agent_status: Dict[str, str]


class RouterStrategy(ABC):
    """路由策略基类"""
    
    @abstractmethod
    async def route(self, context: RoutingContext) -> List[str]:
        """
        路由诉求到目标 Agent
        
        Returns:
            目标 Agent 列表（按优先级排序）
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass


class RoleBasedRouter(RouterStrategy):
    """
    基于角色的路由器
    """
    
    ROLE_GROUPS = {
        "devs": ["Frontend Developer", "Backend Developer", "Full Stack Developer"],
        "quality": ["QA Engineer", "Code Reviewer"],
        "leadership": ["Product Manager", "System Architect", "Tech Lead"],
    }
    
    @property
    def name(self) -> str:
        return "role_based"
    
    async def route(self, context: RoutingContext) -> List[str]:
        to_agent = context.request.to_agent
        available = context.available_agents
        
        if to_agent == "all":
            return available
        
        if to_agent.startswith("group:"):
            group_name = to_agent.split(":")[1]
            group_members = self.ROLE_GROUPS.get(group_name, [])
            return [a for a in available if a in group_members]
        
        if to_agent in available:
            return [to_agent]
        
        matched = [a for a in available if to_agent.lower() in a.lower()]
        if matched:
            return matched
        
        logger.warning(f"No match for role: {to_agent}")
        return []


class SkillBasedRouter(RouterStrategy):
    """
    基于技能的路由器
    """
    
    @property
    def name(self) -> str:
        return "skill_based"
    
    async def route(self, context: RoutingContext) -> List[str]:
        request = context.request
        required_skills = request.context.get("required_skills", [])
        
        if not required_skills:
            return context.available_agents
        
        scored_agents: List[tuple[str, int, int]] = []
        
        for agent in context.available_agents:
            agent_skills = context.agent_skills.get(agent, [])
            matched_skills = [s for s in required_skills if s in agent_skills]
            match_count = len(matched_skills)
            
            if match_count > 0:
                scored_agents.append((agent, match_count, len(agent_skills)))
        
        if not scored_agents:
            logger.warning(f"No agent matches required skills: {required_skills}")
            return context.available_agents
        
        scored_agents.sort(key=lambda x: (-x[1], x[2]))
        
        return [agent for agent, _, _ in scored_agents]


class LoadBalancedRouter(RouterStrategy):
    """
    负载均衡路由器
    """
    
    @property
    def name(self) -> str:
        return "load_balanced"
    
    async def route(self, context: RoutingContext) -> List[str]:
        workloads = context.agent_workloads
        
        if not workloads:
            return context.available_agents
        
        min_workload = min(workloads.values()) if workloads else 0
        
        low_load_agents = [
            agent for agent, workload in workloads.items()
            if workload == min_workload and agent in context.available_agents
        ]
        
        if low_load_agents:
            return low_load_agents
        
        return context.available_agents


class PriorityBasedRouter(RouterStrategy):
    """
    优先级路由器
    """
    
    def __init__(self):
        self.role_router = RoleBasedRouter()
        self.skill_router = SkillBasedRouter()
        self.load_router = LoadBalancedRouter()
    
    @property
    def name(self) -> str:
        return "priority_based"
    
    async def route(self, context: RoutingContext) -> List[str]:
        priority = context.request.priority
        
        if priority == "critical":
            critical_handlers = ["Tech Lead", "Coordinator", "Product Manager"]
            for handler in critical_handlers:
                if handler in context.available_agents:
                    return [handler]
            return context.available_agents
        
        elif priority == "high":
            return await self.skill_router.route(context)
        
        elif priority == "normal":
            return await self.load_router.route(context)
        
        else:
            return context.available_agents


class SmartRouter(RouterStrategy):
    """
    智能路由器 - 综合考虑多个因素
    """
    
    def __init__(self):
        self.role_router = RoleBasedRouter()
        self.skill_router = SkillBasedRouter()
        self.load_router = LoadBalancedRouter()
        self._performance_scores: Dict[str, float] = {}
    
    @property
    def name(self) -> str:
        return "smart"
    
    async def route(self, context: RoutingContext) -> List[str]:
        available = context.available_agents
        
        if not available:
            return []
        
        if context.request.to_agent and context.request.to_agent != "all":
            role_result = await self.role_router.route(context)
            if role_result:
                return role_result
        
        scored_agents: List[tuple[str, float]] = []
        
        for agent in available:
            score = await self._calculate_score(agent, context)
            scored_agents.append((agent, score))
        
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        return [agent for agent, _ in scored_agents]
    
    async def _calculate_score(self, agent: str, context: RoutingContext) -> float:
        """计算 Agent 的综合分数"""
        score = 0.0
        
        required_skills = context.request.context.get("required_skills", [])
        if required_skills:
            agent_skills = context.agent_skills.get(agent, [])
            skill_match = sum(1 for s in required_skills if s in agent_skills) / len(required_skills)
            score += skill_match * 0.3
        
        workload = context.agent_workloads.get(agent, 0)
        max_workload = max(context.agent_workloads.values()) if context.agent_workloads else 1
        load_score = 1 - (workload / max_workload) if max_workload > 0 else 1
        score += load_score * 0.3
        
        performance = self._performance_scores.get(agent, 0.5)
        score += performance * 0.2
        
        priority = context.request.priority
        if priority == "critical":
            senior_roles = ["Tech Lead", "System Architect", "Coordinator"]
            if agent in senior_roles:
                score += 0.2
        
        return score
    
    def update_performance(self, agent: str, score: float):
        """更新 Agent 表现分数"""
        current = self._performance_scores.get(agent, 0.5)
        self._performance_scores[agent] = current * 0.7 + score * 0.3


class RouterService:
    """
    路由服务
    
    统一管理路由策略
    """
    
    def __init__(
        self,
        request_board: Optional[Any] = None,
        default_strategy: RoutingStrategy = RoutingStrategy.SMART,
    ):
        self.request_board = request_board
        self.default_strategy = default_strategy
        
        self._strategies: Dict[RoutingStrategy, RouterStrategy] = {
            RoutingStrategy.ROLE_BASED: RoleBasedRouter(),
            RoutingStrategy.SKILL_BASED: SkillBasedRouter(),
            RoutingStrategy.LOAD_BALANCED: LoadBalancedRouter(),
            RoutingStrategy.PRIORITY_BASED: PriorityBasedRouter(),
            RoutingStrategy.SMART: SmartRouter(),
        }
        
        self._agent_skills: Dict[str, List[str]] = {
            "Product Manager": ["需求分析", "产品规划", "用户研究", "优先级管理"],
            "System Architect": ["架构设计", "技术选型", "性能优化", "系统设计"],
            "Tech Lead": ["技术决策", "代码审查", "团队管理", "技术规划"],
            "Frontend Developer": ["React", "Vue", "CSS", "JavaScript", "UI 开发"],
            "Backend Developer": ["Python", "Java", "数据库", "API 设计", "微服务"],
            "Full Stack Developer": ["React", "Python", "数据库", "API 设计", "DevOps"],
            "QA Engineer": ["测试用例", "自动化测试", "性能测试", "质量保证"],
            "Code Reviewer": ["代码审查", "最佳实践", "重构", "安全审查"],
            "Doc Writer": ["技术文档", "API 文档", "用户手册", "需求文档"],
            "DevOps Engineer": ["CI/CD", "Docker", "Kubernetes", "监控", "自动化"],
            "Security Engineer": ["安全审计", "渗透测试", "安全架构", "合规"],
            "Coordinator": ["协调", "调度", "资源分配", "进度管理"],
        }
        
        self._agent_workloads: Dict[str, int] = {}
    
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
    
    def update_agent_workload(
        self,
        agent_role: str,
        workload: int,
    ):
        """更新 Agent 工作负载"""
        self._agent_workloads[agent_role] = workload
    
    async def route_request(
        self,
        request: Any,
        strategy: Optional[RoutingStrategy] = None,
        available_agents: Optional[List[str]] = None,
    ) -> List[str]:
        """
        路由诉求
        
        Args:
            request: 诉求对象
            strategy: 路由策略（可选）
            available_agents: 可用 Agent 列表（可选）
            
        Returns:
            目标 Agent 列表
        """
        if available_agents is None:
            available_agents = await self._get_available_agents()
        
        context = RoutingContext(
            request=request,
            available_agents=available_agents,
            agent_skills=self._agent_skills,
            agent_workloads=self._agent_workloads.copy(),
            agent_status={},
        )
        
        selected_strategy = strategy or self.default_strategy
        router = self._strategies.get(selected_strategy)
        
        if not router:
            logger.warning(f"Strategy {selected_strategy} not found, using default")
            router = self._strategies[RoutingStrategy.ROLE_BASED]
        
        targets = await router.route(context)
        
        logger.debug(
            f"Routed request to {targets} "
            f"using {router.name} strategy"
        )
        
        return targets
    
    async def _get_available_agents(self) -> List[str]:
        """获取可用 Agent 列表"""
        return list(self._agent_skills.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        return {
            "strategies": list(self._strategies.keys()),
            "agents_registered": len(self._agent_skills),
            "current_workloads": self._agent_workloads.copy(),
        }

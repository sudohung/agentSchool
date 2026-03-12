"""路由服务 (简化版)."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List


class RoutingStrategy(Enum):
    """路由策略"""
    ROLE_BASED = "role_based"
    SKILL_BASED = "skill_based"
    LOAD_BALANCED = "load_balanced"


class RouterService:
    """路由服务 (简化实现)"""
    
    def __init__(self, request_board):
        self.request_board = request_board
        self.default_strategy = RoutingStrategy.ROLE_BASED
    
    async def route_request(self, request, strategy: Optional[RoutingStrategy] = None) -> List[str]:
        """路由诉求"""
        to_agent = request.to_agent
        
        if to_agent == "all":
            return await self._get_all_agents()
        
        return [to_agent]
    
    async def _get_all_agents(self) -> List[str]:
        """获取所有 Agent"""
        return [
            "Product Manager",
            "System Architect",
            "Tech Lead",
            "Frontend Developer",
            "Backend Developer",
            "QA Engineer",
        ]

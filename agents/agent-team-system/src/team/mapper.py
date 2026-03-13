"""角色映射器."""

from __future__ import annotations

from typing import List, Dict, Set
from .config import TaskAnalysis, TaskType, ComplexityLevel
from agent.registry import AgentRegistry


class RoleMapper:
    """
    角色映射器
    
    根据任务分析结果选择合适的 Agent 角色
    
    映射规则:
    1. 核心角色必选 (PM + Tech Lead)
    2. 根据任务类型选择开发角色
    3. 根据复杂度选择质量角色
    4. 根据技术需求选择支持角色
    5. 复杂项目自动添加架构师
    """
    
    # 最大团队规模
    MAX_TEAM_SIZE = 12
    
    # 核心角色 (必选)
    CORE_ROLES = ["Product Manager", "Tech Lead"]
    
    # 任务类型 → 开发角色映射
    TASK_TO_DEVELOPERS = {
        TaskType.WEB_DEVELOPMENT: ["Frontend Developer", "Backend Developer"],
        TaskType.MOBILE_DEVELOPMENT: ["Full Stack Developer"],
        TaskType.API_DEVELOPMENT: ["Backend Developer"],
        TaskType.DATA_ANALYSIS: ["Backend Developer"],
        TaskType.DOCUMENTATION: ["Doc Writer"],
        TaskType.DEVOPS: ["DevOps Engineer"],
        TaskType.SECURITY_AUDIT: ["Security Engineer"],
    }
    
    # 复杂度 → 额外角色
    COMPLEXITY_ROLES = {
        ComplexityLevel.SIMPLE: [],
        ComplexityLevel.MEDIUM: ["QA Engineer"],
        ComplexityLevel.COMPLEX: ["QA Engineer", "Code Reviewer"],
        ComplexityLevel.ENTERPRISE: ["QA Engineer", "Code Reviewer", "Coordinator"],
    }
    
    # 技术需求 → 支持角色
    TECH_TO_SUPPORT = {
        "devops_required": ["DevOps Engineer"],
        "security_required": ["Security Engineer"],
    }
    
    # 角色优先级 (用于裁剪团队规模)
    ROLE_PRIORITY = [
        "Product Manager",
        "Tech Lead",
        "System Architect",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "QA Engineer",
        "Code Reviewer",
        "Coordinator",
        "DevOps Engineer",
        "Security Engineer",
        "Doc Writer",
    ]
    
    def __init__(self):
        """初始化映射器"""
        self.registry = AgentRegistry()
    
    def map(self, analysis: TaskAnalysis) -> List[str]:
        """
        映射角色
        
        Args:
            analysis: 任务分析结果
            
        Returns:
            List[str]: 角色名称列表
            
        Note:
            返回的角色列表会自动去重并限制最大规模
        """
        roles: Set[str] = set()
        
        # 1. 添加核心角色
        roles.update(self.CORE_ROLES)
        
        # 2. 根据任务类型添加开发角色
        developers = self.TASK_TO_DEVELOPERS.get(analysis.task_type, [])
        roles.update(developers)
        
        # 3. 根据复杂度添加质量角色和架构师
        extra_roles = self.COMPLEXITY_ROLES.get(analysis.complexity, [])
        roles.update(extra_roles)
        
        # 复杂项目自动添加架构师
        if analysis.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.ENTERPRISE]:
            roles.add("System Architect")
        
        # 4. 根据技术需求添加支持角色
        for tech_req, support_roles in self.TECH_TO_SUPPORT.items():
            if getattr(analysis, tech_req, False):
                roles.update(support_roles)
        
        # 5. 应用特殊规则
        roles = self._apply_special_rules(roles, analysis)
        
        # 6. 限制团队规模
        if len(roles) > self.MAX_TEAM_SIZE:
            roles = self._prioritize_roles(roles)
        
        return list(roles)
    
    def _apply_special_rules(
        self, 
        roles: Set[str], 
        analysis: TaskAnalysis
    ) -> Set[str]:
        """应用特殊规则"""
        
        # 规则 1: 如果有 Frontend Developer，确保有 Backend Developer
        if "Frontend Developer" in roles and "Backend Developer" not in roles:
            if analysis.task_type != TaskType.MOBILE_DEVELOPMENT:
                roles.add("Backend Developer")
        
        # 规则 2: 如果有 Security Engineer，添加 Code Reviewer
        if "Security Engineer" in roles:
            roles.add("Code Reviewer")
        
        # 规则 3: 企业级项目添加 Coordinator
        if analysis.complexity == ComplexityLevel.ENTERPRISE:
            roles.add("Coordinator")
        
        return roles
    
    def _prioritize_roles(self, roles: Set[str]) -> Set[str]:
        """根据优先级排序并裁剪角色"""
        sorted_roles = sorted(
            roles, 
            key=lambda r: self.ROLE_PRIORITY.index(r) if r in self.ROLE_PRIORITY else 999
        )
        return set(sorted_roles[:self.MAX_TEAM_SIZE])

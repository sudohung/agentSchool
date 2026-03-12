"""Agent 注册表."""

from __future__ import annotations

from typing import Dict, Type, List, Optional


class AgentRegistry:
    """
    Agent 注册表
    
    管理所有可用的 Agent 角色
    """
    
    _registry: Dict[str, Type] = {}
    
    _categories: Dict[str, List[str]] = {
        "core": [],
        "development": [],
        "quality": [],
        "support": [],
    }
    
    @classmethod
    def register(
        cls,
        role_name: str,
        agent_class: Type,
        category: Optional[str] = None,
    ):
        """注册 Agent 角色"""
        cls._registry[role_name] = agent_class
        
        if category and category in cls._categories:
            cls._categories[category].append(role_name)
    
    @classmethod
    def get_role(cls, role_name: str) -> Type:
        """获取角色类"""
        if role_name not in cls._registry:
            raise ValueError(f"Unknown role: {role_name}")
        return cls._registry[role_name]
    
    @classmethod
    def list_roles(cls, category: Optional[str] = None) -> List[str]:
        """列出所有角色"""
        if category:
            return cls._categories.get(category, [])
        return list(cls._registry.keys())
    
    @classmethod
    def get_categories(cls) -> Dict[str, List[str]]:
        """获取所有分类"""
        return cls._categories.copy()

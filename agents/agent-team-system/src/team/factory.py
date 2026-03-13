"""Agent 工厂."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from agent.registry import AgentRegistry


class AgentFactory:
    """
    Agent 工厂
    
    负责创建和配置 Agent 实例
    
    使用全局 AgentRegistry 获取角色类，避免硬编码
    """
    
    # 类级别的注册表引用 (单例)
    _registry = None
    
    def __init__(
        self, 
        document_store=None, 
        request_board=None,
        session=None,
        client=None,
    ):
        """
        初始化工厂
        
        Args:
            document_store: 文档存储实例 (DocumentStore)
            request_board: 诉求看板实例 (RequestBoard)
            session: OpenCode 会话
            client: OpenCode 客户端
        """
        self.document_store = document_store
        self.request_board = request_board
        self.session = session
        self.client = client
        
        # 使用全局注册表
        if AgentFactory._registry is None:
            AgentFactory._registry = AgentRegistry()
        self.registry = AgentFactory._registry
    
    def create_agents(
        self, 
        role_names: List[str],
        config: Optional[Dict] = None,
    ) -> List[Any]:
        """
        批量创建 Agent
        
        Args:
            role_names: 角色名称列表
            config: 可选的额外配置
            
        Returns:
            List[Agent]: Agent 实例列表
            
        Raises:
            ValueError: 角色不存在
        """
        agents = []
        
        for role_name in role_names:
            agent = self.create_agent(role_name, config)
            agents.append(agent)
        
        return agents
    
    def create_agent(
        self, 
        role_name: str,
        config: Optional[Dict] = None,
    ) -> Any:
        """
        创建单个 Agent
        
        Args:
            role_name: 角色名称
            config: 可选的额外配置
            
        Returns:
            Agent: Agent 实例
            
        Raises:
            ValueError: 角色不存在
        """
        # 使用注册表获取角色类
        try:
            agent_class = self.registry.get_role(role_name)
        except ValueError as e:
            raise ValueError(f"Unknown role: {role_name}") from e
        
        # 创建实例
        agent = agent_class(
            session=self.session,
            client=self.client,
        )
        
        # 注入依赖
        if self.document_store:
            agent.document_hub = self.document_store
        if self.request_board:
            agent.request_board = self.request_board
        
        # 应用额外配置
        if config:
            self._apply_config(agent, config)
        
        return agent
    
    def _apply_config(self, agent: Any, config: Dict):
        """应用额外配置"""
        for key, value in config.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

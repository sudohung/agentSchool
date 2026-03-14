"""工作流配置."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from ralph_loop.config import RalphLoopConfig


@dataclass
class WorkflowConfig:
    """
    工作流配置
    
    使用组合模式复用 RalphLoopConfig
    """
    
    # Ralph Loop 配置 (组合)
    ralph_config: RalphLoopConfig = field(default_factory=RalphLoopConfig)
    
    # 工作流特有配置
    quality_passing_score: float = 0.7
    require_manual_review: bool = False
    max_team_size: int = 12
    min_team_size: int = 2
    workflow_timeout: int = 86400  # 24 小时
    delivery_path_base: str = "./deliveries"
    
    # 代理属性 - 便于访问 RalphLoop 配置
    @property
    def max_iterations(self) -> int:
        return self.ralph_config.max_iterations
    
    @property
    def completion_threshold(self) -> float:
        return self.ralph_config.completion_threshold
    
    @property
    def max_setbacks(self) -> int:
        return self.ralph_config.max_setbacks
    
    @property
    def parallel_agents(self) -> bool:
        return self.ralph_config.parallel_agents
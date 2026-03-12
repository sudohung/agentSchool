"""Ralph Loop 配置."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class RalphLoopConfig(BaseModel):
    """Ralph Loop 配置"""
    
    max_iterations: int = 50
    iteration_timeout: int = 3600
    parallel_agents: bool = True
    
    completion_threshold: float = 0.9
    min_iterations: int = 3
    check_interval: int = 5
    
    max_setbacks: int = 20
    setback_cooldown: int = 300
    auto_recovery: bool = True
    
    enable_logging: bool = True
    log_level: str = "INFO"
    save_history: bool = True

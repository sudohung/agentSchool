"""团队配置模型."""

from __future__ import annotations

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import time


class TaskType(Enum):
    """任务类型"""
    WEB_DEVELOPMENT = "web_development"
    MOBILE_DEVELOPMENT = "mobile_development"
    API_DEVELOPMENT = "api_development"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
    SECURITY_AUDIT = "security_audit"
    OTHER = "other"


class ComplexityLevel(Enum):
    """复杂度等级"""
    SIMPLE = "simple"           # 1-2 个角色，1-2 天
    MEDIUM = "medium"           # 3-5 个角色，3-7 天
    COMPLEX = "complex"         # 5+ 角色，1-2 周
    ENTERPRISE = "enterprise"   # 10+ 角色，2 周+


class TaskAnalysis(BaseModel):
    """任务分析结果"""
    
    # 原始输入
    raw_description: str
    
    # 分析结果
    task_type: TaskType
    complexity: ComplexityLevel
    
    # 功能需求
    features: List[str] = Field(default_factory=list)
    
    # 技术需求
    frontend_required: bool = False
    backend_required: bool = False
    database_required: bool = False
    devops_required: bool = False
    security_required: bool = False
    
    # 特殊要求
    special_requirements: List[str] = Field(default_factory=list)
    
    # AI 分析摘要
    ai_summary: Optional[str] = None
    
    # 置信度 (0-1)
    confidence: float = 0.0


@dataclass
class TeamConfig:
    """团队配置"""
    max_team_size: int = 10
    default_complexity: ComplexityLevel = ComplexityLevel.MEDIUM
    enable_ai_analysis: bool = True
    require_manual_approval: bool = False
    storage_base_path: str = "./team_storage"


@dataclass
class TeamContext:
    """团队上下文 - 统一管理共享状态"""
    team_id: str
    task_description: str
    analysis: TaskAnalysis
    config: TeamConfig
    
    # 共享组件
    document_store: Optional[Any] = None
    request_board: Optional[Any] = None
    session: Optional[Any] = None
    client: Optional[Any] = None
    
    # 团队状态
    created_at: int = field(default_factory=lambda: int(time.time()))
    status: str = "initialized"
    iteration_count: int = 0
    agents: List[Any] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.team_id:
            self.team_id = f"team_{int(time.time())}"

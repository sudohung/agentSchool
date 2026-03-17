"""交付系统数据模型."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import time


class DeliveryStatus(Enum):
    """交付状态"""
    PENDING = "pending"
    PREPARING = "preparing"
    QUALITY_CHECKING = "quality_checking"
    PACKAGING = "packaging"
    READY = "ready"
    DELIVERED = "delivered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FEEDBACK = "feedback"


class DeliveryMethod(Enum):
    """交付方式"""
    FILE = "file"
    DIRECTORY = "directory"
    ARCHIVE = "archive"
    GIT = "git"


class QualityLevel(Enum):
    """质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


class DeliveryArtifact(BaseModel):
    """交付物"""
    id: str
    name: str
    type: str
    path: str
    content: Optional[str] = None
    size: int = 0
    hash: Optional[str] = None
    created_at: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QualityCheckResult(BaseModel):
    """质量检查结果"""
    check_name: str
    passed: bool
    score: float
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class DeliveryPackage(BaseModel):
    """交付包"""
    id: str
    name: str
    version: str
    status: DeliveryStatus
    artifacts: List[DeliveryArtifact] = Field(default_factory=list)
    quality_score: float = 0.0
    quality_level: QualityLevel = QualityLevel.ACCEPTABLE
    quality_checks: List[QualityCheckResult] = Field(default_factory=list)
    created_at: int
    delivered_at: Optional[int] = None
    delivery_method: DeliveryMethod = DeliveryMethod.DIRECTORY
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackItem(BaseModel):
    """反馈项"""
    id: str
    type: str
    priority: str
    content: str
    related_artifact: Optional[str] = None
    status: str = "open"
    created_at: int
    resolved_at: Optional[int] = None


class DeliveryReport(BaseModel):
    """交付报告"""
    package_id: str
    project_name: str
    summary: str
    total_artifacts: int
    quality_score: float
    quality_level: QualityLevel
    participating_agents: List[str]
    iterations: int
    total_time: float
    feedback_items: List[FeedbackItem] = Field(default_factory=list)
    generated_at: int

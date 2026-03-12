"""诉求模型."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RequestType(Enum):
    """诉求类型"""
    COLLABORATION = "collaboration"
    INFORMATION = "information"
    REVIEW = "review"
    QUESTION = "question"
    NOTIFICATION = "notification"


class RequestPriority(Enum):
    """诉求优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RequestStatus(Enum):
    """诉求状态"""
    PENDING = "pending"
    RECEIVED = "received"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Request(BaseModel):
    """诉求"""
    id: str
    type: RequestType
    priority: RequestPriority
    status: RequestStatus
    from_agent: str
    to_agent: str
    subject: str
    content: str
    created_at: int
    updated_at: int
    response: Optional[str] = None
    responded_at: Optional[int] = None
    responded_by: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


class RequestResponse(BaseModel):
    """诉求响应"""
    id: str
    request_id: str
    from_agent: str
    content: str
    timestamp: int
    action_taken: Optional[str] = None

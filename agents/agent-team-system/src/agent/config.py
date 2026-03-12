"""Agent 配置和基础模型."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = "idle"              # 空闲
    WORKING = "working"        # 工作中
    WAITING = "waiting"        # 等待诉求/文档
    BLOCKED = "blocked"        # 被阻塞
    DONE = "done"              # 完成


class AgentConfig(BaseModel):
    """Agent 配置"""
    role: str
    expertise: List[str]
    model: Optional[str] = None
    temperature: float = 0.7
    max_iterations: int = 50
    
    class Config:
        arbitrary_types_allowed = True


class DocumentType(Enum):
    """文档类型"""
    PRD = "prd"
    ARCHITECTURE = "architecture"
    TECH_DESIGN = "tech_design"
    API_DESIGN = "api_design"
    CODE = "code"
    TEST_CASE = "test_case"
    TEST_REPORT = "test_report"
    USER_MANUAL = "user_manual"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    """文档元数据"""
    title: str
    doc_type: DocumentType
    author: str
    created_at: int
    updated_at: int
    version: int
    status: str = "draft"
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class DocumentContent(BaseModel):
    """文档内容"""
    content: str
    format: str = "markdown"
    encoding: str = "utf-8"


class Document(BaseModel):
    """文档"""
    id: str
    path: str
    metadata: DocumentMetadata
    content: DocumentContent
    version_history: List[str] = Field(default_factory=list)


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
    
    class Config:
        use_enum_values = True

"""文档模型."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


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
    related_docs: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class DocumentContent(BaseModel):
    """文档内容"""
    content: str
    format: str = "markdown"
    encoding: str = "utf-8"
    language: str = "zh-CN"
    line_count: int = 0
    word_count: int = 0
    hash: Optional[str] = None


class Document(BaseModel):
    """文档"""
    id: str
    path: str
    metadata: DocumentMetadata
    content: DocumentContent
    version_history: List[str] = Field(default_factory=list)

"""权限和问题模型."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PermissionType(Enum):
    """权限类型"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    COMMAND_EXECUTE = "command_execute"
    API_CALL = "api_call"
    EXTERNAL_ACCESS = "external_access"


class PermissionAction(Enum):
    """权限操作"""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class PermissionRequest(BaseModel):
    """权限请求"""
    id: str
    type: PermissionType
    resource: str
    description: str
    requested_by: str
    action: PermissionAction
    remember: bool = False
    
    class Config:
        use_enum_values = True


class PermissionResponse(BaseModel):
    """权限响应"""
    request_id: str
    action: PermissionAction
    reason: Optional[str] = None
    remember: bool = False


class QuestionOption(BaseModel):
    """问题选项"""
    label: str
    description: str
    value: Any = None


class QuestionRequest(BaseModel):
    """问题请求"""
    id: str
    question: str
    header: str
    options: List[QuestionOption]
    multiple: bool = False
    custom: bool = True
    requested_by: str
    
    class Config:
        use_enum_values = True


class QuestionResponse(BaseModel):
    """问题响应"""
    request_id: str
    answers: List[str]
    custom_answer: Optional[str] = None

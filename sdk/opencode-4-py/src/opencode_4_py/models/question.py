"""Question models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class QuestionOption(BaseModel):
    """Question option."""
    label: str
    description: str


class QuestionInfo(BaseModel):
    """Question information."""
    question: str
    header: str
    options: List[QuestionOption]
    multiple: Optional[bool] = None
    custom: Optional[bool] = None


class QuestionToolRef(BaseModel):
    """Question tool reference."""
    message_id: str = Field(..., alias="messageID")
    call_id: str = Field(..., alias="callID")
    
    class Config:
        populate_by_name = True


class QuestionRequest(BaseModel):
    """Question request."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    questions: List[QuestionInfo]
    tool: Optional[QuestionToolRef] = None
    
    class Config:
        populate_by_name = True


class QuestionReplyRequest(BaseModel):
    """Question reply request."""
    answer: List[str]


class QuestionRejectRequest(BaseModel):
    """Question reject request."""
    reason: Optional[str] = None

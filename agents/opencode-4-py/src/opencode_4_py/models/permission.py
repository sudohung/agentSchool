"""Permission models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class PermissionToolRef(BaseModel):
    """Permission tool reference."""
    message_id: str = Field(..., alias="messageID")
    call_id: str = Field(..., alias="callID")
    
    class Config:
        populate_by_name = True


class PermissionRequest(BaseModel):
    """Permission request from AI assistant."""
    id: str = Field(..., pattern="^per.*")
    session_id: str = Field(..., alias="sessionID", pattern="^ses.*")
    permission: str
    patterns: List[str]
    metadata: Dict[str, Any]
    always: List[str] = Field(default_factory=list)
    tool: Optional[PermissionToolRef] = None
    
    class Config:
        populate_by_name = True


class PermissionReplyRequest(BaseModel):
    """Request to reply to a permission request."""
    reply: Literal["once", "always", "reject"]
    message: Optional[str] = None


class PermissionRespondRequest(BaseModel):
    """Request to respond to a permission (deprecated endpoint)."""
    response: Literal["once", "always", "reject"]
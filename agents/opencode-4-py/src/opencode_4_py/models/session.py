"""Session models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union, Dict, Any

from .common import TimeInfo, SessionSummary, ShareInfo, RevertInfo, FileDiff


class Session(BaseModel):
    """Session information."""
    id: str = Field(..., pattern="^ses.*")
    slug: Optional[str] = None
    project_id: str = Field(..., alias="projectID")
    workspace_id: Optional[str] = Field(None, alias="workspaceID")
    directory: str
    parent_id: Optional[str] = Field(None, alias="parentID", pattern="^ses.*")
    summary: Optional[SessionSummary] = None
    share: Optional[ShareInfo] = None
    title: str
    version: str
    time: TimeInfo
    permission: Optional[Dict[str, Any]] = None
    revert: Optional[RevertInfo] = None
    
    class Config:
        populate_by_name = True


class SessionStatusIdle(BaseModel):
    """Session idle status."""
    type: Literal["idle"] = "idle"


class SessionStatusRetry(BaseModel):
    """Session retry status."""
    type: Literal["retry"] = "retry"
    attempt: int
    message: str
    next: int


class SessionStatusBusy(BaseModel):
    """Session busy status."""
    type: Literal["busy"] = "busy"


SessionStatus = Union[SessionStatusIdle, SessionStatusRetry, SessionStatusBusy]


class Todo(BaseModel):
    """Todo item."""
    content: str
    status: Literal["pending", "in_progress", "completed", "cancelled"]
    priority: Literal["high", "medium", "low"]
    id: Optional[str] = None


class PermissionRule(BaseModel):
    """Permission rule."""
    permission: str
    pattern: str
    action: Literal["allow", "deny", "ask"]


PermissionRuleset = List[PermissionRule]


class CreateSessionRequest(BaseModel):
    """Request to create a session."""
    parent_id: Optional[str] = Field(None, alias="parentID", pattern="^ses.*")
    title: Optional[str] = None
    permission: Optional[PermissionRuleset] = None
    
    class Config:
        populate_by_name = True


class UpdateSessionRequest(BaseModel):
    """Request to update a session."""
    title: Optional[str] = None


class SessionListParams(BaseModel):
    """Parameters for listing sessions."""
    directory: Optional[str] = None
    workspace: Optional[str] = None
    roots: Optional[bool] = None
    start: Optional[int] = None
    search: Optional[str] = None
    limit: Optional[int] = None

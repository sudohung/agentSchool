"""Common data models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal, Union
from datetime import datetime


class TimeInfo(BaseModel):
    """Time information for sessions and messages."""
    created: Optional[int] = None
    updated: Optional[int] = None
    completed: Optional[int] = None
    compacting: Optional[int] = None
    archived: Optional[int] = None


class PartTimeInfo(BaseModel):
    """Time information for message parts."""
    start: Optional[int] = None
    end: Optional[int] = None
    created: Optional[int] = None
    compacted: Optional[int] = None


class ModelRef(BaseModel):
    """Model reference."""
    provider_id: str = Field(..., alias="providerID")
    model_id: str = Field(..., alias="modelID")
    
    class Config:
        populate_by_name = True


class PathInfo(BaseModel):
    """Path information."""
    cwd: str
    root: str


class FileDiff(BaseModel):
    """File diff."""
    file: str
    before: str
    after: str
    additions: int
    deletions: int
    status: Optional[Literal["added", "deleted", "modified"]] = None


class SessionSummary(BaseModel):
    """Session summary."""
    additions: int
    deletions: int
    files: int
    diffs: Optional[List[FileDiff]] = None


class ShareInfo(BaseModel):
    """Share information."""
    url: str


class TokenInfo(BaseModel):
    """Token information."""
    total: Optional[int] = None
    input: int
    output: int
    reasoning: Optional[int] = None
    cache: Optional[Dict[str, int]] = None


class RevertInfo(BaseModel):
    """Revert information."""
    message_id: Optional[str] = Field(None, alias="messageID")
    part_id: Optional[str] = Field(None, alias="partID")
    snapshot: Optional[str] = None
    diff: Optional[str] = None
    
    class Config:
        populate_by_name = True

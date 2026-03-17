"""Path and VCS models."""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class AppPath(BaseModel):
    """Application path information."""
    home: str
    state: str
    config: str
    worktree: str
    directory: str


class VcsInfo(BaseModel):
    """Version control system information."""
    branch: Optional[str] = None
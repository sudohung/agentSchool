"""Project models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class ProjectTime(BaseModel):
    """Project time information."""
    created: int
    updated: int
    initialized: Optional[int] = None


class ProjectIcon(BaseModel):
    """Project icon."""
    url: Optional[str] = None
    override: Optional[str] = None
    color: Optional[str] = None


class ProjectCommands(BaseModel):
    """Project commands."""
    start: Optional[str] = None


class Project(BaseModel):
    """Project information."""
    id: str
    worktree: str
    vcs: Optional[Literal["git"]] = None
    name: Optional[str] = None
    icon: Optional[ProjectIcon] = None
    commands: Optional[ProjectCommands] = None
    time: ProjectTime
    sandboxes: List[str] = Field(default_factory=list)


class ProjectUpdateRequest(BaseModel):
    """Request to update project."""
    name: Optional[str] = None
    icon: Optional[ProjectIcon] = None
    commands: Optional[ProjectCommands] = None
"""Command models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class Command(BaseModel):
    """Available command."""
    name: str
    description: Optional[str] = None
    agent: Optional[str] = None
    model: Optional[str] = None
    source: Optional[Literal["command", "mcp", "skill"]] = None
    template: str
    subtask: Optional[bool] = None
    hints: List[str] = Field(default_factory=list)
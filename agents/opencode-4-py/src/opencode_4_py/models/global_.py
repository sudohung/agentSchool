"""Global and Logging models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any


class Health(BaseModel):
    """Health check response."""
    healthy: bool
    version: str


class GlobalEvent(BaseModel):
    """Global event."""
    directory: str
    payload: Dict[str, Any]


class LogEntry(BaseModel):
    """Log entry."""
    service: str
    level: Literal["debug", "info", "warn", "error"]
    message: str
    extra: Optional[Dict[str, Any]] = None

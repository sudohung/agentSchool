"""LSP and Formatter models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class LSPStatus(BaseModel):
    """LSP server status."""
    id: str
    name: str
    root: str
    status: Literal["connected", "error"]


class FormatterStatus(BaseModel):
    """Formatter status."""
    name: str
    extensions: List[str] = Field(default_factory=list)
    enabled: bool = False

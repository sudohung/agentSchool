"""Tool models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ToolIDs(BaseModel):
    """List of tool IDs."""
    root: List[str] = Field(default_factory=list)


class ToolParameter(BaseModel):
    """Tool parameter schema."""
    type: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    required: Optional[List[str]] = None
    items: Optional[Dict[str, Any]] = None


class ToolListItem(BaseModel):
    """Tool list item."""
    id: str
    description: str
    parameters: Dict[str, Any]


ToolList = List[ToolListItem]
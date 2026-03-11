"""MCP Extended models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any


class MCPAuthStartRequest(BaseModel):
    """MCP auth start request."""
    method: Optional[int] = None


class MCPAuthCallbackRequest(BaseModel):
    """MCP auth callback request."""
    code: str
    state: Optional[str] = None


class MCPConnectRequest(BaseModel):
    """MCP connect request."""
    timeout: Optional[int] = None


class MCPAuthResponse(BaseModel):
    """MCP auth response."""
    url: str
    method: Literal["auto", "code"]
    instructions: str

"""MCP (Model Context Protocol) models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any, Union


class McpLocalConfig(BaseModel):
    """MCP local server configuration."""
    type: Literal["local"] = "local"
    command: List[str]
    environment: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None
    timeout: Optional[int] = None


class McpRemoteConfig(BaseModel):
    """MCP remote server configuration."""
    type: Literal["remote"] = "remote"
    url: str
    headers: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None
    timeout: Optional[int] = None
    oauth: Optional[Any] = None


McpConfig = Union[McpLocalConfig, McpRemoteConfig]


class MCPStatusConnected(BaseModel):
    """MCP connected status."""
    status: Literal["connected"] = "connected"


class MCPStatusFailed(BaseModel):
    """MCP failed status."""
    status: Literal["failed"] = "failed"
    error: str


class MCPStatusDisabled(BaseModel):
    """MCP disabled status."""
    status: Literal["disabled"] = "disabled"


class MCPStatusNeedsAuth(BaseModel):
    """MCP needs auth status."""
    status: Literal["needs_auth"] = "needs_auth"


class MCPStatusNeedsClientRegistration(BaseModel):
    """MCP needs client registration status."""
    status: Literal["needs_client_registration"] = "needs_client_registration"


MCPStatus = Union[
    MCPStatusConnected,
    MCPStatusFailed,
    MCPStatusDisabled,
    MCPStatusNeedsAuth,
    MCPStatusNeedsClientRegistration,
]


class MCPAddRequest(BaseModel):
    """Request to add MCP server."""
    name: str
    config: McpConfig

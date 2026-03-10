"""MCP (Model Context Protocol) API implementation."""

from __future__ import annotations

from typing import Optional, Dict, Any, Union

from ..utils.http import HTTPClient
from ..models.mcp import (
    MCPStatusConnected,
    MCPStatusFailed,
    MCPStatusDisabled,
    MCPStatusNeedsAuth,
    MCPStatusNeedsClientRegistration,
    MCPAddRequest,
    McpConfig,
)


MCPStatus = Union[
    MCPStatusConnected,
    MCPStatusFailed,
    MCPStatusDisabled,
    MCPStatusNeedsAuth,
    MCPStatusNeedsClientRegistration,
]


def _parse_mcp_status(data: Dict[str, Any]) -> MCPStatus:
    """Parse MCP status based on status field."""
    status = data.get("status")
    if status == "connected":
        return MCPStatusConnected(**data)
    elif status == "failed":
        return MCPStatusFailed(**data)
    elif status == "disabled":
        return MCPStatusDisabled(**data)
    elif status == "needs_auth":
        return MCPStatusNeedsAuth(**data)
    elif status == "needs_client_registration":
        return MCPStatusNeedsClientRegistration(**data)
    else:
        return MCPStatusFailed(status="failed", error=f"Unknown status: {status}")


class MCPAPI:
    """MCP API client."""
    
    def __init__(
        self,
        http_client: HTTPClient,
        directory: Optional[str] = None,
        workspace: Optional[str] = None,
    ):
        self.http = http_client
        self.directory = directory
        self.workspace = workspace
    
    def _get_params(self) -> Dict[str, Any]:
        """Get default query parameters."""
        params = {}
        if self.directory:
            params["directory"] = self.directory
        if self.workspace:
            params["workspace"] = self.workspace
        return params
    
    def status(self) -> Dict[str, MCPStatus]:
        """Get status of all MCP servers.
        
        Returns:
            Dictionary mapping server names to their statuses.
        """
        response = self.http.get("/mcp", params=self._get_params())
        data = response.json()
        return {name: _parse_mcp_status(status) for name, status in data.items()}
    
    def add(self, name: str, config: McpConfig) -> Dict[str, MCPStatus]:
        """Add a new MCP server.
        
        Args:
            name: Server name.
            config: Server configuration (local or remote).
            
        Returns:
            Updated MCP server statuses.
        """
        request = MCPAddRequest(name=name, config=config)
        response = self.http.post(
            "/mcp",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        data = response.json()
        return {name: _parse_mcp_status(status) for name, status in data.items()}

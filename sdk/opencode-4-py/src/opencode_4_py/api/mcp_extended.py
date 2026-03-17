"""MCP Extended API implementation."""

from __future__ import annotations

from typing import Optional, Dict, Any

from ..utils.http import HTTPClient
from ..models.mcp_extended import (
    MCPAuthStartRequest,
    MCPAuthCallbackRequest,
    MCPConnectRequest,
    MCPAuthResponse,
)


class MCPExtendedAPI:
    """MCP Extended API client."""
    
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
    
    def auth_start(self, name: str, method: Optional[int] = None) -> MCPAuthResponse:
        """Start MCP OAuth authentication.
        
        Args:
            name: MCP server name.
            method: Auth method index.
            
        Returns:
            Authorization URL and instructions.
        """
        request = MCPAuthStartRequest(method=method)
        response = self.http.post(
            f"/mcp/{name}/auth",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        data = response.json()
        return MCPAuthResponse(**data)
    
    def auth_remove(self, name: str) -> bool:
        """Remove MCP OAuth authentication.
        
        Args:
            name: MCP server name.
            
        Returns:
            True if auth was removed successfully.
        """
        response = self.http.delete(
            f"/mcp/{name}/auth",
            params=self._get_params(),
        )
        return response.json()
    
    def auth_callback(
        self,
        name: str,
        code: str,
        state: Optional[str] = None,
    ) -> bool:
        """Handle MCP OAuth callback.
        
        Args:
            name: MCP server name.
            code: OAuth authorization code.
            state: OAuth state parameter.
            
        Returns:
            True if callback was processed successfully.
        """
        request = MCPAuthCallbackRequest(code=code, state=state)
        response = self.http.post(
            f"/mcp/{name}/auth/callback",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        return response.json()
    
    def connect(self, name: str, timeout: Optional[int] = None) -> bool:
        """Connect to MCP server.
        
        Args:
            name: MCP server name.
            timeout: Connection timeout in milliseconds.
            
        Returns:
            True if connection was successful.
        """
        request = MCPConnectRequest(timeout=timeout)
        response = self.http.post(
            f"/mcp/{name}/connect",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        return response.json()
    
    def disconnect(self, name: str) -> bool:
        """Disconnect from MCP server.
        
        Args:
            name: MCP server name.
            
        Returns:
            True if disconnection was successful.
        """
        response = self.http.post(
            f"/mcp/{name}/disconnect",
            params=self._get_params(),
        )
        return response.json()

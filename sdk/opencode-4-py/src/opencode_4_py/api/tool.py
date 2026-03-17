"""Tool API implementation (Experimental)."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from ..utils.http import HTTPClient
from ..models.tool import ToolIDs, ToolListItem, ToolList


class ToolAPI:
    """Tool API client (Experimental)."""
    
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
    
    def list_ids(self) -> List[str]:
        """List all tool IDs.
        
        Returns:
            List of tool IDs.
        """
        response = self.http.get(
            "/experimental/tool/ids",
            params=self._get_params(),
        )
        data = response.json()
        return data
    
    def list(
        self,
        provider: str,
        model: str,
    ) -> ToolList:
        """List tools with JSON schemas for a model.
        
        Args:
            provider: Provider ID (e.g., "anthropic").
            model: Model ID (e.g., "claude-3-5-sonnet").
            
        Returns:
            List of tools with their schemas.
        """
        params = self._get_params()
        params["provider"] = provider
        params["model"] = model
        
        response = self.http.get(
            "/experimental/tool",
            params=params,
        )
        data = response.json()
        return [ToolListItem(**item) for item in data]
"""Agent API implementation."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from ..utils.http import HTTPClient
from ..models.agent import Agent


class AgentAPI:
    """Agent API client."""
    
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
    
    def list(self) -> List[Agent]:
        """List all available agents.
        
        Returns:
            List of available AI agents.
        """
        response = self.http.get("/agent", params=self._get_params())
        data = response.json()
        return [Agent(**item) for item in data]

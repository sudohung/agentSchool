"""Instance API implementation."""

from __future__ import annotations

from typing import Optional, Dict, Any

from ..utils.http import HTTPClient


class InstanceAPI:
    """Instance API client."""
    
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
    
    def dispose(self) -> bool:
        """Dispose the current instance.
        
        Clean up and dispose the current OpenCode instance,
        releasing all resources.
        
        Returns:
            True if instance was disposed successfully.
        """
        response = self.http.post("/instance/dispose", params=self._get_params())
        return response.json()
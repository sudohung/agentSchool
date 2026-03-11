"""LSP and Formatter API implementation."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from ..utils.http import HTTPClient
from ..models.lsp import LSPStatus, FormatterStatus


class LSPAPI:
    """LSP API client."""
    
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
    
    def status(self) -> List[LSPStatus]:
        """Get LSP server status.
        
        Returns:
            List of LSP server statuses.
        """
        response = self.http.get("/lsp", params=self._get_params())
        data = response.json()
        return [LSPStatus(**item) for item in data]


class FormatterAPI:
    """Formatter API client."""
    
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
    
    def status(self) -> List[FormatterStatus]:
        """Get formatter status.
        
        Returns:
            List of formatter statuses.
        """
        response = self.http.get("/formatter", params=self._get_params())
        data = response.json()
        return [FormatterStatus(**item) for item in data]

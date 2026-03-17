"""Path and VCS API implementation."""

from __future__ import annotations

from typing import Optional, Dict, Any

from ..utils.http import HTTPClient
from ..models.path import AppPath, VcsInfo


class PathAPI:
    """Path API client."""
    
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
    
    def get(self) -> AppPath:
        """Get path information.
        
        Returns:
            Path information including home, state, config, worktree, and directory.
        """
        response = self.http.get("/path", params=self._get_params())
        data = response.json()
        return AppPath(**data)


class VcsAPI:
    """VCS (Version Control System) API client."""
    
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
    
    def get(self) -> VcsInfo:
        """Get VCS information.
        
        Returns:
            VCS information including current branch.
        """
        response = self.http.get("/vcs", params=self._get_params())
        data = response.json()
        return VcsInfo(**data)
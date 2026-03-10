"""File API implementation."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from ..utils.http import HTTPClient
from ..models.file import (
    FileNode,
    FileContent,
    FileStatus,
    Symbol,
    TextSearchMatch,
)


class FileAPI:
    """File API client."""
    
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
    
    def list(self, path: str = ".") -> List[FileNode]:
        """List files and directories.
        
        Args:
            path: Directory path to list (default: current directory).
            
        Returns:
            List of file and directory nodes.
        """
        params = self._get_params()
        params["path"] = path
        
        response = self.http.get("/file", params=params)
        data = response.json()
        return [FileNode(**item) for item in data]
    
    def read(self, path: str) -> FileContent:
        """Read file content.
        
        Args:
            path: File path to read.
            
        Returns:
            File content object.
        """
        params = self._get_params()
        params["path"] = path
        
        response = self.http.get("/file/content", params=params)
        data = response.json()
        return FileContent(**data)
    
    def status(self) -> List[FileStatus]:
        """Get Git file status.
        
        Returns:
            List of files with their Git status.
        """
        response = self.http.get("/file/status", params=self._get_params())
        data = response.json()
        return [FileStatus(**item) for item in data]
    
    def search_text(
        self,
        pattern: str,
        path: Optional[str] = None,
    ) -> List[TextSearchMatch]:
        """Search for text in files.
        
        Args:
            pattern: Regex pattern to search for.
            path: Optional path to limit search scope.
            
        Returns:
            List of text search matches.
        """
        params = self._get_params()
        params["pattern"] = pattern
        if path:
            params["path"] = path
        
        response = self.http.get("/find", params=params)
        data = response.json()
        return [TextSearchMatch(**item) for item in data]
    
    def find_files(
        self,
        query: str,
        type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[str]:
        """Find files by name.
        
        Args:
            query: Search query (fuzzy match).
            type: Filter by "file" or "directory".
            limit: Maximum results (1-200).
            
        Returns:
            List of file paths.
        """
        params = self._get_params()
        params["query"] = query
        if type:
            params["type"] = type
        if limit:
            params["limit"] = limit
        
        response = self.http.get("/find/file", params=params)
        return response.json()
    
    def find_symbols(self, query: str) -> List[Symbol]:
        """Find workspace symbols.
        
        Args:
            query: Symbol name query.
            
        Returns:
            List of symbols.
        """
        params = self._get_params()
        params["query"] = query
        
        response = self.http.get("/find/symbol", params=params)
        data = response.json()
        return [Symbol(**item) for item in data]
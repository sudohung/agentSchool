"""Project API implementation."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from ..utils.http import HTTPClient
from ..models.project import Project, ProjectUpdateRequest


class ProjectAPI:
    """Project API client."""
    
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
    
    def list(self) -> List[Project]:
        """List all projects.
        
        Returns:
            List of projects that have been opened with OpenCode.
        """
        response = self.http.get("/project", params=self._get_params())
        data = response.json()
        return [Project(**item) for item in data]
    
    def current(self) -> Project:
        """Get current project.
        
        Returns:
            The currently active project.
        """
        response = self.http.get("/project/current", params=self._get_params())
        data = response.json()
        return Project(**data)
    
    def update(
        self,
        project_id: str,
        name: Optional[str] = None,
        icon: Optional[Dict[str, Any]] = None,
        commands: Optional[Dict[str, Any]] = None,
    ) -> Project:
        """Update project properties.
        
        Args:
            project_id: Project ID.
            name: New project name.
            icon: Icon configuration.
            commands: Commands configuration.
            
        Returns:
            Updated project information.
        """
        request = ProjectUpdateRequest(
            name=name,
            icon=icon,
            commands=commands,
        )
        response = self.http.patch(
            f"/project/{project_id}",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        data = response.json()
        return Project(**data)
    
    def init_git(self) -> Project:
        """Initialize git repository for the current project.
        
        Returns:
            Project information after git initialization.
        """
        response = self.http.post("/project/git/init", params=self._get_params())
        data = response.json()
        return Project(**data)
"""Session API implementation."""

from __future__ import annotations

from typing import Optional, List, Dict, Any
import json

from ..utils.http import HTTPClient
from ..models.session import (
    Session,
    SessionStatus,
    Todo,
    CreateSessionRequest,
    UpdateSessionRequest,
    SessionListParams,
)
from ..models.common import FileDiff


class SessionAPI:
    """Session API client."""
    
    def __init__(self, http_client: HTTPClient, directory: Optional[str] = None):
        self.http = http_client
        self.directory = directory
    
    def _get_params(self) -> Dict[str, Any]:
        """Get default query parameters."""
        params = {}
        if self.directory:
            params["directory"] = self.directory
        return params
    
    def list(
        self,
        workspace: Optional[str] = None,
        roots: Optional[bool] = None,
        start: Optional[int] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Session]:
        """List all sessions."""
        params = self._get_params()
        if workspace:
            params["workspace"] = workspace
        if roots is not None:
            params["roots"] = roots
        if start is not None:
            params["start"] = start
        if search:
            params["search"] = search
        if limit is not None:
            params["limit"] = limit
        
        response = self.http.get("/session", params=params)
        data = response.json()
        return [Session(**item) for item in data]
    
    def get(self, session_id: str) -> Session:
        """Get a session by ID."""
        response = self.http.get(f"/session/{session_id}", params=self._get_params())
        data = response.json()
        return Session(**data)
    
    def create(
        self,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        permission: Optional[List[Dict[str, Any]]] = None,
    ) -> Session:
        """Create a new session."""
        request = CreateSessionRequest(
            parent_id=parent_id,
            title=title,
            permission=permission,
        )
        response = self.http.post("/session", json=request.model_dump(by_alias=True, exclude_none=True))
        data = response.json()
        return Session(**data)
    
    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        response = self.http.delete(f"/session/{session_id}")
        return response.json()
    
    def update(self, session_id: str, title: str) -> Session:
        """Update a session."""
        request = UpdateSessionRequest(title=title)
        response = self.http.patch(
            f"/session/{session_id}",
            json=request.model_dump(by_alias=True, exclude_none=True),
        )
        data = response.json()
        return Session(**data)
    
    def status(self) -> Dict[str, SessionStatus]:
        """Get status for all sessions."""
        response = self.http.get("/session/status", params=self._get_params())
        return response.json()
    
    def children(self, session_id: str) -> List[Session]:
        """Get child sessions."""
        response = self.http.get(f"/session/{session_id}/children", params=self._get_params())
        data = response.json()
        return [Session(**item) for item in data]
    
    def todos(self, session_id: str) -> List[Todo]:
        """Get todos for a session."""
        response = self.http.get(f"/session/{session_id}/todo", params=self._get_params())
        data = response.json()
        return [Todo(**item) for item in data]
    
    def abort(self, session_id: str) -> bool:
        """Abort a running session."""
        response = self.http.post(f"/session/{session_id}/abort", params=self._get_params())
        return response.json()
    
    def share(self, session_id: str) -> Session:
        """Share a session."""
        response = self.http.post(f"/session/{session_id}/share", params=self._get_params())
        data = response.json()
        return Session(**data)
    
    def unshare(self, session_id: str) -> Session:
        """Unshare a session."""
        response = self.http.delete(f"/session/{session_id}/share")
        data = response.json()
        return Session(**data)
    
    def fork(self, session_id: str, message_id: Optional[str] = None) -> Session:
        """Fork a session at a message."""
        body = {"messageID": message_id} if message_id else {}
        response = self.http.post(
            f"/session/{session_id}/fork",
            json=body,
            params=self._get_params(),
        )
        data = response.json()
        return Session(**data)
    
    def diff(self, session_id: str, message_id: Optional[str] = None) -> List[FileDiff]:
        """Get diff for a session."""
        params = self._get_params()
        if message_id:
            params["messageID"] = message_id
        
        response = self.http.get(f"/session/{session_id}/diff", params=params)
        data = response.json()
        return [FileDiff(**item) for item in data]
    
    def summarize(
        self,
        session_id: str,
        provider_id: str,
        model_id: str,
    ) -> bool:
        """Summarize a session."""
        body = {
            "providerID": provider_id,
            "modelID": model_id,
        }
        response = self.http.post(
            f"/session/{session_id}/summarize",
            json=body,
            params=self._get_params(),
        )
        return response.json()
    
    def revert(
        self,
        session_id: str,
        message_id: str,
        part_id: Optional[str] = None,
    ) -> bool:
        """Revert a message."""
        body = {
            "messageID": message_id,
            "partID": part_id,
        }
        response = self.http.post(
            f"/session/{session_id}/revert",
            json=body,
            params=self._get_params(),
        )
        return response.json()
    
    def unrevert(self, session_id: str) -> bool:
        """Unrevert reverted messages."""
        response = self.http.post(
            f"/session/{session_id}/unrevert",
            params=self._get_params(),
        )
        return response.json()
    
    def init(
        self,
        session_id: str,
        message_id: str,
        provider_id: str,
        model_id: str,
    ) -> bool:
        """Initialize session (create AGENTS.md)."""
        body = {
            "messageID": message_id,
            "providerID": provider_id,
            "modelID": model_id,
        }
        response = self.http.post(
            f"/session/{session_id}/init",
            json=body,
            params=self._get_params(),
        )
        return response.json()

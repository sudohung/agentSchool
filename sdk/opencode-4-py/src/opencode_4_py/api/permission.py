"""Permission API implementation."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from ..utils.http import HTTPClient
from ..models.permission import (
    PermissionRequest,
    PermissionReplyRequest,
    PermissionRespondRequest,
)


class PermissionAPI:
    """Permission API client."""

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

    def list(self) -> List[PermissionRequest]:
        """List pending permission requests.

        Get all pending permission requests across all sessions.

        Returns:
            List of pending permission requests.
        """
        response = self.http.get("/permission", params=self._get_params())
        data = response.json()
        return [PermissionRequest(**item) for item in data]

    def reply(
        self,
        request_id: str,
        reply: str,
        message: Optional[str] = None,
    ) -> bool:
        """Reply to a permission request.

        Approve or deny a permission request from the AI assistant.

        Args:
            request_id: Permission request ID (starts with 'per_').
            reply: Response type - 'once', 'always', or 'reject'.
            message: Optional message explaining the decision.

        Returns:
            True if permission was processed successfully.
        """
        request = PermissionReplyRequest(reply=reply, message=message)
        response = self.http.post(
            f"/permission/{request_id}/reply",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        return response.json()

    def respond(
        self,
        session_id: str,
        permission_id: str,
        response: str,
    ) -> bool:
        """Respond to a permission (deprecated endpoint).

        This endpoint is deprecated. Use reply() instead.

        Args:
            session_id: Session ID.
            permission_id: Permission ID.
            response: Response type - 'once', 'always', or 'reject'.

        Returns:
            True if permission was processed successfully.
        """
        request = PermissionRespondRequest(response=response)
        response = self.http.post(
            f"/session/{session_id}/permissions/{permission_id}",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        return response.json()
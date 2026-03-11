"""Question API implementation."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from ..utils.http import HTTPClient
from ..models.question import (
    QuestionRequest,
    QuestionReplyRequest,
    QuestionRejectRequest,
)


class QuestionAPI:
    """Question API client."""
    
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
    
    def list(self) -> List[QuestionRequest]:
        """List pending questions.
        
        Returns:
            List of pending questions.
        """
        response = self.http.get("/question", params=self._get_params())
        data = response.json()
        return [QuestionRequest(**item) for item in data]
    
    def reply(self, request_id: str, answer: List[str]) -> bool:
        """Reply to a question.
        
        Args:
            request_id: Question request ID.
            answer: List of selected answers.
            
        Returns:
            True if reply was successful.
        """
        request = QuestionReplyRequest(answer=answer)
        response = self.http.post(
            f"/question/{request_id}/reply",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        return response.json()
    
    def reject(self, request_id: str, reason: Optional[str] = None) -> bool:
        """Reject a question.
        
        Args:
            request_id: Question request ID.
            reason: Optional rejection reason.
            
        Returns:
            True if rejection was successful.
        """
        request = QuestionRejectRequest(reason=reason)
        response = self.http.post(
            f"/question/{request_id}/reject",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        return response.json()

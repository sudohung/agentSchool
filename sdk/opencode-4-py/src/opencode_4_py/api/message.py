"""Message API implementation."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from ..utils.http import HTTPClient
from ..models.message import (
    MessageWithParts,
    PartInput,
    TextPartInput,
    SendMessageRequest,
    CommandRequest,
    ShellRequest,
    ModelRef,
)


class MessageAPI:
    """Message API client."""
    
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
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[MessageWithParts]:
        """List messages in a session."""
        params = self._get_params()
        if limit is not None:
            params["limit"] = limit
        
        response = self.http.get(
            f"/session/{session_id}/message",
            params=params,
        )
        data = response.json()
        return [MessageWithParts(**item) for item in data]
    
    def get(self, session_id: str, message_id: str) -> MessageWithParts:
        """Get a message by ID."""
        response = self.http.get(
            f"/session/{session_id}/message/{message_id}",
            params=self._get_params(),
        )
        data = response.json()
        return MessageWithParts(**data)
    
    def send(
        self,
        session_id: str,
        parts: List[PartInput],
        model: Optional[ModelRef] = None,
        agent: Optional[str] = None,
        system: Optional[str] = None,
        no_reply: bool = False,
        format: Optional[Dict[str, Any]] = None,
    ) -> MessageWithParts:
        """Send a message and wait for response."""
        request = SendMessageRequest(
            model=model,
            agent=agent,
            no_reply=no_reply,
            format=format,
            system=system,
            parts=parts,
        )
        response = self.http.post(
            f"/session/{session_id}/message",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        data = response.json()
        return MessageWithParts(**data)
    
    def send_text(
        self,
        session_id: str,
        text: str,
        model: Optional[ModelRef] = None,
        agent: Optional[str] = None,
        system: Optional[str] = None,
        no_reply: bool = False,
    ) -> MessageWithParts:
        """Send a text message."""
        part = TextPartInput(text=text)
        return self.send(
            session_id=session_id,
            parts=[part],
            model=model,
            agent=agent,
            system=system,
            no_reply=no_reply,
        )
    
    def send_async(
        self,
        session_id: str,
        parts: List[PartInput],
        model: Optional[ModelRef] = None,
        agent: Optional[str] = None,
        system: Optional[str] = None,
    ) -> None:
        """Send a message asynchronously (no wait)."""
        request = SendMessageRequest(
            model=model,
            agent=agent,
            system=system,
            parts=parts,
        )
        self.http.post(
            f"/session/{session_id}/prompt_async",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
    
    def command(
        self,
        session_id: str,
        command: str,
        arguments: Optional[str] = None,
        model: Optional[ModelRef] = None,
        agent: Optional[str] = None,
    ) -> MessageWithParts:
        """Execute a slash command."""
        request = CommandRequest(
            command=command,
            arguments=arguments,
            model=model,
            agent=agent,
        )
        response = self.http.post(
            f"/session/{session_id}/command",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        data = response.json()
        return MessageWithParts(**data)
    
    def shell(
        self,
        session_id: str,
        command: str,
        model: Optional[ModelRef] = None,
        agent: str = "build",
    ) -> MessageWithParts:
        """Run a shell command."""
        request = ShellRequest(
            command=command,
            model=model,
            agent=agent,
        )
        response = self.http.post(
            f"/session/{session_id}/shell",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        data = response.json()
        return MessageWithParts(**data)
    
    def delete(self, session_id: str, message_id: str) -> bool:
        """Delete a message."""
        response = self.http.delete(
            f"/session/{session_id}/message/{message_id}",
        )
        return response.json()

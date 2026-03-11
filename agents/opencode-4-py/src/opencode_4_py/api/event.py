"""Event API implementation for SSE streaming."""

from __future__ import annotations

from typing import Optional, Dict, Any, Iterator, AsyncIterator, Literal
import json

from ..utils.http import HTTPClient, AsyncHTTPClient
from ..models.event import Event, GlobalEvent


class EventAPI:
    """Event API client for SSE streaming."""
    
    def __init__(self, http_client: HTTPClient, directory: Optional[str] = None):
        self.http = http_client
        self.directory = directory
    
    def _get_params(self) -> Dict[str, Any]:
        """Get default query parameters."""
        params = {}
        if self.directory:
            params["directory"] = self.directory
        return params
    
    def subscribe_global(self) -> Iterator[GlobalEvent]:
        """Subscribe to global events (SSE stream)."""
        for data in self.http.stream_sse("/global/event"):
            yield GlobalEvent(**data)
    
    def subscribe(self) -> Iterator[Event]:
        """Subscribe to project events (SSE stream)."""
        for data in self.http.stream_sse("/event", params=self._get_params()):
            yield self._parse_event(data)
    
    def _parse_event(self, data: Dict[str, Any]) -> Event:
        """Parse event data into appropriate event type."""
        event_type = data.get("type", "")
        
        from ..models.event import (
            EventSessionCreated,
            EventSessionUpdated,
            EventSessionDeleted,
            EventSessionStatus,
            EventMessageUpdated,
            EventMessagePartUpdated,
            EventFileEdited,
            EventTodoUpdated,
            EventServerConnected,
        )
        
        event_classes = {
            "session.created": EventSessionCreated,
            "session.updated": EventSessionUpdated,
            "session.deleted": EventSessionDeleted,
            "session.status": EventSessionStatus,
            "message.updated": EventMessageUpdated,
            "message.part.updated": EventMessagePartUpdated,
            "file.edited": EventFileEdited,
            "todo.updated": EventTodoUpdated,
            "server.connected": EventServerConnected,
        }
        
        event_class = event_classes.get(event_type)
        if event_class:
            return event_class(**data)
        
        return EventSessionUpdated(**data)


class AsyncEventAPI:
    """Async Event API client for SSE streaming."""
    
    def __init__(self, http_client: AsyncHTTPClient, directory: Optional[str] = None):
        self.http = http_client
        self.directory = directory
    
    def _get_params(self) -> Dict[str, Any]:
        """Get default query parameters."""
        params = {}
        if self.directory:
            params["directory"] = self.directory
        return params
    
    async def subscribe_global(self) -> AsyncIterator[GlobalEvent]:
        """Subscribe to global events (SSE stream)."""
        async for data in self.http.stream_sse("/global/event"):
            yield GlobalEvent(**data)
    
    async def subscribe(self) -> AsyncIterator[Event]:
        """Subscribe to project events (SSE stream)."""
        async for data in self.http.stream_sse("/event", params=self._get_params()):
            yield self._parse_event(data)
    
    def _parse_event(self, data: Dict[str, Any]) -> Event:
        """Parse event data into appropriate event type."""
        event_type = data.get("type", "")
        
        from ..models.event import (
            EventSessionCreated,
            EventSessionUpdated,
            EventSessionDeleted,
            EventSessionStatus,
            EventMessageUpdated,
            EventMessagePartUpdated,
            EventFileEdited,
            EventTodoUpdated,
            EventServerConnected,
        )
        
        event_classes = {
            "session.created": EventSessionCreated,
            "session.updated": EventSessionUpdated,
            "session.deleted": EventSessionDeleted,
            "session.status": EventSessionStatus,
            "message.updated": EventMessageUpdated,
            "message.part.updated": EventMessagePartUpdated,
            "file.edited": EventFileEdited,
            "todo.updated": EventTodoUpdated,
            "server.connected": EventServerConnected,
        }
        
        event_class = event_classes.get(event_type)
        if event_class:
            return event_class(**data)
        
        return EventSessionUpdated(**data)

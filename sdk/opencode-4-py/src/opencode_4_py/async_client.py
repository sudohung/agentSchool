"""OpenCode asynchronous client."""

from __future__ import annotations

from typing import Optional

from .config import ClientConfig
from .utils.http import AsyncHTTPClient
from .api.session import SessionAPI
from .api.message import MessageAPI
from .api.event import AsyncEventAPI
from .errors import ConnectionError


class AsyncOpenCodeClient:
    """Asynchronous OpenCode client."""
    
    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize async OpenCode client.
        
        Args:
            config: Client configuration. Uses defaults if not provided.
        """
        self.config = config or ClientConfig()
        
        try:
            self.http = AsyncHTTPClient(
                base_url=self.config.base_url,
                username=self.config.username,
                password=self.config.password,
                timeout=self.config.timeout,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.config.base_url}: {e}")
        
        self._session_api: Optional[SessionAPI] = None
        self._message_api: Optional[MessageAPI] = None
        self._event_api: Optional[AsyncEventAPI] = None
    
    @property
    def session(self) -> SessionAPI:
        """Session API."""
        if self._session_api is None:
            self._session_api = SessionAPI(self.http, self.config.directory)
        return self._session_api
    
    @property
    def message(self) -> MessageAPI:
        """Message API."""
        if self._message_api is None:
            self._message_api = MessageAPI(self.http, self.config.directory)
        return self._message_api
    
    @property
    def event(self) -> AsyncEventAPI:
        """Event API (async)."""
        if self._event_api is None:
            self._event_api = AsyncEventAPI(self.http, self.config.directory)
        return self._event_api
    
    async def health_check(self) -> dict:
        """Check server health.
        
        Returns:
            Health status dict with 'healthy' and 'version' fields.
        """
        response = await self.http.get("/global/health")
        return response.json()
    
    async def close(self) -> None:
        """Close the client connection."""
        await self.http.close()
    
    async def __aenter__(self) -> "AsyncOpenCodeClient":
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.close()

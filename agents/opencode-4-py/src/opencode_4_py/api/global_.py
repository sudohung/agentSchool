"""Global and Logging API implementation."""

from __future__ import annotations

from typing import Optional, Dict, Any, Iterator

from ..utils.http import HTTPClient
from ..models.global_ import Health, GlobalEvent, LogEntry


class GlobalAPI:
    """Global API client."""
    
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
    
    def health(self) -> Health:
        """Check server health.
        
        Returns:
            Health status with version information.
        """
        response = self.http.get("/global/health")
        data = response.json()
        return Health(**data)
    
    def event(self) -> Iterator[GlobalEvent]:
        """Subscribe to global events (SSE stream).
        
        Yields:
            Global events as they occur.
        """
        for data in self.http.stream_sse("/global/event", params=self._get_params()):
            yield GlobalEvent(**data)
    
    def config_get(self) -> Dict[str, Any]:
        """Get global configuration.
        
        Returns:
            Global configuration settings.
        """
        response = self.http.get("/global/config", params=self._get_params())
        return response.json()
    
    def config_update(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update global configuration.
        
        Args:
            config: Configuration update.
            
        Returns:
            Updated configuration.
        """
        response = self.http.patch(
            "/global/config",
            json=config,
            params=self._get_params(),
        )
        return response.json()
    
    def dispose(self) -> bool:
        """Dispose all instances.
        
        Clean up and dispose all OpenCode instances,
        releasing all resources.
        
        Returns:
            True if disposal was successful.
        """
        response = self.http.post("/global/dispose", params=self._get_params())
        return response.json()


class LoggingAPI:
    """Logging API client."""
    
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
    
    def log(self, entry: LogEntry) -> bool:
        """Write a log entry.
        
        Args:
            entry: Log entry to write.
            
        Returns:
            True if log was written successfully.
        """
        response = self.http.post(
            "/log",
            json=entry.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        return response.json()
    
    def log_message(
        self,
        level: str,
        message: str,
        service: str = "opencode-sdk",
        extra: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Write a simple log message.
        
        Args:
            level: Log level (debug, info, warn, error).
            message: Log message.
            service: Service name (default: opencode-sdk).
            extra: Optional additional data.
            
        Returns:
            True if log was written successfully.
        """
        entry = LogEntry(service=service, level=level, message=message, extra=extra)
        return self.log(entry)

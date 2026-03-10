"""OpenCode synchronous client."""

from __future__ import annotations

from typing import Optional

from .config import ClientConfig
from .utils.http import HTTPClient
from .api.session import SessionAPI
from .api.message import MessageAPI
from .api.event import EventAPI
from .api.command import CommandAPI
from .api.file import FileAPI
from .api.tool import ToolAPI
from .api.lsp import LSPAPI, FormatterAPI
from .api.mcp import MCPAPI
from .api.agent import AgentAPI
from .api.project import ProjectAPI
from .api.path import PathAPI, VcsAPI
from .errors import ConnectionError, APIError


class OpenCodeClient:
    """Synchronous OpenCode client."""
    
    def __init__(self, config: Optional[ClientConfig] = None):
        """Initialize OpenCode client.
        
        Args:
            config: Client configuration. Uses defaults if not provided.
        """
        self.config = config or ClientConfig()
        
        try:
            self.http = HTTPClient(
                base_url=self.config.base_url,
                username=self.config.username,
                password=self.config.password,
                timeout=self.config.timeout,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.config.base_url}: {e}")
        
        self._session_api: Optional[SessionAPI] = None
        self._message_api: Optional[MessageAPI] = None
        self._event_api: Optional[EventAPI] = None
        self._command_api: Optional[CommandAPI] = None
        self._file_api: Optional[FileAPI] = None
        self._tool_api: Optional[ToolAPI] = None
        self._lsp_api: Optional[LSPAPI] = None
        self._formatter_api: Optional[FormatterAPI] = None
        self._mcp_api: Optional[MCPAPI] = None
        self._agent_api: Optional[AgentAPI] = None
        self._project_api: Optional[ProjectAPI] = None
        self._path_api: Optional[PathAPI] = None
        self._vcs_api: Optional[VcsAPI] = None
    
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
    def event(self) -> EventAPI:
        """Event API."""
        if self._event_api is None:
            self._event_api = EventAPI(self.http, self.config.directory)
        return self._event_api
    
    @property
    def command(self) -> CommandAPI:
        """Command API."""
        if self._command_api is None:
            self._command_api = CommandAPI(self.http, self.config.directory)
        return self._command_api
    
    @property
    def file(self) -> FileAPI:
        """File API."""
        if self._file_api is None:
            self._file_api = FileAPI(self.http, self.config.directory)
        return self._file_api
    
    @property
    def tool(self) -> ToolAPI:
        """Tool API (Experimental)."""
        if self._tool_api is None:
            self._tool_api = ToolAPI(self.http, self.config.directory)
        return self._tool_api
    
    @property
    def lsp(self) -> LSPAPI:
        """LSP API."""
        if self._lsp_api is None:
            self._lsp_api = LSPAPI(self.http, self.config.directory)
        return self._lsp_api
    
    @property
    def formatter(self) -> FormatterAPI:
        """Formatter API."""
        if self._formatter_api is None:
            self._formatter_api = FormatterAPI(self.http, self.config.directory)
        return self._formatter_api
    
    @property
    def mcp(self) -> MCPAPI:
        """MCP API."""
        if self._mcp_api is None:
            self._mcp_api = MCPAPI(self.http, self.config.directory)
        return self._mcp_api
    
    @property
    def agent(self) -> AgentAPI:
        """Agent API."""
        if self._agent_api is None:
            self._agent_api = AgentAPI(self.http, self.config.directory)
        return self._agent_api
    
    @property
    def project(self) -> ProjectAPI:
        """Project API."""
        if self._project_api is None:
            self._project_api = ProjectAPI(self.http, self.config.directory)
        return self._project_api
    
    @property
    def path(self) -> PathAPI:
        """Path API."""
        if self._path_api is None:
            self._path_api = PathAPI(self.http, self.config.directory)
        return self._path_api
    
    @property
    def vcs(self) -> VcsAPI:
        """VCS API."""
        if self._vcs_api is None:
            self._vcs_api = VcsAPI(self.http, self.config.directory)
        return self._vcs_api
    
    def health_check(self) -> dict:
        """Check server health.
        
        Returns:
            Health status dict with 'healthy' and 'version' fields.
        """
        response = self.http.get("/global/health")
        return response.json()
    
    def close(self) -> None:
        """Close the client connection."""
        self.http.close()
    
    def __enter__(self) -> "OpenCodeClient":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()

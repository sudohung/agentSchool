"""API modules for OpenCode SDK."""

from .session import SessionAPI
from .message import MessageAPI
from .event import EventAPI, AsyncEventAPI
from .command import CommandAPI
from .file import FileAPI
from .tool import ToolAPI
from .lsp import LSPAPI, FormatterAPI
from .mcp import MCPAPI
from .agent import AgentAPI
from .project import ProjectAPI
from .path import PathAPI, VcsAPI
from .instance import InstanceAPI
from .config import ConfigAPI
from .provider import ProviderAPI
from .global_ import GlobalAPI, LoggingAPI
from .question import QuestionAPI
from .mcp_extended import MCPExtendedAPI

__all__ = [
    "SessionAPI",
    "MessageAPI",
    "EventAPI",
    "AsyncEventAPI",
    "CommandAPI",
    "FileAPI",
    "ToolAPI",
    "LSPAPI",
    "FormatterAPI",
    "MCPAPI",
    "AgentAPI",
    "ProjectAPI",
    "PathAPI",
    "VcsAPI",
    "InstanceAPI",
    "ConfigAPI",
    "ProviderAPI",
    "GlobalAPI",
    "LoggingAPI",
    "QuestionAPI",
    "MCPExtendedAPI",
]

# Question API
from .question import QuestionAPI

# MCP Extended API
from .mcp_extended import MCPExtendedAPI

# Add to __all__
__all__.extend([
    "QuestionAPI",
    "MCPExtendedAPI",
])

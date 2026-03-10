"""Opencode-4-py - Python SDK for OpenCode Server."""

__version__ = "0.1.0"

from opencode_4_py.client import OpenCodeClient
from opencode_4_py.async_client import AsyncOpenCodeClient
from opencode_4_py.config import ClientConfig
from opencode_4_py.errors import (
    OpenCodeError,
    ConnectionError,
    AuthenticationError,
    NotFoundError,
    APIError,
)
from opencode_4_py.models.session import Session, SessionStatus
from opencode_4_py.models.message import Message, UserMessage, AssistantMessage, Part, TextPart
from opencode_4_py.models.event import Event, GlobalEvent
from opencode_4_py.models.lsp import LSPStatus, FormatterStatus
from opencode_4_py.models.mcp import MCPStatus, McpLocalConfig, McpRemoteConfig
from opencode_4_py.models.agent import Agent
from opencode_4_py.models.project import Project
from opencode_4_py.models.path import AppPath, VcsInfo
from opencode_4_py.models.config import Config
from opencode_4_py.models.provider import Provider, Model

__all__ = [
    "OpenCodeClient",
    "AsyncOpenCodeClient",
    "ClientConfig",
    "OpenCodeError",
    "ConnectionError",
    "AuthenticationError",
    "NotFoundError",
    "APIError",
    "Session",
    "SessionStatus",
    "Message",
    "UserMessage",
    "AssistantMessage",
    "Part",
    "TextPart",
    "Event",
    "GlobalEvent",
    "LSPStatus",
    "FormatterStatus",
    "MCPStatus",
    "McpLocalConfig",
    "McpRemoteConfig",
    "Agent",
    "Project",
    "AppPath",
    "VcsInfo",
    "Config",
    "Provider",
    "Model",
]

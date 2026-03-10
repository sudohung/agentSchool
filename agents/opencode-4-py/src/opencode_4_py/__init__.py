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
]

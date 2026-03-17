"""Event models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union, Dict, Any

from .session import Session, SessionStatus, Todo
from .message import Message, Part


class EventSessionCreated(BaseModel):
    """Session created event."""
    type: Literal["session.created"] = "session.created"
    properties: Dict[str, Any]


class EventSessionUpdated(BaseModel):
    """Session updated event."""
    type: Literal["session.updated"] = "session.updated"
    properties: Dict[str, Any]


class EventSessionDeleted(BaseModel):
    """Session deleted event."""
    type: Literal["session.deleted"] = "session.deleted"
    properties: Dict[str, Any]


class EventSessionStatus(BaseModel):
    """Session status event."""
    type: Literal["session.status"] = "session.status"
    properties: Dict[str, Any]


class EventSessionIdle(BaseModel):
    """Session idle event."""
    type: Literal["session.idle"] = "session.idle"
    properties: Dict[str, Any]


class EventSessionDiff(BaseModel):
    """Session diff event."""
    type: Literal["session.diff"] = "session.diff"
    properties: Dict[str, Any]


class EventSessionError(BaseModel):
    """Session error event."""
    type: Literal["session.error"] = "session.error"
    properties: Dict[str, Any]


class EventMessageUpdated(BaseModel):
    """Message updated event."""
    type: Literal["message.updated"] = "message.updated"
    properties: Dict[str, Any]


class EventMessageRemoved(BaseModel):
    """Message removed event."""
    type: Literal["message.removed"] = "message.removed"
    properties: Dict[str, Any]


class EventMessagePartUpdated(BaseModel):
    """Message part updated event."""
    type: Literal["message.part.updated"] = "message.part.updated"
    properties: Dict[str, Any]


class EventMessagePartDelta(BaseModel):
    """Message part delta event."""
    type: Literal["message.part.delta"] = "message.part.delta"
    properties: Dict[str, Any]


class EventPermissionAsked(BaseModel):
    """Permission asked event."""
    type: Literal["permission.asked"] = "permission.asked"
    properties: Dict[str, Any]


class EventPermissionUpdated(BaseModel):
    """Permission updated event."""
    type: Literal["permission.updated"] = "permission.updated"
    properties: Dict[str, Any]


class EventQuestionAsked(BaseModel):
    """Question asked event."""
    type: Literal["question.asked"] = "question.asked"
    properties: Dict[str, Any]


class EventTodoUpdated(BaseModel):
    """Todo updated event."""
    type: Literal["todo.updated"] = "todo.updated"
    properties: Dict[str, Any]


class EventFileEdited(BaseModel):
    """File edited event."""
    type: Literal["file.edited"] = "file.edited"
    properties: Dict[str, Any]


class EventFileWatcherUpdated(BaseModel):
    """File watcher updated event."""
    type: Literal["file.watcher.updated"] = "file.watcher.updated"
    properties: Dict[str, Any]


class EventServerConnected(BaseModel):
    """Server connected event."""
    type: Literal["server.connected"] = "server.connected"
    properties: Dict[str, Any]


class EventGlobalDisposed(BaseModel):
    """Global disposed event."""
    type: Literal["global.disposed"] = "global.disposed"
    properties: Dict[str, Any]


Event = Union[
    EventSessionCreated,
    EventSessionUpdated,
    EventSessionDeleted,
    EventSessionStatus,
    EventSessionIdle,
    EventSessionDiff,
    EventSessionError,
    EventMessageUpdated,
    EventMessageRemoved,
    EventMessagePartUpdated,
    EventMessagePartDelta,
    EventPermissionAsked,
    EventPermissionUpdated,
    EventQuestionAsked,
    EventTodoUpdated,
    EventFileEdited,
    EventFileWatcherUpdated,
    EventServerConnected,
    EventGlobalDisposed,
]


class GlobalEvent(BaseModel):
    """Global event."""
    directory: str
    payload: Event

"""Message and Part models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union, Dict, Any

from .common import TimeInfo, PartTimeInfo, ModelRef, PathInfo, TokenInfo, FileDiff


class UserMessage(BaseModel):
    """User message."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    role: Literal["user"] = "user"
    time: TimeInfo
    format: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    agent: str
    model: ModelRef
    system: Optional[str] = None
    tools: Optional[Dict[str, bool]] = None
    variant: Optional[str] = None
    
    class Config:
        populate_by_name = True


class AssistantMessage(BaseModel):
    """Assistant message."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    role: Literal["assistant"] = "assistant"
    time: TimeInfo
    error: Optional[Dict[str, Any]] = None
    parent_id: str = Field(..., alias="parentID")
    model_id: str = Field(..., alias="modelID")
    provider_id: str = Field(..., alias="providerID")
    mode: str
    agent: str
    path: PathInfo
    summary: Optional[bool] = None
    cost: float
    tokens: TokenInfo
    structured: Optional[Dict[str, Any]] = None
    variant: Optional[str] = None
    finish: Optional[str] = None
    
    class Config:
        populate_by_name = True


Message = Union[UserMessage, AssistantMessage]


class TextPart(BaseModel):
    """Text part."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    message_id: str = Field(..., alias="messageID")
    type: Literal["text"] = "text"
    text: str
    synthetic: Optional[bool] = None
    ignored: Optional[bool] = None
    time: Optional[PartTimeInfo] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class FilePartSource(BaseModel):
    """File part source."""
    type: str
    path: str
    text: Optional[Dict[str, Any]] = None


class FilePart(BaseModel):
    """File part."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    message_id: str = Field(..., alias="messageID")
    type: Literal["file"] = "file"
    mime: str
    filename: Optional[str] = None
    url: str
    source: Optional[FilePartSource] = None
    
    class Config:
        populate_by_name = True


class ToolStatePending(BaseModel):
    """Pending tool state."""
    status: Literal["pending"] = "pending"
    input: Dict[str, Any]
    raw: str


class ToolStateRunning(BaseModel):
    """Running tool state."""
    status: Literal["running"] = "running"
    input: Dict[str, Any]
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    time: PartTimeInfo


class ToolStateCompleted(BaseModel):
    """Completed tool state."""
    status: Literal["completed"] = "completed"
    input: Dict[str, Any]
    output: str
    title: str
    metadata: Dict[str, Any]
    time: PartTimeInfo
    attachments: Optional[List[FilePart]] = None


class ToolStateError(BaseModel):
    """Error tool state."""
    status: Literal["error"] = "error"
    input: Dict[str, Any]
    error: str
    metadata: Optional[Dict[str, Any]] = None
    time: PartTimeInfo


ToolState = Union[ToolStatePending, ToolStateRunning, ToolStateCompleted, ToolStateError]


class ToolPart(BaseModel):
    """Tool part."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    message_id: str = Field(..., alias="messageID")
    type: Literal["tool"] = "tool"
    call_id: str = Field(..., alias="callID")
    tool: str
    state: ToolState
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class ReasoningPart(BaseModel):
    """Reasoning part."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    message_id: str = Field(..., alias="messageID")
    type: Literal["reasoning"] = "reasoning"
    text: str
    metadata: Optional[Dict[str, Any]] = None
    time: PartTimeInfo
    
    class Config:
        populate_by_name = True


class SubtaskPart(BaseModel):
    """Subtask part."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    message_id: str = Field(..., alias="messageID")
    type: Literal["subtask"] = "subtask"
    prompt: str
    description: str
    agent: str
    model: Optional[ModelRef] = None
    command: Optional[str] = None
    
    class Config:
        populate_by_name = True


class StepStartPart(BaseModel):
    """Step start part."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    message_id: str = Field(..., alias="messageID")
    type: Literal["step-start"] = "step-start"
    snapshot: Optional[str] = None
    
    class Config:
        populate_by_name = True


class StepFinishPart(BaseModel):
    """Step finish part."""
    id: str
    session_id: str = Field(..., alias="sessionID")
    message_id: str = Field(..., alias="messageID")
    type: Literal["step-finish"] = "step-finish"
    reason: str
    snapshot: Optional[str] = None
    cost: float
    tokens: TokenInfo
    
    class Config:
        populate_by_name = True


Part = Union[TextPart, FilePart, ToolPart, ReasoningPart, SubtaskPart, StepStartPart, StepFinishPart]


class MessageWithParts(BaseModel):
    """Message with parts."""
    info: Message
    parts: List[Part]


class TextPartInput(BaseModel):
    """Text part input."""
    type: Literal["text"] = "text"
    text: str


class FilePartInput(BaseModel):
    """File part input."""
    type: Literal["file"] = "file"
    mime: str
    url: str
    filename: Optional[str] = None


class AgentPartInput(BaseModel):
    """Agent part input."""
    type: Literal["agent"] = "agent"
    name: str


class SubtaskPartInput(BaseModel):
    """Subtask part input."""
    type: Literal["subtask"] = "subtask"
    prompt: str
    description: str
    agent: str


PartInput = Union[TextPartInput, FilePartInput, AgentPartInput, SubtaskPartInput]


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    message_id: Optional[str] = Field(None, alias="messageID")
    model: Optional[ModelRef] = None
    agent: Optional[str] = None
    no_reply: Optional[bool] = Field(None, alias="noReply")
    format: Optional[Dict[str, Any]] = None
    system: Optional[str] = None
    variant: Optional[str] = None
    parts: List[PartInput]
    
    class Config:
        populate_by_name = True


class CommandRequest(BaseModel):
    """Request to execute a command."""
    message_id: Optional[str] = Field(None, alias="messageID")
    agent: Optional[str] = None
    model: Optional[ModelRef] = None
    command: str
    arguments: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ShellRequest(BaseModel):
    """Request to run a shell command."""
    agent: str
    model: Optional[ModelRef] = None
    command: str

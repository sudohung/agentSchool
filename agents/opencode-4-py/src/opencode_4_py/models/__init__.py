"""Data models for OpenCode SDK."""

from .common import (
    TimeInfo,
    ModelRef,
    PathInfo,
    FileDiff,
    SessionSummary,
    ShareInfo,
    TokenInfo,
    RevertInfo,
)
from .session import (
    Session,
    SessionStatus,
    SessionStatusIdle,
    SessionStatusRetry,
    SessionStatusBusy,
    Todo,
    PermissionRule,
    CreateSessionRequest,
    UpdateSessionRequest,
)
from .message import (
    Message,
    UserMessage,
    AssistantMessage,
    Part,
    TextPart,
    FilePart,
    ToolPart,
    ToolState,
    ReasoningPart,
    SubtaskPart,
    StepStartPart,
    StepFinishPart,
    MessageWithParts,
    PartInput,
    TextPartInput,
    SendMessageRequest,
)
from .event import (
    Event,
    GlobalEvent,
    EventSessionCreated,
    EventSessionUpdated,
    EventMessageUpdated,
    EventMessagePartUpdated,
)
from .command import Command
from .file import (
    FileNode,
    FileContent,
    FileStatus,
    Symbol,
    TextSearchMatch,
)
from .tool import (
    ToolIDs,
    ToolListItem,
    ToolList,
)
from .lsp import (
    LSPStatus,
    FormatterStatus,
)
from .mcp import (
    MCPStatus,
    MCPAddRequest,
    McpConfig,
    McpLocalConfig,
    McpRemoteConfig,
)
from .agent import Agent
from .project import (
    Project,
    ProjectTime,
    ProjectIcon,
    ProjectCommands,
    ProjectUpdateRequest,
)
from .path import AppPath, VcsInfo
from .config import (
    Config,
    ServerConfig,
    CommandConfig,
    SkillsConfig,
    WatcherConfig,
    ConfigUpdateRequest,
)
from .provider import (
    Provider,
    Model,
    ModelCost,
    ModelLimit,
    ProviderAuthMethod,
    ProviderAuthAuthorization,
    ProviderListResponse,
)
from .global_ import (
    Health,
    GlobalEvent,
    LogEntry,
)
from .question import (
    QuestionRequest,
    QuestionInfo,
    QuestionOption,
    QuestionReplyRequest,
    QuestionRejectRequest,
)
from .mcp_extended import (
    MCPAuthResponse,
    MCPAuthStartRequest,
    MCPAuthCallbackRequest,
    MCPConnectRequest,
)

__all__ = [
    "TimeInfo",
    "ModelRef",
    "PathInfo",
    "FileDiff",
    "SessionSummary",
    "ShareInfo",
    "TokenInfo",
    "RevertInfo",
    "Session",
    "SessionStatus",
    "Todo",
    "PermissionRule",
    "CreateSessionRequest",
    "UpdateSessionRequest",
    "Message",
    "UserMessage",
    "AssistantMessage",
    "Part",
    "TextPart",
    "FilePart",
    "ToolPart",
    "ToolState",
    "ReasoningPart",
    "SubtaskPart",
    "MessageWithParts",
    "PartInput",
    "TextPartInput",
    "SendMessageRequest",
    "Event",
    "GlobalEvent",
    "EventSessionCreated",
    "EventSessionUpdated",
    "EventMessageUpdated",
    "EventMessagePartUpdated",
    "Command",
    "FileNode",
    "FileContent",
    "FileStatus",
    "Symbol",
    "TextSearchMatch",
    "ToolIDs",
    "ToolListItem",
    "ToolList",
    "LSPStatus",
    "FormatterStatus",
    "MCPStatus",
    "MCPAddRequest",
    "McpConfig",
    "McpLocalConfig",
    "McpRemoteConfig",
    "Agent",
    "Project",
    "ProjectTime",
    "ProjectIcon",
    "ProjectCommands",
    "ProjectUpdateRequest",
    "AppPath",
    "VcsInfo",
    "Config",
    "ServerConfig",
    "CommandConfig",
    "SkillsConfig",
    "WatcherConfig",
    "ConfigUpdateRequest",
    "Provider",
    "Model",
    "ModelCost",
    "ModelLimit",
    "ProviderAuthMethod",
    "ProviderAuthAuthorization",
    "ProviderListResponse",
    "Health",
    "GlobalEvent",
    "LogEntry",
    "QuestionRequest",
    "QuestionInfo",
    "QuestionOption",
    "QuestionReplyRequest",
    "QuestionRejectRequest",
    "MCPAuthResponse",
    "MCPAuthStartRequest",
    "MCPAuthCallbackRequest",
    "MCPConnectRequest",
]

# Question models
from .question import (
    QuestionRequest,
    QuestionInfo,
    QuestionOption,
    QuestionReplyRequest,
    QuestionRejectRequest,
)

# MCP Extended models
from .mcp_extended import (
    MCPAuthResponse,
    MCPAuthStartRequest,
    MCPAuthCallbackRequest,
    MCPConnectRequest,
)

# Add to __all__
__all__.extend([
    "QuestionRequest",
    "QuestionInfo",
    "QuestionOption",
    "QuestionReplyRequest",
    "QuestionRejectRequest",
    "MCPAuthResponse",
    "MCPAuthStartRequest",
    "MCPAuthCallbackRequest",
    "MCPConnectRequest",
])

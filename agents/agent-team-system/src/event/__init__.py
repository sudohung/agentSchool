"""事件处理模块."""

from event.chain import (
    # 事件类型
    SSEEventType,
    SSEEvent,
    QuestionAskedEvent,
    PermissionAskedEvent,
    EventResult,
    EventContext,
    # 责任链
    EventHandler,
    EventHandlerChain,
)
from event.manager import (
    SSEEventManager,
    create_sse_event_manager,
)

__all__ = [
    # 事件类型
    "SSEEventType",
    "SSEEvent",
    "QuestionAskedEvent",
    "PermissionAskedEvent",
    "EventResult",
    "EventContext",
    # 责任链
    "EventHandler",
    "EventHandlerChain",
    # 管理器
    "SSEEventManager",
    "create_sse_event_manager",
]
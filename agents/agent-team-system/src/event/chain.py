"""SSE 事件处理 - 责任链模式实现.

基于责任链模式处理 OpenCode SSE 事件，
核心处理 question_asked 和 permission_asked 事件。
"""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==================== 事件类型定义 ====================

class SSEEventType(Enum):
    """SSE 事件类型"""
    # 交互事件 - 需要决策 Agent 处理
    QUESTION_ASKED = "question_asked"       # 问题询问
    PERMISSION_ASKED = "permission_asked"   # 权限请求
    
    # 其他事件 - 暂时留空占位
    MESSAGE_UPDATED = "message_updated"
    MESSAGE_PART_DELTA = "message_part_delta"
    FILE_EDITED = "file_edited"
    SESSION_ERROR = "session_error"
    SESSION_IDLE = "session_idle"
    SERVER_CONNECTED = "server_connected"
    UNKNOWN = "unknown"


@dataclass
class SSEEvent:
    """SSE 事件数据结构"""
    id: str
    type: SSEEventType
    source: str
    data: Dict[str, Any]
    timestamp: int
    session_id: Optional[str] = None
    raw_event: Any = None  # 原始 OpenCode 事件对象
    
    @classmethod
    def from_opencode(cls, raw_event: Any, session_id: str) -> 'SSEEvent':
        """从 OpenCode 事件创建"""
        event_type_name = type(raw_event).__name__
        
        # 事件类型映射
        type_mapping = {
            'EventQuestionAsked': SSEEventType.QUESTION_ASKED,
            'EventPermissionAsked': SSEEventType.PERMISSION_ASKED,
            'EventMessageUpdated': SSEEventType.MESSAGE_UPDATED,
            'EventMessagePartDelta': SSEEventType.MESSAGE_PART_DELTA,
            'EventFileEdited': SSEEventType.FILE_EDITED,
            'EventSessionError': SSEEventType.SESSION_ERROR,
            'EventSessionIdle': SSEEventType.SESSION_IDLE,
            'EventServerConnected': SSEEventType.SERVER_CONNECTED,
        }
        
        event_type = type_mapping.get(event_type_name, SSEEventType.UNKNOWN)
        
        # 提取事件数据
        event_data = {}
        if hasattr(raw_event, 'model_dump'):
            event_data = raw_event.model_dump()
        elif hasattr(raw_event, '__dict__'):
            event_data = {k: v for k, v in raw_event.__dict__.items() if not k.startswith('_')}
        
        return cls(
            id=f"evt_{int(time.time() * 1000)}",
            type=event_type,
            source="opencode",
            data=event_data,
            timestamp=int(time.time()),
            session_id=session_id,
            raw_event=raw_event,
        )


@dataclass
class QuestionAskedEvent(SSEEvent):
    """问题询问事件"""
    question_id: Optional[str] = None
    question: Optional[str] = None
    options: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_sse_event(cls, event: SSEEvent) -> 'QuestionAskedEvent':
        """从 SSE 事件创建"""
        raw = event.raw_event
        return cls(
            id=event.id,
            type=event.type,
            source=event.source,
            data=event.data,
            timestamp=event.timestamp,
            session_id=event.session_id,
            raw_event=raw,
            question_id=getattr(raw, 'question_id', None) if raw else None,
            question=getattr(raw, 'question', None) if raw else event.data.get('question'),
            options=getattr(raw, 'options', []) if raw else event.data.get('options', []),
            context=event.data.get('context', {}),
        )


@dataclass
class PermissionAskedEvent(SSEEvent):
    """权限请求事件"""
    permission_id: Optional[str] = None
    permission_type: Optional[str] = None  # file_read, file_write, command_execute
    resource: Optional[str] = None
    agent_role: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_sse_event(cls, event: SSEEvent) -> 'PermissionAskedEvent':
        """从 SSE 事件创建"""
        raw = event.raw_event
        return cls(
            id=event.id,
            type=event.type,
            source=event.source,
            data=event.data,
            timestamp=event.timestamp,
            session_id=event.session_id,
            raw_event=raw,
            permission_id=getattr(raw, 'permission_id', None) if raw else None,
            permission_type=getattr(raw, 'type', None) if raw else event.data.get('type'),
            resource=getattr(raw, 'resource', None) if raw else event.data.get('resource'),
            agent_role=getattr(raw, 'agent', None) if raw else event.data.get('agent'),
            context=event.data.get('context', {}),
        )


@dataclass
class EventResult:
    """事件处理结果"""
    handled: bool
    action: Optional[str] = None  # answered, allowed, denied, ignored
    message: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


# ==================== 事件上下文 ====================

@dataclass
class EventContext:
    """事件处理上下文
    
    包含处理事件所需的所有依赖和服务
    """
    session_id: str
    opencode_client: Any  # OpenCodeClient
    decision_agent: Any   # DecisionAgent
    document_hub: Any = None
    request_board: Any = None
    agent_registry: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_sdk(self) -> Any:
        """获取 OpenCode SDK"""
        return self.opencode_client
    
    def get_decision_agent(self) -> Any:
        """获取决策 Agent"""
        return self.decision_agent


# ==================== 责任链基类 ====================

class EventHandler(ABC):
    """
    事件处理器基类 (责任链模式)
    
    职责：
    1. 判断是否能处理该事件 (can_handle)
    2. 处理事件 (handle)
    3. 传递给下一个处理器 (next)
    """
    
    def __init__(self):
        self._next: Optional[EventHandler] = None
    
    @abstractmethod
    def can_handle(self, event_type: SSEEventType) -> bool:
        """
        判断是否能处理该事件类型
        
        Args:
            event_type: 事件类型
            
        Returns:
            是否能处理
        """
        pass
    
    @abstractmethod
    async def handle(self, event: SSEEvent, context: EventContext) -> Optional[EventResult]:
        """
        处理事件
        
        Args:
            event: SSE 事件
            context: 事件上下文
            
        Returns:
            处理结果，如果返回 None 则传递给下一个处理器
        """
        pass
    
    def set_next(self, handler: 'EventHandler') -> 'EventHandler':
        """
        设置下一个处理器
        
        Args:
            handler: 下一个处理器
            
        Returns:
            下一个处理器（支持链式调用）
        """
        self._next = handler
        return handler
    
    async def process(self, event: SSEEvent, context: EventContext) -> Optional[EventResult]:
        """
        处理事件（责任链入口）
        
        如果当前处理器不能处理，则传递给下一个处理器
        
        Args:
            event: SSE 事件
            context: 事件上下文
            
        Returns:
            处理结果
        """
        # 检查是否能处理
        if self.can_handle(event.type):
            logger.debug(f"{self.__class__.__name__} handling event: {event.type.value}")
            result = await self.handle(event, context)
            if result:
                return result
        
        # 传递给下一个处理器
        if self._next:
            return await self._next.process(event, context)
        
        # 没有处理器能处理
        logger.warning(f"No handler found for event type: {event.type.value}")
        return EventResult(handled=False, action="no_handler")


# ==================== 事件处理器链 ====================

class EventHandlerChain:
    """
    事件处理器链
    
    管理责任链的构建和事件分发
    """
    
    def __init__(self, context: EventContext):
        self.context = context
        self._head: Optional[EventHandler] = None
        self._handlers: List[EventHandler] = []
        self._stats: Dict[str, int] = {}
    
    def add_handler(self, handler: EventHandler) -> 'EventHandlerChain':
        """
        添加处理器到链末尾
        
        Args:
            handler: 事件处理器
            
        Returns:
            self（支持链式调用）
        """
        self._handlers.append(handler)
        
        if not self._head:
            self._head = handler
        else:
            # 找到最后一个处理器并设置 next
            current = self._head
            while current._next:
                current = current._next
            current.set_next(handler)
        
        return self
    
    async def process(self, event: SSEEvent) -> Optional[EventResult]:
        """
        处理事件
        
        Args:
            event: SSE 事件
            
        Returns:
            处理结果
        """
        if not self._head:
            logger.warning("No handlers registered")
            return EventResult(handled=False)
        
        # 统计
        event_type = event.type.value
        self._stats[event_type] = self._stats.get(event_type, 0) + 1
        
        # 处理
        try:
            result = await self._head.process(event, self.context)
            return result
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}")
            return EventResult(handled=False, action="error", message=str(e))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计"""
        return {
            "handlers_count": len(self._handlers),
            "event_stats": self._stats.copy(),
            "handlers": [h.__class__.__name__ for h in self._handlers],
        }
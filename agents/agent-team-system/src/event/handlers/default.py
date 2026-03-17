"""默认事件处理器 - 其他事件占位符."""

from __future__ import annotations

import logging
from typing import Optional

from event.chain import (
    EventHandler,
    SSEEventType,
    SSEEvent,
    EventContext,
    EventResult,
)

logger = logging.getLogger(__name__)


class DefaultHandler(EventHandler):
    """
    默认事件处理器
    
    职责：
    1. 处理所有未匹配的事件类型
    2. 记录事件日志
    3. 返回未处理状态
    
    当前实现：
    - 仅记录日志，不做实际处理
    - 为其他事件类型留空占位
    """
    
    def can_handle(self, event_type: SSEEventType) -> bool:
        """处理所有事件类型"""
        return True
    
    async def handle(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> Optional[EventResult]:
        """
        处理事件
        
        当前仅记录日志，不做实际处理
        """
        event_type = event.type.value
        logger.info(f"📋 Default handler received event: {event_type}")
        
        # 根据事件类型做不同处理
        handler_method = getattr(self, f"_handle_{event_type}", None)
        if handler_method:
            return await handler_method(event, context)
        
        # 默认：仅记录日志
        logger.debug(f"Event {event.id} ({event_type}) logged but not processed")
        return EventResult(
            handled=True,
            action="logged",
            message=f"Event {event_type} received and logged",
        )
    
    # ==================== 占位处理器 ====================
    # 以下方法为其他事件类型的占位处理器
    # 当前仅记录日志，后续可扩展实现
    
    async def _handle_message_updated(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> EventResult:
        """处理消息更新事件（占位）"""
        logger.debug(f"Message updated: {event.id}")
        return EventResult(handled=True, action="logged")
    
    async def _handle_message_part_delta(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> EventResult:
        """处理消息增量事件（占位）"""
        logger.debug(f"Message delta: {event.id}")
        return EventResult(handled=True, action="logged")
    
    async def _handle_file_edited(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> EventResult:
        """处理文件编辑事件（占位）"""
        logger.debug(f"File edited: {event.id}")
        return EventResult(handled=True, action="logged")
    
    async def _handle_session_error(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> EventResult:
        """处理会话错误事件（占位）"""
        logger.error(f"Session error: {event.data}")
        return EventResult(handled=True, action="logged")
    
    async def _handle_session_idle(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> EventResult:
        """处理会话空闲事件（占位）"""
        logger.debug(f"Session idle: {event.id}")
        return EventResult(handled=True, action="logged")
    
    async def _handle_server_connected(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> EventResult:
        """处理服务器连接事件（占位）"""
        logger.info(f"Server connected: {event.id}")
        return EventResult(handled=True, action="logged")
    
    async def _handle_unknown(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> EventResult:
        """处理未知事件"""
        logger.warning(f"Unknown event type: {event.type}")
        return EventResult(handled=True, action="logged")
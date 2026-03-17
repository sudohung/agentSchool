"""事件处理服务 - 使用 opencode-4-py SDK."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    
    AGENT_MESSAGE = "agent_message"
    AGENT_STATUS = "agent_status"
    AGENT_ERROR = "agent_error"
    
    WORKFLOW_START = "workflow_start"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    
    SYSTEM_NOTIFICATION = "system_notification"
    SYSTEM_ERROR = "system_error"


@dataclass
class Event:
    """事件"""
    id: str
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventHandlerService:
    """
    事件处理服务
    
    使用 opencode-4-py SDK 实现事件流处理
    
    功能：
    - SSE 事件流连接
    - 事件分发
    - 事件过滤
    - 事件历史
    """
    
    def __init__(
        self,
        opencode_client: Any,
        session_id: Optional[str] = None,
    ):
        self.client = opencode_client
        self.session_id = session_id
        
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._history: List[Event] = []
        self._max_history = 1000
        
        self._running = False
        self._event_task: Optional[asyncio.Task] = None
        self._event_queue: asyncio.Queue = asyncio.Queue()
    
    async def start(self):
        """启动事件服务"""
        self._running = True
        
        self._event_task = asyncio.create_task(self._event_loop())
        
        await self._connect_sse()
        
        logger.info("EventHandlerService started")
    
    async def stop(self):
        """停止事件服务"""
        self._running = False
        
        if self._event_task:
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
        
        logger.info("EventHandlerService stopped")
    
    def on_event(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
    ):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def off_event(
        self,
        event_type: EventType,
        handler: Callable,
    ):
        """取消事件处理器"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]
    
    async def emit(self, event: Event):
        """发送事件"""
        await self._event_queue.put(event)
    
    async def emit_custom(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any],
    ):
        """发送自定义事件"""
        event = Event(
            id=self._generate_event_id(),
            type=event_type,
            source=source,
            data=data,
            timestamp=int(time.time()),
        )
        await self.emit(event)
    
    async def _event_loop(self):
        """事件处理循环"""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0,
                )
                await self._dispatch_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event loop: {e}")
    
    async def _dispatch_event(self, event: Event):
        """分发事件"""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        handlers = self._handlers.get(event.type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    async def _connect_sse(self):
        """连接 SSE 事件流"""
        if not self.client:
            logger.warning("No OpenCode client, SSE disabled")
            return
        
        try:
            asyncio.create_task(self._sse_listener())
            logger.info("SSE connection established")
        except Exception as e:
            logger.error(f"Failed to connect SSE: {e}")
    
    async def _sse_listener(self):
        """SSE 监听器"""
        while self._running:
            try:
                async for sse_event in self._get_sse_stream():
                    event = self._parse_sse_event(sse_event)
                    if event:
                        await self.emit(event)
            except Exception as e:
                logger.error(f"SSE error: {e}")
                await asyncio.sleep(5)
    
    async def _get_sse_stream(self):
        """获取 SSE 流 - 使用 opencode-4-py SDK"""
        if not self.client or not self.session_id:
            while self._running:
                await asyncio.sleep(1)
            return
        
        try:
            event_api = self.client.event
            async for event in event_api.subscribe(session_id=self.session_id):
                yield event
        except Exception as e:
            logger.error(f"Error getting SSE stream: {e}")
            while self._running:
                await asyncio.sleep(1)
    
    def _parse_sse_event(self, sse_data: Any) -> Optional[Event]:
        """解析 SSE 事件"""
        try:
            if isinstance(sse_data, str):
                data = json.loads(sse_data)
            else:
                data = sse_data
            
            event_type_str = data.get("type", "unknown")
            
            event_type_mapping = {
                "file.edited": EventType.FILE_MODIFIED,
                "message.updated": EventType.AGENT_MESSAGE,
                "session.error": EventType.SYSTEM_ERROR,
                "question.asked": EventType.SYSTEM_NOTIFICATION,
            }
            
            event_type = event_type_mapping.get(
                event_type_str,
                EventType.SYSTEM_NOTIFICATION
            )
            
            return Event(
                id=data.get("id", self._generate_event_id()),
                type=event_type,
                source=data.get("source", "opencode"),
                data=data.get("data", {}),
                timestamp=data.get("timestamp", int(time.time())),
                metadata=data.get("metadata", {}),
            )
        except Exception as e:
            logger.error(f"Failed to parse SSE event: {e}")
            return None
    
    def _generate_event_id(self) -> str:
        """生成事件 ID"""
        import hashlib
        timestamp = int(time.time() * 1000)
        data = f"event:{timestamp}"
        return "evt_" + hashlib.md5(data.encode()).hexdigest()[:12]
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """获取事件历史"""
        results = self._history
        
        if event_type:
            results = [e for e in results if e.type == event_type]
        
        if source:
            results = [e for e in results if e.source == source]
        
        return results[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取事件统计"""
        by_type = {}
        for event in self._history:
            type_str = event.type.value
            by_type[type_str] = by_type.get(type_str, 0) + 1
        
        return {
            "total_events": len(self._history),
            "by_type": by_type,
            "handlers_registered": sum(len(h) for h in self._handlers.values()),
        }


class AgentEventBridge:
    """
    Agent 事件桥接器
    
    将 OpenCode 事件桥接到 Agent Team System
    """
    
    def __init__(
        self,
        event_handler: EventHandlerService,
        agent_registry: Any = None,
        request_board: Any = None,
    ):
        self.event_handler = event_handler
        self.agent_registry = agent_registry
        self.request_board = request_board
        
        self._register_handlers()
    
    def _register_handlers(self):
        """注册事件处理器"""
        self.event_handler.on_event(
            EventType.FILE_MODIFIED,
            self._on_file_modified
        )
        
        self.event_handler.on_event(
            EventType.AGENT_MESSAGE,
            self._on_agent_message
        )
        
        self.event_handler.on_event(
            EventType.WORKFLOW_ERROR,
            self._on_workflow_error
        )
    
    async def _on_file_modified(self, event: Event):
        """文件修改事件处理"""
        file_path = event.data.get("path")
        logger.info(f"File modified: {file_path}")
    
    async def _on_agent_message(self, event: Event):
        """Agent 消息事件处理"""
        message = event.data.get("message")
        source_agent = event.data.get("agent")
        logger.info(f"Agent message from {source_agent}: {message}")
    
    async def _on_workflow_error(self, event: Event):
        """工作流错误事件处理"""
        error = event.data.get("error")
        logger.error(f"Workflow error: {error}")

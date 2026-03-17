"""SSE 事件管理器 - 整合 SSE 订阅和责任链处理."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Any

from event.chain import (
    SSEEvent,
    SSEEventType,
    EventContext,
    EventHandlerChain,
)
from event.handlers import (
    QuestionAskHandler,
    PermissionAskHandler,
    DefaultHandler,
)

logger = logging.getLogger(__name__)


class SSEEventManager:
    """
    SSE 事件管理器
    
    整合 SSE 订阅和责任链事件处理
    
    功能：
    1. 连接 OpenCode SSE 流
    2. 将事件分发给责任链处理
    3. 管理事件处理生命周期
    """
    
    def __init__(
        self,
        opencode_client: Any,
        session_id: str,
        decision_agent: Any,
        document_hub: Any = None,
        request_board: Any = None,
    ):
        """
        初始化 SSE 事件管理器
        
        Args:
            opencode_client: OpenCode 客户端
            session_id: 会话 ID
            decision_agent: 决策 Agent
            document_hub: 文档中心（可选）
            request_board: 诉求看板（可选）
        """
        self.client = opencode_client
        self.session_id = session_id
        self.decision_agent = decision_agent
        
        # 创建事件上下文
        self.context = EventContext(
            session_id=session_id,
            opencode_client=opencode_client,
            decision_agent=decision_agent,
            document_hub=document_hub,
            request_board=request_board,
        )
        
        # 创建责任链
        self.chain = self._build_chain()
        
        # 状态
        self._running = False
        self._sse_task: Optional[asyncio.Task] = None
        
        # 统计
        self._stats = {
            "events_received": 0,
            "events_processed": 0,
            "questions_answered": 0,
            "permissions_handled": 0,
        }
    
    def _build_chain(self) -> EventHandlerChain:
        """
        构建事件处理责任链
        
        链顺序：
        1. QuestionAskHandler - 处理问题询问
        2. PermissionAskHandler - 处理权限请求
        3. DefaultHandler - 处理其他事件
        """
        chain = EventHandlerChain(self.context)
        
        # 添加处理器（顺序重要）
        chain.add_handler(QuestionAskHandler())
        chain.add_handler(PermissionAskHandler())
        chain.add_handler(DefaultHandler())
        
        logger.info(f"Event handler chain built with {len(chain._handlers)} handlers")
        return chain
    
    async def start(self):
        """启动 SSE 事件监听"""
        if self._running:
            logger.warning("SSEEventManager already running")
            return
        
        self._running = True
        self._sse_task = asyncio.create_task(self._sse_listener())
        
        logger.info(f"SSEEventManager started for session {self.session_id}")
    
    async def stop(self):
        """停止 SSE 事件监听"""
        self._running = False
        
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
        
        logger.info("SSEEventManager stopped")
    
    async def _sse_listener(self):
        """SSE 事件监听器"""
        logger.info("Starting SSE event listener...")
        
        while self._running:
            try:
                # 使用 OpenCode SDK 订阅事件
                if hasattr(self.client, 'event') and hasattr(self.client.event, 'subscribe'):
                    # 尝试不同的 API 签名
                    import inspect
                    sig = inspect.signature(self.client.event.subscribe)
                    
                    # 检查是否有 session_id 参数
                    if 'session_id' in sig.parameters:
                        async for raw_event in self.client.event.subscribe(session_id=self.session_id):
                            if not self._running:
                                break
                            await self._handle_raw_event(raw_event)
                    else:
                        # 没有 session_id 参数，使用全局事件流
                        logger.info("Using global event stream (no session_id)")
                        async for raw_event in self.client.event.subscribe():
                            if not self._running:
                                break
                            await self._handle_raw_event(raw_event)
                else:
                    logger.warning("OpenCode SDK event.subscribe not available")
                    await asyncio.sleep(5)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SSE listener error: {e}")
                await asyncio.sleep(5)
    
    async def _handle_raw_event(self, raw_event: Any):
        """
        处理原始 SSE 事件
        
        Args:
            raw_event: OpenCode 原始事件对象
        """
        self._stats["events_received"] += 1
        
        try:
            # 转换为统一事件格式
            event = SSEEvent.from_opencode(raw_event, self.session_id)
            
            logger.info(f"📨 Received event: {event.type.value}")
            
            # 核心事件处理
            if event.type in (SSEEventType.QUESTION_ASKED, SSEEventType.PERMISSION_ASKED):
                logger.info(f"🎯 Processing core event: {event.type.value}")
                
                # 分发给责任链处理
                result = await self.chain.process(event)
                
                if result and result.handled:
                    self._stats["events_processed"] += 1
                    
                    # 更新统计
                    if event.type == SSEEventType.QUESTION_ASKED:
                        self._stats["questions_answered"] += 1
                    elif event.type == SSEEventType.PERMISSION_ASKED:
                        self._stats["permissions_handled"] += 1
                    
                    logger.info(f"✅ Event handled: {result.action}")
                else:
                    logger.warning(f"⚠️ Event not handled: {event.id}")
            else:
                # 其他事件 - 简单记录
                logger.debug(f"📋 Event logged: {event.type.value}")
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def get_statistics(self) -> dict:
        """获取事件处理统计"""
        return {
            **self._stats,
            "chain_stats": self.chain.get_statistics(),
            "running": self._running,
        }


# ==================== 工厂函数 ====================

async def create_sse_event_manager(
    opencode_client: Any,
    session_id: str,
    decision_agent: Any,
    **kwargs,
) -> SSEEventManager:
    """
    创建并启动 SSE 事件管理器
    
    Args:
        opencode_client: OpenCode 客户端
        session_id: 会话 ID
        decision_agent: 决策 Agent
        **kwargs: 其他参数
        
    Returns:
        已启动的 SSEEventManager 实例
    """
    manager = SSEEventManager(
        opencode_client=opencode_client,
        session_id=session_id,
        decision_agent=decision_agent,
        **kwargs,
    )
    
    await manager.start()
    
    return manager
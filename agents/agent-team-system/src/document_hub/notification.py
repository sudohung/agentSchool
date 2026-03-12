"""通知服务 (简化版)."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Callable, Dict, Any
import asyncio


class NotificationType(Enum):
    """通知类型"""
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Notification:
    """通知"""
    
    def __init__(
        self,
        id: str,
        type: NotificationType,
        priority: NotificationPriority,
        document_id: str,
        message: str,
        sender: str,
        recipients: List[str],
    ):
        self.id = id
        self.type = type
        self.priority = priority
        self.document_id = document_id
        self.message = message
        self.sender = sender
        self.recipients = recipients


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._history: List[Notification] = []
    
    def subscribe(self, topic: str, callback: Callable):
        """订阅主题"""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
    
    async def publish(self, notification: Notification):
        """发布通知"""
        await self._queue.put(notification)
        self._history.append(notification)
        await self._notify_subscribers(notification)
    
    async def _notify_subscribers(self, notification: Notification):
        """通知订阅者"""
        pass

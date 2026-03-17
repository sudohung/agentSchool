"""通知服务 - 完整的通知管理功能."""

from __future__ import annotations

import asyncio
import hashlib
import time
from enum import Enum
from typing import Optional, List, Callable, Dict, Any, Set
import logging

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """通知类型"""
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_LOCKED = "document_locked"
    DOCUMENT_UNLOCKED = "document_unlocked"
    VERSION_CREATED = "version_created"
    VERSION_ROLLBACK = "version_rollback"


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification:
    """通知"""
    
    def __init__(
        self,
        id: str,
        type: NotificationType,
        priority: NotificationPriority,
        document_id: str,
        document_title: str,
        message: str,
        sender: str,
        recipients: List[str],
        timestamp: Optional[int] = None,
        read: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.type = type
        self.priority = priority
        self.document_id = document_id
        self.document_title = document_title
        self.message = message
        self.sender = sender
        self.recipients = recipients
        self.timestamp = timestamp or int(time.time())
        self.read = read
        self.metadata = metadata or {}


class NotificationService:
    """
    通知服务
    
    功能：
    - 订阅/发布模式
    - 按主题过滤
    - 批量通知
    - 通知历史
    - Agent 收件箱
    """
    
    def __init__(self):
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._inbox: Dict[str, List[Notification]] = {}
        self._history: List[Notification] = []
        self.max_history = 1000
    
    def subscribe(
        self,
        topic: str,
        callback: Callable[[Notification], None],
    ):
        """
        订阅主题
        
        主题格式：
        - "document.*" - 所有文档事件
        - "document.created" - 文档创建
        - "document.updated.{doc_type}" - 特定类型更新
        - "agent.{role}" - 特定 Agent 的通知
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = set()
        self._subscribers[topic].add(callback)
        logger.debug(f"Subscribed to topic: {topic}")
    
    def unsubscribe(
        self,
        topic: str,
        callback: Callable[[Notification], None],
    ):
        """取消订阅"""
        if topic in self._subscribers:
            self._subscribers[topic].discard(callback)
    
    async def publish(self, notification: Notification):
        """
        发布通知
        
        Args:
            notification: 通知对象
        """
        self._history.append(notification)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
        
        for recipient in notification.recipients:
            if recipient not in self._inbox:
                self._inbox[recipient] = []
            self._inbox[recipient].append(notification)
        
        await self._notify_subscribers(notification)
        
        logger.debug(f"Notification published: {notification.id} to {notification.recipients}")
    
    async def _notify_subscribers(self, notification: Notification):
        """通知匹配的订阅者"""
        topics_to_notify: Set[str] = set()
        
        exact_topic = f"document.{notification.type.value}"
        if exact_topic in self._subscribers:
            topics_to_notify.add(exact_topic)
        
        wildcard_topic = "document.*"
        if wildcard_topic in self._subscribers:
            topics_to_notify.add(wildcard_topic)
        
        for recipient in notification.recipients:
            agent_topic = f"agent.{recipient}"
            if agent_topic in self._subscribers:
                topics_to_notify.add(agent_topic)
        
        doc_type = notification.metadata.get("doc_type")
        if doc_type:
            type_topic = f"document.{notification.type.value}.{doc_type}"
            if type_topic in self._subscribers:
                topics_to_notify.add(type_topic)
        
        for topic in topics_to_notify:
            for callback in self._subscribers.get(topic, set()):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(notification)
                    else:
                        callback(notification)
                except Exception as e:
                    logger.error(f"Error in notification callback: {e}")
    
    async def notify_document_change(
        self,
        notification_type: NotificationType,
        document_id: str,
        document_title: str,
        sender: str,
        recipients: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        发送文档变更通知
        
        便捷方法
        """
        notification = Notification(
            id=self._generate_notification_id(),
            type=notification_type,
            priority=NotificationPriority.NORMAL,
            document_id=document_id,
            document_title=document_title,
            message=self._generate_message(notification_type, document_title, sender),
            sender=sender,
            recipients=recipients,
            timestamp=int(time.time()),
            metadata=metadata or {},
        )
        
        await self.publish(notification)
    
    def get_inbox(
        self,
        agent_role: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """
        获取 Agent 的收件箱
        
        Args:
            agent_role: Agent 角色
            unread_only: 是否只返回未读
            limit: 最大数量
            
        Returns:
            通知列表
        """
        notifications = self._inbox.get(agent_role, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        return notifications[-limit:]
    
    def mark_as_read(self, notification_id: str, agent_role: str):
        """标记通知为已读"""
        for notification in self._inbox.get(agent_role, []):
            if notification.id == notification_id:
                notification.read = True
                break
    
    def clear_inbox(self, agent_role: str):
        """清空收件箱"""
        self._inbox[agent_role] = []
    
    def get_history(
        self,
        document_id: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100,
    ) -> List[Notification]:
        """获取通知历史"""
        results = self._history
        
        if document_id:
            results = [n for n in results if n.document_id == document_id]
        
        if notification_type:
            results = [n for n in results if n.type.value == notification_type]
        
        return results[-limit:]
    
    def _generate_notification_id(self) -> str:
        """生成通知 ID"""
        timestamp = int(time.time() * 1000)
        data = f"notification:{timestamp}"
        return "notif_" + hashlib.md5(data.encode()).hexdigest()[:12]
    
    def _generate_message(
        self,
        notification_type: NotificationType,
        document_title: str,
        sender: str,
    ) -> str:
        """生成通知消息"""
        messages = {
            NotificationType.DOCUMENT_CREATED: f"{sender} 创建了文档：{document_title}",
            NotificationType.DOCUMENT_UPDATED: f"{sender} 更新了文档：{document_title}",
            NotificationType.DOCUMENT_DELETED: f"{sender} 删除了文档：{document_title}",
            NotificationType.DOCUMENT_LOCKED: f"{sender} 锁定了文档：{document_title}",
            NotificationType.DOCUMENT_UNLOCKED: f"{sender} 解锁了文档：{document_title}",
            NotificationType.VERSION_CREATED: f"{sender} 创建了新版本：{document_title}",
            NotificationType.VERSION_ROLLBACK: f"{sender} 回滚了文档：{document_title}",
        }
        return messages.get(notification_type, f"{sender} 对 {document_title} 执行了操作")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取通知统计"""
        by_type = {}
        for notification in self._history:
            type_str = notification.type.value
            by_type[type_str] = by_type.get(type_str, 0) + 1
        
        return {
            "total_notifications": len(self._history),
            "by_type": by_type,
            "subscribers_count": sum(len(s) for s in self._subscribers.values()),
            "topics_count": len(self._subscribers),
        }

"""反馈处理器."""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional
import logging

from .models import FeedbackItem

logger = logging.getLogger(__name__)


class FeedbackHandler:
    """
    反馈处理器
    
    功能：
    - 收集用户反馈
    - 分类反馈
    - 优先级排序
    - 触发后续迭代
    """
    
    def __init__(self, request_board: Optional[Any] = None):
        self.request_board = request_board
        self._feedback_items: List[FeedbackItem] = []
    
    async def submit_feedback(
        self,
        feedback_type: str,
        priority: str,
        content: str,
        related_artifact: Optional[str] = None,
    ) -> FeedbackItem:
        """提交反馈"""
        feedback = FeedbackItem(
            id=self._generate_feedback_id(),
            type=feedback_type,
            priority=priority,
            content=content,
            related_artifact=related_artifact,
            status="open",
            created_at=int(time.time()),
        )
        
        self._feedback_items.append(feedback)
        
        logger.info(f"Feedback submitted: {feedback.id} ({feedback_type})")
        
        return feedback
    
    async def get_feedback(
        self,
        feedback_type: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[FeedbackItem]:
        """获取反馈列表"""
        results = self._feedback_items
        
        if feedback_type:
            results = [f for f in results if f.type == feedback_type]
        
        if priority:
            results = [f for f in results if f.priority == priority]
        
        if status:
            results = [f for f in results if f.status == status]
        
        return results
    
    async def resolve_feedback(self, feedback_id: str) -> bool:
        """解决反馈"""
        for feedback in self._feedback_items:
            if feedback.id == feedback_id:
                feedback.status = "resolved"
                feedback.resolved_at = int(time.time())
                return True
        return False
    
    async def trigger_iteration(self, feedback: FeedbackItem) -> str:
        """触发新的迭代"""
        if not self.request_board:
            raise RuntimeError("RequestBoard not available")
        
        from request_board.models import Request, RequestType, RequestPriority, RequestStatus
        
        priority_map = {
            "low": RequestPriority.LOW,
            "medium": RequestPriority.NORMAL,
            "high": RequestPriority.HIGH,
            "critical": RequestPriority.CRITICAL,
        }
        
        request = Request(
            id="",
            type=RequestType.COLLABORATION,
            priority=priority_map.get(feedback.priority, RequestPriority.NORMAL),
            status=RequestStatus.PENDING,
            from_agent="User",
            to_agent="Coordinator",
            subject=f"反馈处理：{feedback.type}",
            content=feedback.content,
            context={
                "feedback_id": feedback.id,
                "feedback_type": feedback.type,
                "related_artifact": feedback.related_artifact,
            },
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        
        request_id = await self.request_board.create_request(request)
        
        logger.info(f"Triggered iteration for feedback {feedback.id}: request {request_id}")
        
        return request_id
    
    def _generate_feedback_id(self) -> str:
        """生成反馈 ID"""
        import hashlib
        timestamp = int(time.time() * 1000)
        data = f"feedback:{timestamp}"
        return "fb_" + hashlib.md5(data.encode()).hexdigest()[:12]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取反馈统计"""
        by_type = {}
        by_priority = {}
        by_status = {}
        
        for feedback in self._feedback_items:
            by_type[feedback.type] = by_type.get(feedback.type, 0) + 1
            by_priority[feedback.priority] = by_priority.get(feedback.priority, 0) + 1
            by_status[feedback.status] = by_status.get(feedback.status, 0) + 1
        
        return {
            "total": len(self._feedback_items),
            "by_type": by_type,
            "by_priority": by_priority,
            "by_status": by_status,
        }

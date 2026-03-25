"""反馈处理器 - 完善版.

功能：
- 收集用户反馈
- 分析和分类反馈
- 优先级排序
- 创建改进任务
- 触发后续迭代
"""

from __future__ import annotations

import time
import hashlib
from typing import List, Dict, Any, Optional
from enum import Enum
import logging
import asyncio

from .models import FeedbackItem

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """反馈类型"""
    
    BUG = "bug"  # Bug 报告
    IMPROVEMENT = "improvement"  # 改进建议
    FEATURE = "feature"  # 新功能请求
    PERFORMANCE = "performance"  # 性能问题
    DOCUMENTATION = "documentation"  # 文档问题
    UX = "ux"  # 用户体验
    OTHER = "other"  # 其他


class FeedbackPriority(str, Enum):
    """反馈优先级"""
    
    P0_CRITICAL = "p0_critical"  # 关键问题
    P1_HIGH = "p1_high"  # 高优先级
    P2_MEDIUM = "p2_medium"  # 中优先级
    P3_LOW = "p3_low"  # 低优先级


class FeedbackStatus(str, Enum):
    """反馈状态"""
    
    PENDING = "pending"  # 待处理
    ANALYZING = "analyzing"  # 分析中
    PRIORITIZED = "prioritized"  # 已排序
    IN_PROGRESS = "in_progress"  # 处理中
    RESOLVED = "resolved"  # 已解决
    REJECTED = "rejected"  # 已拒绝


class FeedbackAnalysis:
    """反馈分析结果"""
    
    def __init__(
        self,
        feedback_id: str,
        feedback_type: FeedbackType,
        priority: FeedbackPriority,
        confidence: float,
        keywords: List[str],
        sentiment: str = "neutral",
        impact_scope: str = "medium",
    ):
        self.feedback_id = feedback_id
        self.feedback_type = feedback_type
        self.priority = priority
        self.confidence = confidence
        self.keywords = keywords
        self.sentiment = sentiment
        self.impact_scope = impact_scope
    
    def __repr__(self) -> str:
        return (
            f"FeedbackAnalysis({self.feedback_type}, {self.priority}, "
            f"confidence={self.confidence:.2f})"
        )


class FeedbackProcessor:
    """
    反馈处理器
    
    职责：
    1. 收集用户反馈
    2. 分析和分类反馈
    3. 优先级排序
    4. 创建改进任务
    5. 触发新的迭代
    """
    
    def __init__(
        self,
        request_board: Optional[Any] = None,
        document_hub: Optional[Any] = None,
    ):
        self.request_board = request_board
        self.document_hub = document_hub
        self._feedback_items: List[FeedbackItem] = []
        self._feedback_queue: asyncio.Queue = asyncio.Queue()
        self._analysis_cache: Dict[str, FeedbackAnalysis] = {}
        
        # 关键词映射（用于自动分类）
        self._type_keywords = {
            FeedbackType.BUG: ["bug", "error", "crash", "fail", "issue", "wrong"],
            FeedbackType.IMPROVEMENT: ["improve", "enhance", "better", "optimize"],
            FeedbackType.FEATURE: ["feature", "add", "new", "request"],
            FeedbackType.PERFORMANCE: ["slow", "performance", "speed", "latency"],
            FeedbackType.DOCUMENTATION: ["doc", "documentation", "guide", "example"],
            FeedbackType.UX: ["ux", "ui", "design", "interface", "usability"],
        }
    
    async def collect(
        self,
        delivery_id: str,
        content: str,
        feedback_type: str = "other",
        priority: str = "p2_medium",
        user_id: str = "user",
        attachments: Optional[List[str]] = None,
    ) -> FeedbackItem:
        """
        收集反馈
        
        Args:
            delivery_id: 交付 ID
            content: 反馈内容
            feedback_type: 反馈类型
            priority: 优先级
            user_id: 用户 ID
            attachments: 附件列表
        
        Returns:
            FeedbackItem: 反馈项
        """
        feedback_id = self._generate_feedback_id()
        
        feedback = FeedbackItem(
            id=feedback_id,
            type=feedback_type,
            priority=priority,
            content=content,
            status="open",
            created_at=int(time.time()),
            delivery_id=delivery_id,
            user_id=user_id,
            attachments=attachments or [],
        )
        
        self._feedback_items.append(feedback)
        await self._feedback_queue.put(feedback)
        
        logger.info(f"Feedback collected: {feedback_id} ({feedback_type})")
        
        return feedback
    
    async def analyze(self, feedback: FeedbackItem) -> FeedbackAnalysis:
        """
        分析反馈
        
        步骤:
        1. 提取关键词
        2. 情感分析
        3. 分类反馈
        4. 评估影响范围
        
        Args:
            feedback: 反馈项
        
        Returns:
            FeedbackAnalysis: 分析结果
        """
        logger.info(f"Analyzing feedback: {feedback.id}")
        
        # 检查缓存
        if feedback.id in self._analysis_cache:
            logger.debug(f"Analysis cached for: {feedback.id}")
            return self._analysis_cache[feedback.id]
        
        content_lower = feedback.content.lower()
        
        # 1. 提取关键词
        keywords = self._extract_keywords(content_lower)
        
        # 2. 自动分类
        feedback_type = self._classify_feedback(content_lower, keywords)
        
        # 3. 情感分析（简化版）
        sentiment = self._analyze_sentiment(content_lower)
        
        # 4. 评估影响范围
        impact_scope = self._assess_impact(feedback_type, content_lower)
        
        # 5. 优先级评估
        priority = self._determine_priority(
            feedback_type,
            sentiment,
            impact_scope,
            keywords,
        )
        
        # 计算置信度
        confidence = self._calculate_confidence(keywords, feedback_type)
        
        analysis = FeedbackAnalysis(
            feedback_id=feedback.id,
            feedback_type=feedback_type,
            priority=priority,
            confidence=confidence,
            keywords=keywords,
            sentiment=sentiment,
            impact_scope=impact_scope,
        )
        
        # 缓存分析结果
        self._analysis_cache[feedback.id] = analysis
        
        logger.info(
            f"Analysis complete: {feedback.id} -> "
            f"{feedback_type.value}, {priority.value}, {confidence:.2f}"
        )
        
        return analysis
    
    async def prioritize(
        self,
        feedback: FeedbackItem,
        analysis: FeedbackAnalysis,
    ) -> FeedbackPriority:
        """
        优先级排序
        
        考虑因素:
        - 反馈类型
        - 影响范围
        - 紧急程度
        - 用户重要性
        
        Args:
            feedback: 反馈项
            analysis: 反馈分析
        
        Returns:
            FeedbackPriority: 最终优先级
        """
        # 基于分析结果的优先级
        base_priority = analysis.priority
        
        # 根据影响范围调整
        if analysis.impact_scope == "critical":
            if base_priority in [FeedbackPriority.P2_MEDIUM, FeedbackPriority.P3_LOW]:
                base_priority = FeedbackPriority.P1_HIGH
        elif analysis.impact_scope == "high":
            if base_priority == FeedbackPriority.P3_LOW:
                base_priority = FeedbackPriority.P2_MEDIUM
        
        # 根据情感调整（负面情绪提高优先级）
        if analysis.sentiment == "negative":
            if base_priority == FeedbackPriority.P3_LOW:
                base_priority = FeedbackPriority.P2_MEDIUM
        
        logger.info(f"Prioritized: {feedback.id} -> {base_priority.value}")
        
        return base_priority
    
    async def create_task(
        self,
        feedback: FeedbackItem,
        analysis: FeedbackAnalysis,
    ) -> Optional[Any]:
        """
        创建改进任务
        
        Args:
            feedback: 反馈项
            analysis: 反馈分析
        
        Returns:
            Request: 诉求（新任务），如果 request_board 不可用则返回 None
        """
        if not self.request_board:
            logger.warning("RequestBoard not available, cannot create task")
            return None
        
        from request_board.models import (
            Request,
            RequestType,
            RequestPriority,
            RequestStatus,
        )
        
        # 映射反馈优先级到诉求优先级
        priority_map = {
            FeedbackPriority.P0_CRITICAL: RequestPriority.CRITICAL,
            FeedbackPriority.P1_HIGH: RequestPriority.HIGH,
            FeedbackPriority.P2_MEDIUM: RequestPriority.NORMAL,
            FeedbackPriority.P3_LOW: RequestPriority.LOW,
        }
        
        request_priority = priority_map.get(
            analysis.priority,
            RequestPriority.NORMAL,
        )
        
        # 创建任务描述
        task_description = self._create_task_description(feedback, analysis)
        
        # 创建诉求
        request = Request(
            id=f"req_{feedback.id}",
            type=RequestType.COLLABORATION,
            priority=request_priority,
            status=RequestStatus.PENDING,
            from_agent="FeedbackProcessor",
            to_agent="all",
            subject=f"Feedback: {analysis.feedback_type.value} - {feedback.content[:50]}",
            content=task_description,
            context={
                "feedback_id": feedback.id,
                "feedback_type": analysis.feedback_type.value,
                "delivery_id": feedback.delivery_id,
                "keywords": analysis.keywords,
            },
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        
        # 添加到诉求看板
        await self.request_board.create_request(request)
        
        logger.info(
            f"Task created: {request.id} for feedback {feedback.id}"
        )
        
        return request
    
    async def trigger_iteration(
        self,
        task: Any,
    ) -> str:
        """
        触发新的迭代
        
        Args:
            task: 任务诉求
        
        Returns:
            str: 新工作流 ID
        """
        logger.info(f"Triggering iteration for task: {task.id}")
        
        # 这里可以触发新的工作流
        # 目前返回任务 ID 作为工作流 ID
        return f"workflow_{task.id}"
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 简单实现：查找预定义关键词
        all_keywords = []
        for keyword_list in self._type_keywords.values():
            all_keywords.extend(keyword_list)
        
        for keyword in all_keywords:
            if keyword in content:
                keywords.append(keyword)
        
        return keywords
    
    def _classify_feedback(
        self,
        content: str,
        keywords: List[str],
    ) -> FeedbackType:
        """分类反馈"""
        # 统计每种类型的匹配度
        type_scores = {ft: 0 for ft in FeedbackType}
        
        for feedback_type, type_keywords in self._type_keywords.items():
            for keyword in keywords:
                if keyword in type_keywords:
                    type_scores[feedback_type] += 1
        
        # 返回得分最高的类型
        best_type = max(type_scores, key=type_scores.get)
        
        if type_scores[best_type] == 0:
            return FeedbackType.OTHER
        
        return best_type
    
    def _analyze_sentiment(self, content: str) -> str:
        """情感分析（简化版）"""
        positive_words = [
            "good", "great", "excellent", "love", "like", "happy",
            "thanks", "thank", "awesome", "perfect",
        ]
        negative_words = [
            "bad", "terrible", "awful", "hate", "dislike", "angry",
            "frustrated", "disappointed", "worst", "horrible",
        ]
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"
    
    def _assess_impact(
        self,
        feedback_type: FeedbackType,
        content: str,
    ) -> str:
        """评估影响范围"""
        critical_keywords = [
            "crash", "data loss", "security", "corrupt",
            "broken", "cannot use", "blocking",
        ]
        
        high_keywords = [
            "major", "important", "critical", "urgent",
        ]
        
        for keyword in critical_keywords:
            if keyword in content:
                return "critical"
        
        for keyword in high_keywords:
            if keyword in content:
                return "high"
        
        if feedback_type == FeedbackType.BUG:
            return "medium"
        
        return "low"
    
    def _determine_priority(
        self,
        feedback_type: FeedbackType,
        sentiment: str,
        impact_scope: str,
        keywords: List[str],
    ) -> FeedbackPriority:
        """确定优先级"""
        # Bug 通常优先级较高
        if feedback_type == FeedbackType.BUG:
            if impact_scope == "critical":
                return FeedbackPriority.P0_CRITICAL
            elif impact_scope == "high":
                return FeedbackPriority.P1_HIGH
            else:
                return FeedbackPriority.P2_MEDIUM
        
        # 性能问题
        if feedback_type == FeedbackType.PERFORMANCE:
            if "slow" in keywords or "latency" in keywords:
                return FeedbackPriority.P1_HIGH
            return FeedbackPriority.P2_MEDIUM
        
        # 功能请求
        if feedback_type == FeedbackType.FEATURE:
            return FeedbackPriority.P3_LOW
        
        # 默认
        return FeedbackPriority.P2_MEDIUM
    
    def _calculate_confidence(
        self,
        keywords: List[str],
        feedback_type: FeedbackType,
    ) -> float:
        """计算置信度"""
        if not keywords:
            return 0.3
        
        # 统计匹配的关键词数量
        type_keywords = self._type_keywords.get(feedback_type, [])
        matches = sum(1 for kw in keywords if kw in type_keywords)
        
        # 置信度 = 匹配数 / 总关键词数
        confidence = min(1.0, matches / max(1, len(keywords)) + 0.5)
        
        return confidence
    
    def _create_task_description(
        self,
        feedback: FeedbackItem,
        analysis: FeedbackAnalysis,
    ) -> str:
        """创建任务描述"""
        description = f"""
# Feedback Task

## Original Feedback
- ID: {feedback.id}
- Type: {analysis.feedback_type.value}
- Priority: {analysis.priority.value}
- User: {feedback.user_id}

## Content
{feedback.content}

## Analysis
- Keywords: {', '.join(analysis.keywords)}
- Sentiment: {analysis.sentiment}
- Impact: {analysis.impact_scope}
- Confidence: {analysis.confidence:.2f}

## Action Required
Please address this feedback by:
1. Reviewing the issue
2. Implementing necessary changes
3. Testing the fix
4. Updating the delivery
"""
        return description
    
    def _generate_feedback_id(self) -> str:
        """生成反馈 ID"""
        timestamp = int(time.time() * 1000)
        data = f"feedback:{timestamp}"
        return "fb_" + hashlib.md5(data.encode()).hexdigest()[:12]
    
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
                logger.info(f"Feedback resolved: {feedback_id}")
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._feedback_items)
        
        by_type = {}
        by_priority = {}
        by_status = {}
        
        for feedback in self._feedback_items:
            by_type[feedback.type] = by_type.get(feedback.type, 0) + 1
            by_priority[feedback.priority] = by_priority.get(feedback.priority, 0) + 1
            by_status[feedback.status] = by_status.get(feedback.status, 0) + 1
        
        return {
            "total": total,
            "by_type": by_type,
            "by_priority": by_priority,
            "by_status": by_status,
            "queue_size": self._feedback_queue.qsize(),
        }

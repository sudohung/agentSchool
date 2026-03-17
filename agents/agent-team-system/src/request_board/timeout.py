"""超时监控 - 完整的超时管理和升级机制."""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EscalationLevel(Enum):
    """升级级别"""
    FIRST = "first"
    SECOND = "second"
    FINAL = "final"


@dataclass
class TimeoutConfig:
    """超时配置"""
    
    timeout_by_priority: Dict[str, int] = None
    escalation_threshold: Dict[str, int] = None
    escalation_targets: Dict[str, str] = None
    check_interval: int = 60
    max_escalations: int = 3
    
    def __post_init__(self):
        if self.timeout_by_priority is None:
            self.timeout_by_priority = {
                "low": 3600,
                "normal": 1800,
                "high": 900,
                "critical": 300,
            }
        
        if self.escalation_threshold is None:
            self.escalation_threshold = {
                "low": 1800,
                "normal": 900,
                "high": 300,
                "critical": 120,
            }
        
        if self.escalation_targets is None:
            self.escalation_targets = {
                "low": "Coordinator",
                "normal": "Tech Lead",
                "high": "Product Manager",
                "critical": "Product Manager",
            }
    
    def get_timeout(self, priority: str) -> int:
        return self.timeout_by_priority.get(priority, 1800)
    
    def get_escalation_threshold(self, priority: str) -> int:
        return self.escalation_threshold.get(priority, 900)
    
    def get_escalation_target(self, priority: str) -> str:
        return self.escalation_targets.get(priority, "Coordinator")


class TimeoutMonitor:
    """
    超时监控器
    
    功能：
    - 监控诉求处理时间
    - 自动升级超时诉求
    - 发送提醒通知
    - 记录超时历史
    """
    
    def __init__(
        self,
        request_board: Any,
        router_service: Optional[Any] = None,
        notification_service: Optional[Any] = None,
        config: Optional[TimeoutConfig] = None,
    ):
        self.request_board = request_board
        self.router_service = router_service
        self.notification_service = notification_service
        self.config = config or TimeoutConfig()
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._escalation_count: Dict[str, int] = {}
        self._timeout_history: List[Dict[str, Any]] = []
        self.max_history = 500
    
    async def start(self):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("TimeoutMonitor started")
    
    async def stop(self):
        """停止监控"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("TimeoutMonitor stopped")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._check_timeouts()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}")
                await asyncio.sleep(5)
    
    async def _check_timeouts(self):
        """检查超时诉求"""
        now = int(time.time())
        
        pending_requests = await self.request_board.get_all_requests()
        pending_requests = [
            r for r in pending_requests
            if r.status in ["pending", "processing", "waiting"]
        ]
        
        for request in pending_requests:
            age = now - request.created_at
            
            threshold = self.config.get_escalation_threshold(request.priority)
            
            if age >= threshold:
                await self._handle_timeout(request, age, threshold)
    
    async def _handle_timeout(
        self,
        request: Any,
        age: int,
        threshold: int,
    ):
        """处理超时诉求"""
        request_id = request.id
        escalation_count = self._escalation_count.get(request_id, 0)
        
        if escalation_count >= self.config.max_escalations:
            logger.warning(f"Request {request_id} reached max escalations")
            return
        
        escalation_level = self._get_escalation_level(escalation_count)
        escalation_target = self._get_next_escalation_target(
            request.priority,
            escalation_count
        )
        
        timeout_event = {
            "request_id": request_id,
            "age": age,
            "threshold": threshold,
            "escalation_level": escalation_level.value,
            "escalation_target": escalation_target,
            "timestamp": int(time.time()),
        }
        self._timeout_history.append(timeout_event)
        if len(self._timeout_history) > self.max_history:
            self._timeout_history = self._timeout_history[-self.max_history:]
        
        original_target = request.to_agent
        await self.request_board.update_request(
            request_id=request_id,
            updates={
                "status": "escalated",
                "context": {
                    **request.context,
                    "escalation": {
                        "level": escalation_level.value,
                        "original_target": original_target,
                        "escalated_to": escalation_target,
                        "escalated_at": int(time.time()),
                    }
                }
            }
        )
        
        self._escalation_count[request_id] = escalation_count + 1
        
        await self._send_escalation_notification(
            request,
            escalation_target,
            escalation_level,
            age,
        )
        
        logger.info(
            f"Escalated request {request_id} from {original_target} "
            f"to {escalation_target} (level: {escalation_level.value})"
        )
    
    def _get_escalation_level(self, count: int) -> EscalationLevel:
        if count == 0:
            return EscalationLevel.FIRST
        elif count == 1:
            return EscalationLevel.SECOND
        else:
            return EscalationLevel.FINAL
    
    def _get_next_escalation_target(
        self,
        priority: str,
        escalation_count: int,
    ) -> str:
        base_target = self.config.get_escalation_target(priority)
        
        escalation_chain = {
            "Coordinator": "Tech Lead",
            "Tech Lead": "Product Manager",
            "Product Manager": "Coordinator",
        }
        
        target = base_target
        for _ in range(escalation_count):
            target = escalation_chain.get(target, "Coordinator")
        
        return target
    
    async def _send_escalation_notification(
        self,
        request: Any,
        escalation_target: str,
        level: EscalationLevel,
        age: int,
    ):
        """发送升级通知"""
        if not self.notification_service:
            return
        
        priority_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "normal": "🟡",
            "low": "🟢",
        }
        
        emoji = priority_emoji.get(request.priority, "⚪")
        level_text = {
            EscalationLevel.FIRST: "首次升级",
            EscalationLevel.SECOND: "二次升级",
            EscalationLevel.FINAL: "最终升级",
        }
        
        message = (
            f"{emoji} **{level_text[level]}提醒**\n\n"
            f"诉求 #{request.id} 已等待 {age // 60} 分钟未响应\n\n"
            f"**主题**: {request.subject}\n"
            f"**优先级**: {request.priority}\n"
            f"**原始接收方**: {request.to_agent}\n\n"
            f"请及时处理。"
        )
        
        logger.info(f"Sending escalation notification to {escalation_target}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取超时统计"""
        now = int(time.time())
        
        recent_timeouts = [
            e for e in self._timeout_history
            if now - e["timestamp"] < 3600
        ]
        
        by_level = {}
        for event in recent_timeouts:
            level = event["escalation_level"]
            by_level[level] = by_level.get(level, 0) + 1
        
        return {
            "total_escalations": len(self._timeout_history),
            "recent_escalations_1h": len(recent_timeouts),
            "by_level": by_level,
            "escalation_counts": dict(self._escalation_count),
        }
    
    def get_timeout_history(
        self,
        request_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取超时历史"""
        history = self._timeout_history
        
        if request_id:
            history = [e for e in history if e["request_id"] == request_id]
        
        return history[-limit:]

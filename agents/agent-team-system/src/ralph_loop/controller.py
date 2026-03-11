"""迭代控制器 (简化版)."""

from __future__ import annotations

import asyncio
from typing import Optional, List
from datetime import datetime

from .config import RalphLoopConfig
from .state import LoopStatus, IterationState


class IterationController:
    """迭代控制器"""
    
    def __init__(self, config: Optional[RalphLoopConfig] = None):
        self.config = config or RalphLoopConfig()
        self.status = LoopStatus.IDLE
        self.current_iteration: Optional[IterationState] = None
        self.history: List[IterationState] = []
        self._lock = asyncio.Lock()
        self._running = False
    
    async def start(self, agents: List, team_session):
        """启动 Loop"""
        async with self._lock:
            if self.status != LoopStatus.IDLE:
                raise RuntimeError("Loop is already running")
            
            self.status = LoopStatus.RUNNING
            self._running = True
            
            self.current_iteration = IterationState(
                iteration_number=0,
                start_time=int(datetime.now().timestamp()),
                status=LoopStatus.RUNNING,
                agents_participating=[a.role for a in agents],
            )
    
    async def stop(self):
        """停止 Loop"""
        async with self._lock:
            self._running = False
            self.status = LoopStatus.STOPPED
            
            if self.current_iteration:
                self.current_iteration.end_time = int(datetime.now().timestamp())
                self.current_iteration.status = LoopStatus.STOPPED
                self.history.append(self.current_iteration)
    
    def get_current_iteration(self) -> Optional[IterationState]:
        """获取当前迭代"""
        return self.current_iteration
    
    def get_history(self) -> List[IterationState]:
        """获取历史"""
        return self.history

"""迭代控制器 - 完整版."""

from __future__ import annotations

import asyncio
from typing import Optional, List, Any
from datetime import datetime

from .config import RalphLoopConfig
from .state import LoopStatus, IterationState
from .setback import SetbackHandler, Setback
from .visualizer import IterationVisualizer, RealTimeMonitor


class IterationController:
    """
    迭代控制器 - 完整版
    
    功能:
    - 迭代控制
    - 挫折处理
    - 可视化监控
    - 性能分析
    """
    
    def __init__(self, config: Optional[RalphLoopConfig] = None):
        self.config = config or RalphLoopConfig()
        self.status = LoopStatus.IDLE
        self.current_iteration: Optional[IterationState] = None
        self.history: List[IterationState] = []
        self._lock = asyncio.Lock()
        self._running = False
        
        # 挫折处理
        self.setback_handler = SetbackHandler()
        
        # 可视化
        self.visualizer = IterationVisualizer()
        self.monitor = RealTimeMonitor(self.visualizer)
    
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
            
            # 启动可视化
            self.visualizer.start_iteration(agents)
    
    async def stop(self):
        """停止 Loop"""
        async with self._lock:
            self._running = False
            self.status = LoopStatus.STOPPED
            
            if self.current_iteration:
                self.current_iteration.end_time = int(datetime.now().timestamp())
                self.current_iteration.status = LoopStatus.STOPPED
                self.history.append(self.current_iteration)
            
            # 结束可视化
            self.visualizer.end_iteration()
    
    def get_current_iteration(self) -> Optional[IterationState]:
        """获取当前迭代"""
        return self.current_iteration
    
    def get_history(self) -> List[IterationState]:
        """获取历史"""
        return self.history

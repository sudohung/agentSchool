"""迭代控制器 - 完善版."""

from __future__ import annotations

import asyncio
from typing import Optional, List, Any, Dict
from datetime import datetime
import time

from .config import RalphLoopConfig
from .state import LoopStatus, IterationState
from .setback import SetbackHandler, Setback, SetbackType, SetbackSeverity
from .completion import CompletionChecker, CompletionCriteria
from .visualizer import IterationVisualizer


class IterationController:
    """
    迭代控制器 - 完善版
    
    管理 Ralph Loop 的完整生命周期
    """
    
    def __init__(self, config: Optional[RalphLoopConfig] = None):
        self.config = config or RalphLoopConfig()
        self.status = LoopStatus.IDLE
        self.current_iteration: Optional[IterationState] = None
        self.history: List[IterationState] = []
        self._lock = asyncio.Lock()
        self._running = False
        self._paused = False

        # 挫折处理
        self.setback_handler = SetbackHandler()
        
        # 完成度检查
        self.completion_checker = CompletionChecker(
            CompletionCriteria(
                requirement_coverage=self.config.completion_threshold,
            )
        )

        # 可视化
        self.visualizer = IterationVisualizer()
    
    async def start(self, agents: List, team_session):
        """启动 Loop"""
        async with self._lock:
            if self.status == LoopStatus.RUNNING:
                raise RuntimeError("Loop is already running")
            
            self.status = LoopStatus.RUNNING
            self._running = True
            self._paused = False

            self.current_iteration = IterationState(
                iteration_number=0,
                start_time=int(datetime.now().timestamp()),
                status=LoopStatus.RUNNING,
                agents_participating=[a.role for a in agents],
            )

            self.visualizer.start_iteration(agents)
    
    async def pause(self):
        """暂停 Loop"""
        async with self._lock:
            if self.status != LoopStatus.RUNNING:
                return
            self.status = LoopStatus.PAUSED
            self._paused = True

    async def resume(self):
        """恢复 Loop"""
        async with self._lock:
            if self.status != LoopStatus.PAUSED:
                return
            self.status = LoopStatus.RUNNING
            self._paused = False

    async def stop(self):
        """停止 Loop"""
        async with self._lock:
            self._running = False
            self._paused = False
            self.status = LoopStatus.STOPPED
            
            if self.current_iteration:
                self.current_iteration.end_time = int(datetime.now().timestamp())
                self.current_iteration.status = LoopStatus.STOPPED
                self.history.append(self.current_iteration)

            self.visualizer.end_iteration()
    
    async def execute_iteration(
        self,
        agents: List,
        execute_agent_func: Any,
    ) -> Dict[str, Any]:
        """
        执行一轮迭代

        Args:
            agents: Agent 列表
            execute_agent_func: 执行单个 Agent 的函数

        Returns:
            迭代结果
        """
        if not self._running:
            return {"success": False, "error": "Loop not running"}

        # 等待恢复
        while self._paused and self._running:
            await asyncio.sleep(0.5)

        if not self._running:
            return {"success": False, "error": "Loop stopped"}

        results = []
        errors = []

        # 并行执行
        if self.config.parallel_agents:
            tasks = [
                self._execute_with_recovery(agent, execute_agent_func)
                for agent in agents
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for agent in agents:
                result = await self._execute_with_recovery(agent, execute_agent_func)
                results.append(result)

        # 统计结果
        for result in results:
            if isinstance(result, Exception):
                errors.append(result)
                self.current_iteration.setbacks_encountered += 1
            elif isinstance(result, dict):
                self.current_iteration.documents_read += result.get("documents_read", 0)
                self.current_iteration.requests_processed += result.get("requests_processed", 0)
                self.current_iteration.documents_produced += result.get("documents_produced", 0)
                self.current_iteration.requests_posted += result.get("requests_posted", 0)

        # 更新迭代计数
        self.current_iteration.iteration_number += 1

        # 更新可視化
        self.visualizer.update_iteration(
            documents_read=self.current_iteration.documents_read,
            documents_produced=self.current_iteration.documents_produced,
            requests_processed=self.current_iteration.requests_processed,
            requests_posted=self.current_iteration.requests_posted,
            setbacks_count=self.current_iteration.setbacks_encountered,
        )

        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "iteration": self.current_iteration.iteration_number,
        }

    async def _execute_with_recovery(
        self,
        agent: Any,
        execute_func: Any,
    ) -> Dict:
        """
        带恢复机制的执行

        遏到挫折时尝试恢复
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                result = await execute_func(agent)
                return result

            except Exception as e:
                retry_count += 1

                # 记录挫折
                setback = await self.setback_handler.record_setback(
                    agent=agent,
                    iteration=self.current_iteration.iteration_number,
                    error=e,
                )

                # 尝试恢复
                if self.config.auto_recovery:
                    recovered = await self.setback_handler.attempt_recovery(setback)
                    if recovered:
                        continue

                # 无法恢复
                return {
                    "success": False,
                    "error": e,
                    "retries": retry_count,
                }

        return {
            "success": False,
            "error": Exception("Max retries exceeded"),
            "retries": max_retries,
        }

    async def check_completion(self, team_state: Dict) -> float:
        """检查完成度"""
        result = await self.completion_checker.check(team_state)
        self.current_iteration.completion_score = result["score"]
        return result["score"]

    def get_current_iteration(self) -> Optional[IterationState]:
        """获取当前迭代"""
        return self.current_iteration
    
    def get_history(self) -> List[IterationState]:
        """获取历史"""
        return self.history

    def get_setbacks(self) -> List[Setback]:
        """获取挫折列表"""
        return self.setback_handler.get_all_setbacks()

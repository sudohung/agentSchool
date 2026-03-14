"""工作流引擎."""

from __future__ import annotations

import asyncio
import time
from typing import List, Any, Optional, Dict
from dataclasses import dataclass

from .config import WorkflowConfig
from .context import WorkflowContext
from .coordinator import TeamCoordinator
from .quality import QualityGate
from ralph_loop.config import RalphLoopConfig


@dataclass
class WorkflowResult:
    """工作流结果"""
    success: bool
    team: List[Any]
    context: Optional[WorkflowContext]
    error: Optional[str] = None
    delivery_path: Optional[str] = None


class WorkflowEngine:
    """
    工作流引擎
    
    实现完整的 Agent 团队协作工作流
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        初始化工作流引擎
        
        Args:
            config: 工作流配置
        """
        self.config = config or WorkflowConfig()
        self.status = "initialized"
        self._lock = asyncio.Lock()
        self._running = False
        
        # 组件
        self.coordinator: Optional[TeamCoordinator] = None
        self.quality_gate = QualityGate()
        
        # 上下文
        self.context: Optional[WorkflowContext] = None
    
    async def start(
        self,
        team: List[Any],
        task_description: str,
        document_store: Any,
        request_board: Any,
        client: Any = None,
    ) -> WorkflowResult:
        """
        启动工作流
        
        Args:
            team: Agent 团队
            task_description: 任务描述
            document_store: 文档存储
            request_board: 诉求看板
            client: OpenCode 客户端
            
        Returns:
            WorkflowResult: 工作流结果
        """
        async with self._lock:
            if self._running:
                return WorkflowResult(
                    success=False,
                    team=[],
                    context=None,
                    error="Workflow already running",
                )
            
            self._running = True
            self.status = "running"
            
            # 1. 创建上下文
            self.context = WorkflowContext(
                workflow_id=self._generate_id("wf"),
                task_description=task_description,
                team=team,
                document_store=document_store,
                request_board=request_board,
                client=client,
            )
            
            # 2. 创建协调器
            self.coordinator = TeamCoordinator(
                context=self.context,
                config=self.config,
            )
            
            # 3. 执行工作流
            success = await self._execute_workflow()
            
            # 4. 返回结果
            return WorkflowResult(
                success=success,
                team=team,
                context=self.context,
                delivery_path=self.context.delivery_path if self.context else None,
            )
    
    async def _execute_workflow(self) -> bool:
        """执行工作流主循环"""
        try:
            iteration = 0
            max_iterations = self.config.ralph_config.max_iterations
            completion_threshold = self.config.ralph_config.completion_threshold
            
            while self._running and iteration < max_iterations:
                iteration += 1
                
                # 1. 执行一轮迭代
                if self.coordinator:
                    iteration_result = await self.coordinator.execute_iteration()
                else:
                    return False
                
                # 2. 更新上下文
                if self.context:
                    self.context.iteration_count += 1
                    self.context.total_documents += iteration_result.get("documents_produced", 0) if isinstance(iteration_result, dict) else 0
                    self.context.total_requests += iteration_result.get("requests_processed", 0) if isinstance(iteration_result, dict) else 0
                    self.context.total_setbacks += iteration_result.get("setbacks_count", 0) if isinstance(iteration_result, dict) else 0
                
                # 3. 检查完成度 (需要 5 个以上迭代才开始检查)
                if iteration >= 5:
                    completion_score = 0.0
                    if self.coordinator:
                        completion_score = await self.coordinator.check_completion()
                    
                    # 4. 检查是否达到完成阈值
                    if completion_score >= completion_threshold:
                        # 5. 质量检查
                        quality_result = await self.quality_gate.check(self.context) if self.context else None
                        
                        if quality_result and quality_result.passed:
                            # 6. 交付
                            delivery_path = await self._deliver()
                            if self.context:
                                self.context.delivery_path = delivery_path
                                self.context.quality_score = quality_result.overall_score
                            
                            self.status = "completed"
                            if self.context:
                                self.context.complete("quality_passed")
                            return True
                        else:
                            # 质量不通过，继续迭代
                            if self.context and quality_result:
                                self.context.metadata["quality_issues"] = quality_result.check_results
                            continue
                
                # 7. 检查挫折数量
                if self.context and self.context.total_setbacks >= self.config.ralph_config.max_setbacks:
                    self.status = "failed"
                    if self.context:
                        self.context.fail(f"Too many setbacks: {self.context.total_setbacks}")
                    return False
                
                # 8. 短暂延迟
                await asyncio.sleep(1)
            
            # 最大迭代次数到达
            self.status = "completed"
            if self.context:
                self.context.complete("max_iterations_reached")
            return True
            
        except Exception as e:
            self.status = "failed"
            if self.context:
                self.context.fail(str(e))
            return False
    
    async def _deliver(self) -> str:
        """交付产品"""
        # 整合所有文档到交付目录
        import os
        if self.context:
            delivery_path = f"{self.config.delivery_path_base}/{self.context.workflow_id}"
        else:
            delivery_path = f"{self.config.delivery_path_base}/workflow_{int(time.time())}"
        
        # 创建交付目录
        os.makedirs(delivery_path, exist_ok=True)
        
        # 获取文档并复制
        if self.context and self.context.document_store:
            documents = await self.context.document_store.list_documents()
            for i, doc in enumerate(documents):
                doc_path = os.path.join(delivery_path, f"doc_{i}_{getattr(doc, 'id', 'unknown')}.md")
                with open(doc_path, 'w', encoding='utf-8') as f:
                    content = getattr(doc, 'content', None)
                    if content and hasattr(content, 'content'):
                        f.write(content.content)
        
        return delivery_path
    
    def _generate_id(self, prefix: str) -> str:
        """生成 ID"""
        import hashlib
        import time
        timestamp = int(time.time() * 1000)
        data = f"{prefix}:{timestamp}"
        return f"{prefix}_{hashlib.md5(data.encode()).hexdigest()[:12]}"
    
    async def pause(self):
        """暂停工作流"""
        self.status = "paused"
        if self.coordinator:
            await self.coordinator.pause()
    
    async def resume(self):
        """恢复工作流"""
        self.status = "running"
        if self.coordinator:
            await self.coordinator.resume()
    
    async def stop(self):
        """停止工作流"""
        self._running = False
        self.status = "stopped"
        if self.coordinator:
            await self.coordinator.stop()
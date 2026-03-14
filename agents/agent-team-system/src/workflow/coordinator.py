"""团队协调器."""

from __future__ import annotations

import asyncio
import time
from typing import List, Any, Optional, Dict
from dataclasses import dataclass

from .config import WorkflowConfig
from .context import WorkflowContext
from ralph_loop.config import RalphLoopConfig
from ralph_loop.controller import IterationController
from ralph_loop.completion import CompletionChecker, CompletionCriteria


@dataclass
class IterationResult:
    """迭代结果"""
    success: bool
    documents_produced: int
    requests_processed: int
    setbacks_count: int
    errors: List[Exception]
    completion_score: float = 0.0


class TeamCoordinator:
    """
    团队协调器
    
    协调 Agent 团队执行 Ralph Loop
    """
    
    def __init__(
        self, 
        context: WorkflowContext, 
        config: Optional[WorkflowConfig] = None,
    ):
        """
        初始化协调器
        
        Args:
            context: 工作流上下文
            config: 工作流配置
        """
        self.context = context
        self.config = config
        
        # 初始化 Ralph Loop 组件
        ralph_config = getattr(config, 'ralph_config', None) or RalphLoopConfig()
        self.iteration_controller = IterationController(
            config=ralph_config,
        )
        self.completion_checker = CompletionChecker(
            criteria=CompletionCriteria(requirement_coverage=0.8)
        )
        
        # 状态
        self._paused = False
        self._stopped = False
        self._lock = asyncio.Lock()
    
    async def execute_iteration(self) -> IterationResult:
        """
        执行一轮迭代
        
        Returns:
            IterationResult: 迭代结果
        """
        async with self._lock:
            if self._stopped:
                return IterationResult(
                    success=False,
                    documents_produced=0,
                    requests_processed=0,
                    setbacks_count=0,
                    errors=[RuntimeError("Coordinator stopped")],
                )
            
            # 等待恢复
            while self._paused and not self._stopped:
                await asyncio.sleep(0.5)
            
            if self._stopped:
                return IterationResult(
                    success=False,
                    documents_produced=0,
                    requests_processed=0,
                    setbacks_count=0,
                    errors=[RuntimeError("Coordinator stopped")],
                )
        
        # 启动迭代控制器
        await self.iteration_controller.start(
            agents=self.context.team,
            team_session=self.context,
        )
        
        # 执行迭代
        result = await self._execute_agents_ralph_loop()
        
        # 停止迭代控制器
        await self.iteration_controller.stop()
        
        return result
    
    async def _execute_agents_ralph_loop(self) -> IterationResult:
        """执行所有 Agent 的 Ralph Loop"""
        tasks = []
        results = []
        errors = []
        
        for agent in self.context.team:
            task = asyncio.create_task(self._execute_agent_ralph(agent))
            tasks.append(task)
        
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        documents_produced = 0
        requests_processed = 0
        setbacks_count = 0
        
        for i, task_result in enumerate(task_results):
            if isinstance(task_result, Exception):
                errors.append(task_result)
                setbacks_count += 1
            elif isinstance(task_result, dict):
                results.append(task_result)
                documents_produced += task_result.get("documents_produced", 0)
                requests_processed += task_result.get("requests_processed", 0)
                setbacks_count += task_result.get("setbacks_count", 0)
        
        # 计算完成度
        completion_score = 0.0
        if self.context.team:
            team_state = await self._get_team_state()
            completion_result = await self.completion_checker.check(team_state)
            completion_score = completion_result.get("score", 0.0)
        
        return IterationResult(
            success=len(errors) == 0,
            documents_produced=documents_produced,
            requests_processed=requests_processed,
            setbacks_count=setbacks_count,
            errors=errors,
            completion_score=completion_score,
        )
    
    async def _execute_agent_ralph(self, agent: Any) -> Dict:
        """执行单个 Agent 的 Ralph Loop"""
        result = {
            "success": True,
            "documents_produced": 0,
            "requests_processed": 0,
            "setbacks_count": 0,
            "result": None,
        }
        
        try:
            # R - Read (阅读文档)
            docs = await agent.read_documents()
            result["documents_read"] = len(docs)
            
            # A - Act (响应诉求)
            requests = await agent.act_on_requests()
            result["requests_processed"] = len(requests)
            
            # L - Leverage (发挥专长)
            work_result = await agent.leverage_expertise()
            result["result"] = work_result
            
            # P - Produce (产出文档)
            if work_result:
                document = await agent.produce_document(work_result)
                if document:
                    # 保存到文档中心
                    await self.context.document_store.save(document)
                    if hasattr(self.context, 'add_document'):
                        self.context.add_document(document)
                    result["documents_produced"] = 1
            
            # H - Help (发布诉求)
            help_requests = await agent.help_requests()
            for req in help_requests:
                await self.context.request_board.create_request(req)
        
        except Exception as e:
            result["success"] = False
            result["error"] = e
            result["setbacks_count"] = 1
            if hasattr(self.context, 'record_setback'):
                self.context.record_setback()
        
        return result
    
    async def _get_team_state(self) -> Dict:
        """获取团队状态"""
        # 从文档中心和诉求看板收集信息
        documents = await self.context.document_store.list_documents(limit=100) if self.context.document_store else []
        requests = await self.context.request_board.get_all_requests() if self.context.request_board else []
        
        return {
            "requirement_coverage": self._calculate_requirement_coverage(),
            "document_completeness": self._calculate_document_completeness(documents),
            "request_resolution_rate": self._calculate_request_resolution_rate(requests),
            "quality_indicators": self._calculate_quality_indicators(documents),
        }
    
    def _calculate_requirement_coverage(self) -> float:
        """计算需求覆盖率"""
        # 简化实现：基于任务描述和产出文档的关系
        # 实际实现会更复杂
        docs_count = len(self.context.metadata.get('documents', [])) if self.context.metadata else 0
        return min(1.0, docs_count / 10)
    
    def _calculate_document_completeness(self, documents: List) -> float:
        """计算文档完整度"""
        if not documents:
            return 0.0
        # 简化计算
        return min(1.0, len(documents) / 20)
    
    def _calculate_request_resolution_rate(self, requests: List) -> float:
        """计算诉求解决率"""
        if not requests:
            return 0.0
        resolved = sum(1 for req in requests if getattr(req, 'status', None) == 'resolved')
        return resolved / len(requests) if len(requests) > 0 else 0.0
    
    def _calculate_quality_indicators(self, documents: List) -> Dict:
        """计算质量指标"""
        if not documents:
            return {
                "avg_length": 0,
                "doc_types_covered": 0,
            }
        
        total_length = sum(len(getattr(doc, 'content', {}).get('content', '')) for doc in documents)
        avg_length = total_length / len(documents) if len(documents) > 0 else 0
        doc_types_count = len(set(getattr(doc, 'metadata', {}).get('doc_type', '') for doc in documents))
        
        return {
            "avg_length": avg_length,
            "doc_types_covered": doc_types_count,
        }
    
    async def check_completion(self) -> float:
        """检查完成度"""
        team_state = await self._get_team_state()
        result = await self.completion_checker.check(team_state)
        return result.get("score", 0.0)
    
    async def pause(self):
        """暂停协调器"""
        async with self._lock:
            self._paused = True
            if hasattr(self.iteration_controller, 'pause'):
                await self.iteration_controller.pause()
    
    async def resume(self):
        """恢复协调器"""
        async with self._lock:
            self._paused = False
            if hasattr(self.iteration_controller, 'resume'):
                await self.iteration_controller.resume()
    
    async def stop(self):
        """停止协调器"""
        async with self._lock:
            self._stopped = True
            if self.iteration_controller:
                await self.iteration_controller.stop()
    
    async def deliver(self) -> str:
        """交付产品"""
        # 整合所有文档到交付目录
        import os
        delivery_path = f"./deliveries/{getattr(self.context, 'workflow_id', f'workflow_{int(time.time())}')}"
        
        documents = await self.context.document_store.list_documents() if self.context.document_store else []
        
        os.makedirs(delivery_path, exist_ok=True)
        
        for i, doc in enumerate(documents):
            doc_path = os.path.join(delivery_path, f"doc_{i}_{getattr(doc, 'id', 'unknown')}.md")
            with open(doc_path, 'w', encoding='utf-8') as f:
                content_obj = getattr(doc, 'content', None)
                if content_obj and hasattr(content_obj, 'content'):
                    f.write(content_obj.content)
        
        return delivery_path
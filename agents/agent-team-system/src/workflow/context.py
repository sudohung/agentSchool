"""工作流上下文."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict
import time


@dataclass
class WorkflowContext:
    """
    工作流上下文
    
    存储工作流运行时的所有状态
    """
    
    # 基础信息
    workflow_id: str
    task_description: str
    team: List[Any]  # Agent 列表
    
    # 依赖组件
    document_store: Any
    request_board: Any
    client: Any = None
    
    # 运行时状态
    status: str = "initialized"
    iteration_count: int = 0
    start_time: int = field(default_factory=lambda: int(time.time()))
    end_time: Optional[int] = None
    
    # 统计数据
    total_documents: int = 0
    total_requests: int = 0
    total_setbacks: int = 0
    quality_score: float = 0.0
    
    # 迭代数据
    current_iteration: Optional[Any] = None
    iteration_history: List[Any] = field(default_factory=list)
    
    # 交付数据
    delivery_path: Optional[str] = None
    completion_reason: Optional[str] = None
    error: Optional[str] = None
    
    # 扩展数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.workflow_id:
            self.workflow_id = f"workflow_{int(time.time())}"
    
    def add_document(self, document: Any):
        """添加文档到统计"""
        self.total_documents += 1
        self.metadata.setdefault("documents", []).append(document)
    
    def add_request(self, request: Any):
        """添加诉求到统计"""
        self.total_requests += 1
        self.metadata.setdefault("requests", []).append(request)
    
    def record_setback(self):
        """记录挫折"""
        self.total_setbacks += 1
    
    def get_duration(self) -> int:
        """获取运行时长"""
        if self.end_time:
            return self.end_time - self.start_time
        return int(time.time()) - self.start_time
    
    def complete(self, reason: str = "completed"):
        """标记完成"""
        self.status = "completed"
        self.completion_reason = reason
        self.end_time = int(time.time())
    
    def fail(self, error: str):
        """标记失败"""
        self.status = "failed"
        self.error = error
        self.end_time = int(time.time())
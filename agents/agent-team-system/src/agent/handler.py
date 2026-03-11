"""权限/问题处理器."""

from __future__ import annotations

import re
from typing import Optional, List, Dict, Any
from .permissions import (
    PermissionRequest,
    PermissionResponse,
    PermissionAction,
    PermissionType,
    QuestionRequest,
    QuestionResponse,
)


class PermissionQuestionHandler:
    """
    权限/问题处理器
    
    处理权限请求和问题
    实现三层响应机制：缓存→规则→用户
    """
    
    def __init__(self, auto_allow_patterns: Optional[List[str]] = None):
        # 自动允许的模式
        self.auto_allow_patterns = auto_allow_patterns or [
            r"^read:.*\.md$",
            r"^read:.*\.txt$",
            r"^read:.*\.json$",
        ]
        
        # 权限缓存
        self.permission_cache: Dict[str, PermissionAction] = {}
        
        # 待处理请求
        self.pending_permissions: List[PermissionRequest] = []
        self.pending_questions: List[QuestionRequest] = []
    
    async def handle_permission(
        self,
        request: PermissionRequest,
    ) -> PermissionResponse:
        """
        处理权限请求
        
        优先级：
        1. 检查缓存
        2. 检查自动规则
        3. 加入待处理队列
        """
        # 1. 检查缓存
        cache_key = f"{request.type.value}:{request.resource}"
        if cache_key in self.permission_cache:
            return PermissionResponse(
                request_id=request.id,
                action=self.permission_cache[cache_key],
                reason="From cache",
            )
        
        # 2. 检查自动允许规则
        if self._matches_auto_allow(request):
            if request.remember:
                self.permission_cache[cache_key] = PermissionAction.ALLOW
            return PermissionResponse(
                request_id=request.id,
                action=PermissionAction.ALLOW,
                reason="Auto allowed",
            )
        
        # 3. 加入待处理队列
        self.pending_permissions.append(request)
        
        return PermissionResponse(
            request_id=request.id,
            action=PermissionAction.ASK,
            reason="Pending user approval",
        )
    
    async def handle_question(
        self,
        request: QuestionRequest,
    ) -> Optional[QuestionResponse]:
        """
        处理问题请求
        
        1. 检查是否可以自动回答
        2. 加入待处理队列
        """
        # 1. 检查自动回答
        auto_answer = await self._auto_answer_question(request)
        if auto_answer:
            return QuestionResponse(
                request_id=request.id,
                answers=auto_answer,
            )
        
        # 2. 加入待处理队列
        self.pending_questions.append(request)
        return None
    
    def _matches_auto_allow(self, request: PermissionRequest) -> bool:
        """检查是否匹配自动允许规则"""
        resource_pattern = f"{request.type.value}:{request.resource}"
        for pattern in self.auto_allow_patterns:
            if re.match(pattern, resource_pattern):
                return True
        return False
    
    async def _auto_answer_question(
        self,
        request: QuestionRequest,
    ) -> Optional[List[str]]:
        """自动回答问题"""
        # 简化实现，可以根据预设规则回答
        return None
    
    def get_pending_requests(self) -> Dict[str, List]:
        """获取所有待处理请求"""
        return {
            "permissions": self.pending_permissions,
            "questions": self.pending_questions,
        }
    
    def clear_pending(self):
        """清空待处理队列"""
        self.pending_permissions = []
        self.pending_questions = []

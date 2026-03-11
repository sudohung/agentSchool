"""诉求看板管理 (简化版)."""

from __future__ import annotations

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import Request, RequestStatus, RequestType, RequestPriority, RequestResponse


class RequestBoard:
    """诉求看板"""
    
    def __init__(self):
        self._requests: Dict[str, Request] = {}
        self._agent_index: Dict[str, List[str]] = {}
        self._status_index: Dict[str, List[str]] = {}
        self._responses: Dict[str, List[RequestResponse]] = {}
        self._lock = asyncio.Lock()
    
    async def create_request(self, request: Request) -> str:
        """创建诉求"""
        async with self._lock:
            if not request.id:
                request.id = self._generate_id()
            self._requests[request.id] = request
            self._update_indices(request)
            return request.id
    
    async def get_request(self, request_id: str) -> Optional[Request]:
        """获取诉求"""
        return self._requests.get(request_id)
    
    async def update_request(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """更新诉求"""
        async with self._lock:
            if request_id not in self._requests:
                return False
            
            request = self._requests[request_id]
            for key, value in updates.items():
                if hasattr(request, key):
                    setattr(request, key, value)
            
            request.updated_at = int(datetime.now().timestamp())
            return True
    
    async def get_requests_for_agent(
        self,
        agent_role: str,
        status: Optional[RequestStatus] = None,
        limit: int = 100,
    ) -> List[Request]:
        """获取 Agent 的诉求"""
        request_ids = self._agent_index.get(agent_role, [])
        results = []
        
        for request_id in request_ids:
            request = self._requests.get(request_id)
            if not request:
                continue
            
            if status and request.status != status.value:
                continue
            
            results.append(request)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def add_response(
        self,
        request_id: str,
        response: RequestResponse,
    ) -> bool:
        """添加响应"""
        async with self._lock:
            if request_id not in self._requests:
                return False
            
            if request_id not in self._responses:
                self._responses[request_id] = []
            
            self._responses[request_id].append(response)
            
            request = self._requests[request_id]
            request.status = RequestStatus.RESOLVED.value
            request.response = response.content
            request.responded_at = response.timestamp
            request.responded_by = response.from_agent
            
            return True
    
    def _update_indices(self, request: Request):
        """更新索引"""
        for agent in [request.from_agent, request.to_agent]:
            if agent not in self._agent_index:
                self._agent_index[agent] = []
            self._agent_index[agent].append(request.id)
        
        if request.status not in self._status_index:
            self._status_index[request.status] = []
        self._status_index[request.status].append(request.id)
    
    def _generate_id(self) -> str:
        """生成 ID"""
        import hashlib
        timestamp = int(datetime.now().timestamp() * 1000)
        data = f"request:{timestamp}"
        return "req_" + hashlib.md5(data.encode()).hexdigest()[:12]

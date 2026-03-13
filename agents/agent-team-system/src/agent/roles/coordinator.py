"""协调员 Agent."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from agent.base import Agent
from agent.config import Document, DocumentType, DocumentMetadata, DocumentContent, Request, RequestType, RequestPriority, RequestStatus
from agent.permissions import PermissionRequest, QuestionRequest


class CoordinatorAgent(Agent):
    """
    协调员 Agent
    
    职责：团队协调、进度跟踪、资源调度、权限/问题批量处理
    产出：Status_Report.md、进度报告
    """
    
    def __init__(self, session=None, client=None):
        super().__init__(
            role="Coordinator",
            expertise=["项目管理", "团队协调", "进度管理", "风险管理", "沟通技巧", "问题解决", "文档管理", "资源调度"],
            session=session,
            client=client,
        )
        self._pending_permissions: List[PermissionRequest] = []
        self._pending_questions: List[QuestionRequest] = []
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            docs = await self.document_hub.list_documents(limit=20)
            documents.extend(docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """A - 响应诉求"""
        processed = []
        
        if self.request_board:
            pending = await self.request_board.get_requests_for_agent(
                agent_role=self.role,
                status=RequestStatus.PENDING,
            )
            
            for request in pending:
                if request.type == RequestType.COLLABORATION:
                    await self._handle_collaboration(request)
                    processed.append(request)
                elif request.type == RequestType.NOTIFICATION:
                    await self._handle_notification(request)
                    processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """L - 发挥专业能力"""
        result = await self.send_message("""
作为项目协调者，请分析当前项目状态：

1. 汇总各角色工作进度
2. 识别进度风险和阻塞
3. 评估资源利用效率
4. 制定调整建议
5. 更新项目计划

输出项目状态报告和协调建议。
""")
        return result
    
    async def produce_document(self, work_result: Any) -> Document:
        """P - 产出文档"""
        import time
        
        content = self._format_status_report(work_result)
        
        return Document(
            id=self._generate_id("status"),
            path="reports/Status_Report.md",
            metadata=DocumentMetadata(
                title="项目状态报告",
                doc_type=DocumentType.OTHER,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["项目", "状态", "报告"],
            ),
            content=DocumentContent(
                content=content,
                format="markdown",
            ),
        )
    
    async def help_requests(self) -> List[Request]:
        """H - 发布诉求"""
        import time
        
        requests = []
        
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.COLLABORATION,
            priority=RequestPriority.HIGH,
            from_agent=self.role,
            to_agent="Product Manager",
            subject="请确认优先级调整",
            content="基于当前进度，建议调整以下任务优先级",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def collect_permission_request(self, request: PermissionRequest) -> None:
        """收集权限请求"""
        self._pending_permissions.append(request)
    
    def collect_question_request(self, request: QuestionRequest) -> None:
        """收集问题请求"""
        self._pending_questions.append(request)
    
    def get_pending_permissions(self) -> List[PermissionRequest]:
        """获取待处理权限请求"""
        return self._pending_permissions.copy()
    
    def get_pending_questions(self) -> List[QuestionRequest]:
        """获取待处理问题请求"""
        return self._pending_questions.copy()
    
    def clear_processed(self) -> None:
        """清空已处理的请求"""
        self._pending_permissions.clear()
        self._pending_questions.clear()
    
    async def _handle_collaboration(self, request: Request):
        """处理协作请求"""
        pass
    
    async def _handle_notification(self, request: Request):
        """处理通知请求"""
        pass
    
    def _format_status_report(self, work_result: Any) -> str:
        """格式化状态报告"""
        return f"""# 项目状态报告

## 1. 项目概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 进度汇总

### 已完成
- [x] 任务 1
- [x] 任务 2

### 进行中
- [ ] 任务 3 (80%)
- [ ] 任务 4 (50%)

### 待开始
- [ ] 任务 5

## 3. 风险和阻塞

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 风险 1 | 高 | 措施 1 |

## 4. 资源状态

| 角色 | 状态 | 工作负载 |
|------|------|---------|
| Frontend | 正常 | 80% |

## 5. 下周计划

- 计划 1
- 计划 2

## 6. 需要关注

- 关注点 1
- 关注点 2
"""

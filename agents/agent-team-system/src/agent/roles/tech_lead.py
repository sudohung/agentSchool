"""技术负责人 Agent."""

from __future__ import annotations

from typing import List, Any
from agent.base import Agent
from agent.config import Document, DocumentType, DocumentMetadata, DocumentContent, Request, RequestType, RequestPriority, RequestStatus


class TechLeadAgent(Agent):
    """
    技术负责人 Agent
    
    职责：技术方案、任务分解、代码审查
    产出：Tech_Design.md、任务列表
    """
    
    def __init__(self, session=None, client=None):
        super().__init__(
            role="Tech Lead",
            expertise=["技术规划", "任务分解", "代码审查", "团队协调", "质量管理"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            docs = await self.document_hub.list_documents(
                doc_type=DocumentType.ARCHITECTURE,
                limit=10,
            )
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
                if "细化" in request.subject:
                    await self._detail_plan(request)
                    processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """L - 发挥专业能力"""
        result = await self.send_message("""
作为技术负责人，请制定技术方案：

1. 细化架构设计
2. 分解开发任务
3. 制定技术规范
4. 评估工作量
5. 制定开发计划

输出技术方案文档和任务列表。
""")
        return result
    
    async def produce_document(self, work_result: Any) -> Document:
        """P - 产出文档"""
        import time
        
        content = self._format_tech_design(work_result)
        
        return Document(
            id=self._generate_id("tech"),
            path="design/Tech_Design.md",
            metadata=DocumentMetadata(
                title="技术方案设计",
                doc_type=DocumentType.TECH_DESIGN,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["技术", "设计"],
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
        
        # 请求开发人员评估
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.COLLABORATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Backend Developer",
            subject="请评估开发工作量",
            content="基于技术方案，请评估开发工作量",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_tech_design(self, work_result: Any) -> str:
        """格式化技术设计文档"""
        return f"""# 技术方案设计

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 任务分解

### 阶段 1: 基础架构
- [ ] 任务 1
- [ ] 任务 2

### 阶段 2: 核心功能
- [ ] 任务 3
- [ ] 任务 4

## 3. 技术规范

### 代码规范
- 命名规范
- 注释规范

### 接口规范
- RESTful API
- GraphQL

## 4. 工作量评估

| 任务 | 工时 (天) | 负责人 |
|------|----------|--------|
| 任务 1 | 3 | Developer |

## 5. 开发计划

### Week 1
- 任务 1
- 任务 2

### Week 2
- 任务 3
- 任务 4
"""
    
    async def _detail_plan(self, request: Request):
        """细化方案"""
        pass

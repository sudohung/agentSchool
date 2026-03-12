"""产品经理 Agent."""

from __future__ import annotations

from typing import List, Dict, Any
from agent.base import Agent
from agent.config import Document, DocumentType, DocumentMetadata, DocumentContent, Request, RequestType, RequestPriority, RequestStatus


class ProductManagerAgent(Agent):
    """
    产品经理 Agent
    
    职责：需求分析、产品规划、优先级排序
    产出：PRD.md、用户故事、需求列表
    """
    
    def __init__(self, session=None, client=None):
        super().__init__(
            role="Product Manager",
            expertise=["需求分析", "产品规划", "用户调研", "竞品分析", "优先级排序"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            # 阅读用户需求文档
            docs = await self.document_hub.list_documents(
                doc_type=DocumentType.PRD,
                limit=10,
            )
            documents.extend(docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """A - 响应诉求"""
        processed = []
        
        if self.request_board:
            # 处理需求澄清请求
            pending = await self.request_board.get_requests_for_agent(
                agent_role=self.role,
                status=RequestStatus.PENDING,
            )
            
            for request in pending:
                if request.type == RequestType.CLARIFICATION:  # type: ignore
                    # 澄清需求
                    await self._handle_clarification(request)
                    processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """L - 发挥专业能力"""
        result = await self.send_message("""
作为产品经理，请分析以下需求：

1. 识别核心功能和用户价值
2. 创建用户故事 (As a... I want... So that...)
3. 定义验收标准 (Given/When/Then)
4. 确定优先级 (MoSCoW 方法)
5. 识别风险和依赖

输出结构化的分析结果。
""")
        return result
    
    async def produce_document(self, work_result: Any) -> Document:
        """P - 产出文档"""
        import time
        
        content = self._format_prd(work_result)
        
        return Document(
            id=self._generate_id("prd"),
            path="prd/PRD_v1.md",
            metadata=DocumentMetadata(
                title="产品需求文档",
                doc_type=DocumentType.PRD,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["需求", "PRD"],
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
        
        # 请求技术可行性评估
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.REVIEW,
            priority=RequestPriority.HIGH,
            from_agent=self.role,
            to_agent="System Architect",
            subject="请评估技术可行性",
            content="基于 PRD，请评估技术可行性和风险",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_prd(self, work_result: Any) -> str:
        """格式化 PRD 文档"""
        return f"""# 产品需求文档

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 用户故事

### 用户故事 1
- **As a** 用户
- **I want** 功能
- **So that** 价值

### 验收标准
- Given 条件
- When 操作
- Then 结果

## 3. 功能优先级

### Must Have (必须有)
- 核心功能 1
- 核心功能 2

### Should Have (应该有)
- 重要功能 1

### Could Have (可以有)
- 可选功能 1

### Won't Have (本次没有)
- 延期功能 1

## 4. 风险和依赖

### 技术风险
- 风险 1
- 风险 2

### 依赖
- 依赖 1
- 依赖 2
"""
    
    async def _handle_clarification(self, request: Request):
        """处理需求澄清请求"""
        # 实现澄清逻辑
        pass

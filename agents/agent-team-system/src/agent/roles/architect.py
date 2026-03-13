"""系统架构师 Agent."""

from __future__ import annotations

from typing import List, Any
from agent.base import Agent
from agent.config import Document, DocumentType, DocumentMetadata, DocumentContent, Request, RequestType, RequestPriority, RequestStatus


class SystemArchitectAgent(Agent):
    """
    系统架构师 Agent
    
    职责：系统架构设计、技术选型
    产出：Architecture.md、技术栈文档
    """
    
    def __init__(self, session=None, client=None):
        super().__init__(
            role="System Architect",
            expertise=["系统架构设计", "技术选型", "微服务架构", "数据库设计", "性能优化", "安全设计"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            # 阅读 PRD 文档
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
            pending = await self.request_board.get_requests_for_agent(
                agent_role=self.role,
                status=RequestStatus.PENDING,
            )
            
            for request in pending:
                if "技术可行性" in request.subject:
                    await self._assess_feasibility(request)
                    processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """L - 发挥专业能力"""
        result = await self.send_message("""
作为系统架构师，请设计系统架构：

1. 选择合适的架构模式 (单体/微服务/Serverless)
2. 选择技术栈 (前端/后端/数据库)
3. 设计系统组件和交互
4. 定义技术约束和规范
5. 识别技术风险和缓解措施

输出架构设计文档。
""")
        return result
    
    async def produce_document(self, work_result: Any) -> Document:
        """P - 产出文档"""
        import time
        
        content = self._format_architecture(work_result)
        
        return Document(
            id=self._generate_id("arch"),
            path="design/Architecture.md",
            metadata=DocumentMetadata(
                title="系统架构设计",
                doc_type=DocumentType.ARCHITECTURE,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["架构", "设计"],
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
        
        # 请求 Tech Lead 细化方案
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.COLLABORATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Tech Lead",
            subject="请细化技术方案",
            content="基于架构设计，请细化具体技术方案",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_architecture(self, work_result: Any) -> str:
        """格式化架构文档"""
        return f"""# 系统架构设计

## 1. 架构模式

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 技术栈

### 前端
- 框架：React/Vue
- 语言：TypeScript
- 状态管理：Redux/Pinia

### 后端
- 语言：Python/Java/Go
- 框架：FastAPI/Spring
- 数据库：PostgreSQL/MongoDB

### 基础设施
- 容器：Docker
- 编排：Kubernetes
- 云服务：AWS/Azure

## 3. 系统组件

### 组件图
```
[用户界面] → [API 网关] → [微服务] → [数据库]
```

## 4. 技术约束

- 性能要求
- 安全要求
- 合规要求

## 5. 风险和缓解

### 技术风险
- 风险 1：缓解措施
- 风险 2：缓解措施
"""
    
    async def _assess_feasibility(self, request: Request):
        """评估技术可行性"""
        pass

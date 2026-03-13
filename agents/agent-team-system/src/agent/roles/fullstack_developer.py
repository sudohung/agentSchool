"""全栈开发 Agent."""

from __future__ import annotations

import time
from typing import List, Any
from agent.base import Agent
from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)


class FullStackDeveloperAgent(Agent):
    """
    全栈开发 Agent
    
    职责：
    - 全栈功能开发
    - 快速原型实现
    - 端到端测试
    - 部署上线
    
    产出：
    - code/fullstack/
    - docs/Feature_Docs.md
    """
    
    def __init__(self, session=None, client=None):
        """初始化全栈开发 Agent."""
        super().__init__(
            role="Full Stack Developer",
            expertise=[
                "前端开发",
                "后端开发",
                "数据库设计",
                "部署",
                "DevOps",
            ],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """
        R - 阅读文档
        
        阅读内容：
        - PRD 文档
        - 架构设计
        - 技术规范
        
        Returns:
            阅读到的文档列表
        """
        documents = []
        
        if self.document_hub:
            prd_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.PRD,
                limit=5,
            )
            documents.extend(prd_docs)
            
            arch_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.ARCHITECTURE,
                limit=5,
            )
            documents.extend(arch_docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """
        A - 响应诉求
        
        处理诉求：
        - 功能开发请求 (from Product Manager)
        - 原型实现请求
        
        Returns:
            处理过的诉求列表
        """
        processed = []
        
        if self.request_board:
            pending = await self.request_board.get_requests_for_agent(
                agent_role=self.role,
                status=RequestStatus.PENDING,
            )
            
            for request in pending:
                await self._handle_feature_request(request)
                processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """
        L - 发挥专业能力
        
        执行全栈开发工作：
        1. 分析需求
        2. 设计架构
        3. 实现前端
        4. 实现后端
        5. 集成测试
        
        Returns:
            工作结果
        """
        result = await self.send_message("""
        作为全栈开发工程师，请实现完整功能：
        
        1. 需求分析
           - 功能需求
           - 技术需求
           - 性能需求
        
        2. 架构设计
           - 前端架构
           - 后端架构
           - 数据库设计
        
        3. 前端实现
           - UI 组件
           - 状态管理
           - API 对接
        
        4. 后端实现
           - API 接口
           - 业务逻辑
           - 数据存储
        
        5. 测试验证
           - 单元测试
           - 集成测试
           - 端到端测试
        
        请输出完整的实现方案。
        """)
        
        return result
    
    async def produce_document(self, work_result: Any) -> Document:
        """
        P - 产出文档
        
        Args:
            work_result: 工作结果
            
        Returns:
            产出的文档
        """
        content = self._format_feature_doc(work_result)
        
        return Document(
            id=self._generate_id("fs"),
            path="docs/Feature_Docs.md",
            metadata=DocumentMetadata(
                title="功能文档",
                doc_type=DocumentType.CODE,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["全栈", "功能", "实现"],
            ),
            content=DocumentContent(
                content=content,
                format="markdown",
            ),
        )
    
    async def help_requests(self) -> List[Request]:
        """
        H - 发布诉求
        
        Returns:
            发布的诉求列表
        """
        requests = []
        
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.REVIEW,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Code Reviewer",
            subject="请求代码审查",
            content="请审查全栈代码实现",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.COLLABORATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="QA Engineer",
            subject="请求测试",
            content="请测试功能实现",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_feature_doc(self, work_result: Any) -> str:
        """格式化功能文档"""
        return f"""# 功能文档

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 技术架构

### 2.1 前端
- 框架: React
- 状态管理: Redux
- UI 组件库: Ant Design

### 2.2 后端
- 语言: Python
- 框架: FastAPI
- 数据库: PostgreSQL

### 2.3 部署
- 容器: Docker
- 编排: Kubernetes

## 3. 数据库设计

### 3.1 表结构
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 4. API 接口

### 4.1 用户接口
- POST /api/users - 创建用户
- GET /api/users - 获取用户列表
- GET /api/users/:id - 获取用户详情
- PUT /api/users/:id - 更新用户
- DELETE /api/users/:id - 删除用户

## 5. 前端组件

### 5.1 页面组件
- UserList - 用户列表页
- UserDetail - 用户详情页
- UserForm - 用户表单

### 5.2 公共组件
- Header - 头部导航
- Footer - 底部信息
- Loading - 加载状态

## 6. 测试

### 6.1 单元测试
- 前端组件测试
- 后端接口测试
- 数据库操作测试

### 6.2 集成测试
- API 集成测试
- 端到端测试
"""
    
    async def _handle_feature_request(self, request: Request):
        """处理功能请求"""
        pass
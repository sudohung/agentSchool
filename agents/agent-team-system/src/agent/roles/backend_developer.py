"""后端开发 Agent."""

from __future__ import annotations

import time
from typing import List, Any
from agent.base import Agent
from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)


class BackendDeveloperAgent(Agent):
    """
    后端开发 Agent
    
    职责：
    - 开发 API 接口
    - 实现业务逻辑
    - 数据库设计
    - 性能优化
    - 安全实现
    - 单元测试
    
    产出：
    - backend/API_Docs.md
    - backend/DB_Schema.md
    - code/backend/
    """
    
    def __init__(self, session=None, client=None):
        """初始化后端开发 Agent."""
        super().__init__(
            role="Backend Developer",
            expertise=[
                "Python/Java/Go",
                "RESTful API",
                "数据库设计",
                "缓存",
                "消息队列",
                "微服务",
                "性能优化",
            ],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """
        R - 阅读文档
        
        阅读内容：
        - PRD 文档 (了解业务需求)
        - 架构设计文档 (了解系统架构)
        - 数据库设计文档 (了解数据模型)
        - API 设计文档 (了解接口规范)
        
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
            
            tech_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.TECH_DESIGN,
                limit=5,
            )
            documents.extend(tech_docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """
        A - 响应诉求
        
        处理诉求：
        - API 开发请求 (from Frontend Developer)
        - 业务逻辑实现请求 (from Product Manager)
        - 后端 Bug 修复请求 (from QA Engineer)
        - 性能优化请求 (from Tech Lead)
        
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
                if "API" in request.subject:
                    await self._handle_api_development(request)
                elif "Bug" in request.subject:
                    await self._handle_bug_fix(request)
                elif "性能" in request.subject:
                    await self._handle_performance_optimization(request)
                
                processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """
        L - 发挥专业能力
        
        执行后端开发工作：
        1. 设计 API 接口
        2. 实现业务逻辑
        3. 设计数据库模型
        4. 优化性能
        5. 编写测试
        
        Returns:
            工作结果
        """
        result = await self.send_message("""
        作为后端开发工程师，请根据以下需求实现后端功能：
        
        1. API 设计
           - RESTful 规范
           - 接口定义
           - 参数验证
        
        2. 业务逻辑实现
           - 核心业务流程
           - 数据处理
           - 异常处理
        
        3. 数据库设计
           - 表结构设计
           - 索引优化
           - 关系映射
        
        4. 安全实现
           - 认证授权
           - 数据验证
           - SQL 注入防护
        
        5. 性能优化
           - 查询优化
           - 缓存策略
           - 异步处理
        
        请输出：
        - API 接口设计
        - 核心代码实现
        - 数据库 Schema
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
        content = self._format_api_doc(work_result)
        
        return Document(
            id=self._generate_id("be"),
            path="backend/API_Docs.md",
            metadata=DocumentMetadata(
                title="API 接口文档",
                doc_type=DocumentType.API_DOC,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["后端", "API", "接口"],
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
            type=RequestType.CLARIFICATION,
            priority=RequestPriority.HIGH,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="System Architect",
            subject="请求架构设计确认",
            content="请确认后端架构设计是否符合要求",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.REVIEW,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Tech Lead",
            subject="请求代码审查",
            content="请审查后端代码实现",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_api_doc(self, work_result: Any) -> str:
        """格式化 API 文档"""
        return f"""# API 接口文档

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 接口列表

### 2.1 用户认证

#### POST /api/v1/auth/login
**描述**: 用户登录
**请求体**:
```json
{{
  "username": "string",
  "password": "string"
}}
```
**响应**:
```json
{{
  "code": 200,
  "data": {{
    "token": "string",
    "user": {{}}
  }}
}}
```

#### POST /api/v1/auth/logout
**描述**: 用户登出
**请求头**: Authorization: Bearer <token>

### 2.2 用户管理

#### GET /api/v1/users
**描述**: 获取用户列表
**参数**:
- page: 页码
- size: 每页数量

#### POST /api/v1/users
**描述**: 创建用户
**请求体**:
```json
{{
  "username": "string",
  "email": "string",
  "password": "string"
}}
```

## 3. 数据库 Schema

### users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| username | VARCHAR(50) | 用户名 |
| email | VARCHAR(100) | 邮箱 |
| password_hash | VARCHAR(255) | 密码哈希 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 4. 安全措施

- JWT 认证
- 密码加密 (bcrypt)
- SQL 注入防护
- XSS 防护
"""
    
    async def _handle_api_development(self, request: Request):
        """处理 API 开发请求"""
        pass
    
    async def _handle_bug_fix(self, request: Request):
        """处理 Bug 修复"""
        pass
    
    async def _handle_performance_optimization(self, request: Request):
        """处理性能优化请求"""
        pass
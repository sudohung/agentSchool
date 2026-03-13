"""前端开发 Agent."""

from __future__ import annotations

import time
from typing import List, Any
from agent.base import Agent
from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)


class FrontendDeveloperAgent(Agent):
    """
    前端开发 Agent
    
    职责：
    - 实现 UI 界面
    - 开发前端组件
    - 对接后端 API
    - 前端性能优化
    - 响应式设计实现
    - 前端测试
    
    产出：
    - frontend/UI_Components.md
    - frontend/Component_Docs.md
    - code/frontend/
    """
    
    def __init__(self, session=None, client=None):
        """初始化前端开发 Agent."""
        super().__init__(
            role="Frontend Developer",
            expertise=[
                "HTML/CSS/JavaScript",
                "React/Vue/Angular",
                "TypeScript",
                "前端构建工具",
                "响应式设计",
                "前端性能优化",
                "状态管理",
            ],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """
        R - 阅读文档
        
        阅读内容：
        - PRD 文档 (了解功能需求)
        - 架构设计文档 (了解技术约束)
        - UI/UX 设计稿 (了解界面要求)
        - API 文档 (了解接口定义)
        
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
            
            api_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.API_DOC,
                limit=10,
            )
            documents.extend(api_docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """
        A - 响应诉求
        
        处理诉求：
        - API 对接请求 (from Backend Developer)
        - UI 实现请求 (from Product Manager)
        - 前端 Bug 修复请求 (from QA Engineer)
        
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
                    await self._handle_api_request(request)
                elif "UI" in request.subject:
                    await self._handle_ui_request(request)
                elif "Bug" in request.subject or "修复" in request.subject:
                    await self._handle_bug_fix(request)
                
                processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """
        L - 发挥专业能力
        
        执行前端开发工作：
        1. 分析 UI/UX 设计要求
        2. 选择合适的组件库和框架
        3. 设计组件结构
        4. 实现响应式布局
        5. 处理前端状态管理
        6. 对接后端 API
        7. 优化前端性能
        
        Returns:
            工作结果
        """
        result = await self.send_message("""
        作为前端开发工程师，请根据以下需求实现前端功能：
        
        1. 分析 UI/UX 设计要求
           - 页面布局
           - 交互流程
           - 视觉风格
        
        2. 选择技术方案
           - 组件库选择
           - 状态管理方案
           - 路由方案
        
        3. 设计组件结构
           - 页面组件
           - 公共组件
           - 工具函数
        
        4. 实现核心功能
           - 关键代码实现
           - API 对接代码
           - 状态管理代码
        
        5. 性能优化
           - 代码分割
           - 懒加载
           - 缓存策略
        
        请输出：
        - 组件结构设计
        - 关键代码实现
        - API 对接方案
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
        content = self._format_component_doc(work_result)
        
        return Document(
            id=self._generate_id("fe"),
            path="frontend/UI_Components.md",
            metadata=DocumentMetadata(
                title="前端组件文档",
                doc_type=DocumentType.CODE,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["前端", "组件", "UI"],
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
            type=RequestType.COLLABORATION,
            priority=RequestPriority.HIGH,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Backend Developer",
            subject="请求 API 接口定义",
            content="请提供 API 接口定义文档，包括接口路径、请求参数、响应格式",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.REVIEW,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Product Manager",
            subject="UI 设计确认",
            content="请确认前端组件设计是否符合需求",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_component_doc(self, work_result: Any) -> str:
        """格式化组件文档"""
        return f"""# 前端组件文档

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 组件结构

```
src/
├── components/       # 公共组件
│   ├── Button/
│   ├── Input/
│   └── Modal/
├── pages/           # 页面组件
│   ├── Home/
│   └── Dashboard/
├── hooks/           # 自定义 Hooks
├── services/        # API 服务
└── utils/           # 工具函数
```

## 3. 核心组件

### 3.1 Button 组件
- **描述**: 通用按钮组件
- **Props**:
  - type: 'primary' | 'secondary' | 'danger'
  - size: 'small' | 'medium' | 'large'
  - disabled: boolean

### 3.2 Input 组件
- **描述**: 输入框组件
- **Props**:
  - placeholder: string
  - maxLength: number
  - onChange: function

## 4. API 对接

### 4.1 API 服务配置
```typescript
const apiClient = axios.create({{
  baseURL: '/api/v1',
  timeout: 10000,
}});
```

### 4.2 接口封装
```typescript
export const userApi = {{
  login: (data) => apiClient.post('/auth/login', data),
  logout: () => apiClient.post('/auth/logout'),
}};
```

## 5. 性能优化

### 5.1 代码分割
- 路由级懒加载
- 组件级懒加载

### 5.2 状态管理
- Redux / Zustand
- React Query (服务端状态)

### 5.3 缓存策略
- 浏览器缓存
- 本地存储
"""
    
    async def _handle_api_request(self, request: Request):
        """处理 API 对接请求"""
        pass
    
    async def _handle_ui_request(self, request: Request):
        """处理 UI 实现请求"""
        pass
    
    async def _handle_bug_fix(self, request: Request):
        """处理 Bug 修复"""
        pass
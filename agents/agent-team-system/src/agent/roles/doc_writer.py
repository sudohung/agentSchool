"""文档工程师 Agent."""

from __future__ import annotations

import time
from typing import List, Any
from agent.base import Agent
from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)


class DocWriterAgent(Agent):
    """
    文档工程师 Agent
    
    职责：
    - 编写用户手册
    - 编写 API 文档
    - 维护文档
    - 文档审查
    
    产出：
    - docs/User_Manual.md
    - docs/API_Docs.md
    - docs/README.md
    """
    
    def __init__(self, session=None, client=None):
        """初始化文档工程师 Agent."""
        super().__init__(
            role="Doc Writer",
            expertise=[
                "技术写作",
                "文档组织",
                "Markdown",
                "API 文档",
                "用户手册",
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
        - API 文档
        - 代码文档
        
        Returns:
            阅读到的文档列表
        """
        documents = []
        
        if self.document_hub:
            all_docs = await self.document_hub.list_documents(limit=50)
            documents.extend(all_docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """
        A - 响应诉求
        
        处理诉求：
        - 文档编写请求 (from Product Manager)
        - 文档更新请求 (from Developer)
        
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
                if "文档" in request.subject:
                    await self._handle_documentation(request)
                
                processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """
        L - 发挥专业能力
        
        执行文档编写工作：
        1. 整理需求信息
        2. 编写用户手册
        3. 编写 API 文档
        4. 编写 README
        
        Returns:
            工作结果
        """
        result = await self.send_message("""
        作为文档工程师，请编写项目文档：
        
        1. 用户手册
           - 快速开始
           - 功能说明
           - 常见问题
        
        2. API 文档
           - 接口说明
           - 参数说明
           - 示例代码
        
        3. README
           - 项目介绍
           - 安装说明
           - 使用说明
        
        请输出结构化的文档内容。
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
        content = self._format_user_manual(work_result)
        
        return Document(
            id=self._generate_id("doc"),
            path="docs/User_Manual.md",
            metadata=DocumentMetadata(
                title="用户手册",
                doc_type=DocumentType.USER_MANUAL,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["文档", "用户手册", "说明"],
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
            type=RequestType.INFORMATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Product Manager",
            subject="请求功能说明",
            content="请提供功能详细说明，以便编写用户手册",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_user_manual(self, work_result: Any) -> str:
        """格式化用户手册"""
        return f"""# 用户手册

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 快速开始

### 2.1 环境要求
- Python 3.8+
- Node.js 16+
- Docker (可选)

### 2.2 安装步骤

```bash
# 克隆项目
git clone <repository-url>

# 安装依赖
pip install -r requirements.txt
npm install

# 启动服务
python app.py
```

## 3. 功能说明

### 3.1 用户管理
- 用户注册
- 用户登录
- 密码重置

### 3.2 数据管理
- 数据查询
- 数据导入
- 数据导出

### 3.3 系统设置
- 个人设置
- 系统配置

## 4. 常见问题

### Q1: 如何重置密码？
A: 点击登录页面的"忘记密码"链接，按照提示操作。

### Q2: 如何导出数据？
A: 进入数据管理页面，选择要导出的数据，点击"导出"按钮。

## 5. 联系我们

- 技术支持: support@example.com
- 问题反馈: https://github.com/xxx/issues
"""
    
    async def _handle_documentation(self, request: Request):
        """处理文档请求"""
        pass
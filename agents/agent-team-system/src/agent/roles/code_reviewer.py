"""代码审查员 Agent."""

from __future__ import annotations

import time
from typing import List, Any
from agent.base import Agent
from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)


class CodeReviewerAgent(Agent):
    """
    代码审查员 Agent
    
    职责：
    - 代码审查
    - 质量检查
    - 最佳实践推广
    - 代码规范执行
    
    产出：
    - review/Code_Review.md
    - review/Quality_Report.md
    """
    
    def __init__(self, session=None, client=None):
        """初始化代码审查员 Agent."""
        super().__init__(
            role="Code Reviewer",
            expertise=[
                "代码审查",
                "设计模式",
                "代码规范",
                "重构",
                "最佳实践",
                "性能优化",
            ],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """
        R - 阅读文档
        
        阅读内容：
        - 代码文档
        - 架构设计
        - 技术规范
        
        Returns:
            阅读到的文档列表
        """
        documents = []
        
        if self.document_hub:
            code_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.CODE,
                limit=20,
            )
            documents.extend(code_docs)
            
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
        - 代码审查请求 (from Developer)
        - 质量检查请求 (from Tech Lead)
        
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
                if "审查" in request.subject or "Review" in request.subject:
                    await self._handle_code_review(request)
                elif "质量" in request.subject:
                    await self._handle_quality_check(request)
                
                processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """
        L - 发挥专业能力
        
        执行代码审查工作：
        1. 检查代码质量
        2. 检查代码规范
        3. 检查安全问题
        4. 提出改进建议
        
        Returns:
            工作结果
        """
        result = await self.send_message("""
        作为代码审查员，请进行代码审查：
        
        1. 代码质量检查
           - 代码结构
           - 命名规范
           - 注释质量
        
        2. 设计模式检查
           - 是否合理使用设计模式
           - 是否存在反模式
        
        3. 性能问题检查
           - 算法复杂度
           - 资源使用
           - 潜在性能瓶颈
        
        4. 安全问题检查
           - SQL 注入风险
           - XSS 风险
           - 敏感数据处理
        
        5. 改进建议
           - 重构建议
           - 最佳实践建议
        
        请输出详细的审查报告。
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
        content = self._format_review_report(work_result)
        
        return Document(
            id=self._generate_id("cr"),
            path="review/Code_Review.md",
            metadata=DocumentMetadata(
                title="代码审查报告",
                doc_type=DocumentType.OTHER,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["审查", "代码", "质量"],
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
            type=RequestType.NOTIFICATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Tech Lead",
            subject="审查完成通知",
            content="代码审查已完成，请查看审查报告",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_review_report(self, work_result: Any) -> str:
        """格式化审查报告"""
        return f"""# 代码审查报告

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 代码质量评分

| 指标 | 评分 | 说明 |
|------|------|------|
| 代码结构 | 8/10 | 结构清晰，模块划分合理 |
| 命名规范 | 9/10 | 命名规范，语义明确 |
| 注释质量 | 7/10 | 部分代码缺少注释 |
| 测试覆盖 | 8/10 | 测试覆盖率较高 |

## 3. 问题列表

### 3.1 严重问题
- 无

### 3.2 一般问题
1. [文件名:行号] 问题描述
2. [文件名:行号] 问题描述

### 3.3 建议改进
1. 建议使用更高效的数据结构
2. 建议添加异常处理

## 4. 最佳实践建议

### 4.1 设计模式
- 建议使用工厂模式优化对象创建
- 建议使用策略模式处理不同业务逻辑

### 4.2 性能优化
- 建议使用缓存减少数据库查询
- 建议使用异步处理提高响应速度

## 5. 总结

整体代码质量良好，建议修复上述问题后合并。
"""
    
    async def _handle_code_review(self, request: Request):
        """处理代码审查"""
        pass
    
    async def _handle_quality_check(self, request: Request):
        """处理质量检查"""
        pass
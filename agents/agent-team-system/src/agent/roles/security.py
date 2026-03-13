"""安全工程师 Agent."""

from __future__ import annotations

import time
from typing import List, Any
from agent.base import Agent
from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)


class SecurityAgent(Agent):
    """
    安全工程师 Agent
    
    职责：
    - 安全审计
    - 漏洞扫描
    - 安全加固
    - 安全培训
    
    产出：
    - security/Security_Report.md
    - security/Security_Guide.md
    """
    
    def __init__(self, session=None, client=None):
        """初始化安全工程师 Agent."""
        super().__init__(
            role="Security Engineer",
            expertise=[
                "安全审计",
                "渗透测试",
                "安全编码",
                "合规",
                "漏洞分析",
            ],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """
        R - 阅读文档
        
        阅读内容：
        - 架构设计
        - 代码文档
        - 安全配置
        
        Returns:
            阅读到的文档列表
        """
        documents = []
        
        if self.document_hub:
            arch_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.ARCHITECTURE,
                limit=5,
            )
            documents.extend(arch_docs)
            
            code_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.CODE,
                limit=20,
            )
            documents.extend(code_docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """
        A - 响应诉求
        
        处理诉求：
        - 安全审计请求 (from Tech Lead)
        - 漏洞扫描请求
        
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
                if "安全" in request.subject:
                    await self._handle_security_audit(request)
                elif "漏洞" in request.subject:
                    await self._handle_vulnerability_scan(request)
                
                processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """
        L - 发挥专业能力
        
        执行安全工作：
        1. 安全审计
        2. 漏洞扫描
        3. 安全加固
        4. 编写安全指南
        
        Returns:
            工作结果
        """
        result = await self.send_message("""
        作为安全工程师，请进行安全审计：
        
        1. 代码安全审计
           - SQL 注入风险
           - XSS 风险
           - CSRF 风险
           - 敏感数据泄露
        
        2. 架构安全审计
           - 认证授权机制
           - 数据加密
           - 网络安全
        
        3. 配置安全审计
           - 服务器配置
           - 数据库配置
           - 密钥管理
        
        4. 安全加固建议
           - 代码修复建议
           - 配置优化建议
           - 架构改进建议
        
        请输出详细的安全报告。
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
        content = self._format_security_report(work_result)
        
        return Document(
            id=self._generate_id("sec"),
            path="security/Security_Report.md",
            metadata=DocumentMetadata(
                title="安全审计报告",
                doc_type=DocumentType.OTHER,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["安全", "审计", "漏洞"],
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
            priority=RequestPriority.CRITICAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Tech Lead",
            subject="安全漏洞通知",
            content="发现安全漏洞，请及时修复",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_security_report(self, work_result: Any) -> str:
        """格式化安全报告"""
        return f"""# 安全审计报告

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 漏洞统计

| 严重程度 | 数量 | 状态 |
|----------|------|------|
| 严重 | 0 | - |
| 高危 | 2 | 待修复 |
| 中危 | 5 | 待修复 |
| 低危 | 10 | 待修复 |

## 3. 漏洞详情

### 3.1 高危漏洞

#### VH-001: SQL 注入风险
- **位置**: api/user.py:45
- **描述**: 用户输入未经过滤直接拼接到 SQL 语句
- **影响**: 可能导致数据库泄露
- **修复建议**: 使用参数化查询

#### VH-002: XSS 风险
- **位置**: frontend/component.js:120
- **描述**: 用户输入直接渲染到页面
- **影响**: 可能导致 XSS 攻击
- **修复建议**: 对用户输入进行 HTML 编码

### 3.2 中危漏洞

1. 敏感信息明文传输
2. 缺少 CSRF Token
3. 密码复杂度要求不足
4. 会话超时时间过长
5. 错误信息泄露敏感数据

## 4. 安全加固建议

### 4.1 代码层面
- 所有用户输入必须验证和过滤
- 使用参数化查询防止 SQL 注入
- 对输出进行 HTML 编码防止 XSS

### 4.2 配置层面
- 启用 HTTPS
- 配置安全响应头
- 设置合理的会话超时时间

### 4.3 架构层面
- 实施最小权限原则
- 添加 Web 应用防火墙
- 部署入侵检测系统

## 5. 修复优先级

1. **立即修复**: 高危漏洞 (VH-001, VH-002)
2. **一周内修复**: 中危漏洞
3. **一个月内修复**: 低危漏洞
"""
    
    async def _handle_security_audit(self, request: Request):
        """处理安全审计"""
        pass
    
    async def _handle_vulnerability_scan(self, request: Request):
        """处理漏洞扫描"""
        pass
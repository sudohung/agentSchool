"""测试工程师 Agent."""

from __future__ import annotations

import time
from typing import List, Any
from agent.base import Agent
from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)


class QAAgent(Agent):
    """
    测试工程师 Agent
    
    职责：
    - 制定测试计划
    - 编写测试用例
    - 执行测试
    - 报告 Bug
    - 回归测试
    - 自动化测试
    
    产出：
    - test/Test_Plan.md
    - test/Test_Cases.md
    - test/Test_Report.md
    - test/Bug_Report.md
    """
    
    def __init__(self, session=None, client=None):
        """初始化测试工程师 Agent."""
        super().__init__(
            role="QA Engineer",
            expertise=[
                "测试设计",
                "自动化测试",
                "性能测试",
                "安全测试",
                "Bug 跟踪",
                "测试工具",
            ],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """
        R - 阅读文档
        
        阅读内容：
        - PRD 文档 (了解功能需求)
        - API 文档 (了解接口定义)
        - 代码文档 (了解实现细节)
        - 之前的测试报告
        
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
            
            api_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.API_DOC,
                limit=10,
            )
            documents.extend(api_docs)
            
            test_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.TEST_CASE,
                limit=10,
            )
            documents.extend(test_docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """
        A - 响应诉求
        
        处理诉求：
        - 测试请求 (from Product Manager)
        - Bug 验证请求 (from Developer)
        - 回归测试请求 (from Tech Lead)
        
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
                if "测试" in request.subject:
                    await self._handle_test_request(request)
                elif "Bug" in request.subject and "验证" in request.subject:
                    await self._handle_bug_verification(request)
                elif "回归" in request.subject:
                    await self._handle_regression_test(request)
                
                processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """
        L - 发挥专业能力
        
        执行测试工作：
        1. 分析需求和功能
        2. 设计测试用例
        3. 识别测试风险
        4. 制定测试策略
        5. 规划测试资源
        
        Returns:
            工作结果
        """
        result = await self.send_message("""
        作为测试工程师，请设计测试方案：
        
        1. 测试范围分析
           - 功能测试范围
           - 性能测试范围
           - 安全测试范围
        
        2. 测试用例设计
           - 正常流程用例
           - 异常流程用例
           - 边界值用例
        
        3. 测试策略
           - 手动测试
           - 自动化测试
           - 性能测试
        
        4. 风险识别
           - 技术风险
           - 业务风险
           - 时间风险
        
        请输出：
        - 测试计划
        - 测试用例列表
        - 验收标准
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
        content = self._format_test_cases(work_result)
        
        return Document(
            id=self._generate_id("qa"),
            path="test/Test_Cases.md",
            metadata=DocumentMetadata(
                title="测试用例文档",
                doc_type=DocumentType.TEST_CASE,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["测试", "用例", "QA"],
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
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Product Manager",
            subject="确认验收标准",
            content="请确认功能验收标准",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.COLLABORATION,
            priority=RequestPriority.HIGH,
            status=RequestStatus.PENDING,
            from_agent=self.role,
            to_agent="Backend Developer",
            subject="Bug 修复请求",
            content="发现以下 Bug 需要修复",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_test_cases(self, work_result: Any) -> str:
        """格式化测试用例文档"""
        return f"""# 测试用例文档

## 1. 测试计划

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 测试用例

### TC001 - 用户登录
**前置条件**: 用户已注册
**测试步骤**:
1. 打开登录页面
2. 输入用户名
3. 输入密码
4. 点击登录按钮
**预期结果**: 登录成功，跳转到首页

### TC002 - 用户注册
**前置条件**: 无
**测试步骤**:
1. 打开注册页面
2. 输入用户名
3. 输入邮箱
4. 输入密码
5. 确认密码
6. 点击注册按钮
**预期结果**: 注册成功，发送验证邮件

### TC003 - 数据查询
**前置条件**: 用户已登录
**测试步骤**:
1. 打开数据页面
2. 输入查询条件
3. 点击查询按钮
**预期结果**: 显示查询结果列表

## 3. 边界值测试

### BV001 - 用户名长度测试
- 最小长度: 3 字符
- 最大长度: 50 字符
- 边界值: 2, 3, 50, 51 字符

### BV002 - 密码长度测试
- 最小长度: 8 字符
- 最大长度: 100 字符
- 边界值: 7, 8, 100, 101 字符

## 4. 异常流程测试

### EX001 - 登录失败
**测试步骤**: 输入错误的用户名或密码
**预期结果**: 显示错误提示

### EX002 - 网络异常
**测试步骤**: 断开网络连接
**预期结果**: 显示网络错误提示

## 5. 验收标准

| 功能 | 通过条件 |
|------|----------|
| 用户登录 | 正确凭据可登录 |
| 用户注册 | 信息完整可注册 |
| 数据查询 | 查询结果正确 |
"""
    
    async def _handle_test_request(self, request: Request):
        """处理测试请求"""
        pass
    
    async def _handle_bug_verification(self, request: Request):
        """处理 Bug 验证"""
        pass
    
    async def _handle_regression_test(self, request: Request):
        """处理回归测试"""
        pass
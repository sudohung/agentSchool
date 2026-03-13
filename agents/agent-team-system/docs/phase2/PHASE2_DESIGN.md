# Phase 2: Agent 角色库完善设计文档

> Agent Team System - Phase 2 详细设计
>
> 版本：0.2.0
> 创建日期：2026-03-13
> 最后更新：2026-03-13

---

## 1. 概述

### 1.1 当前状态分析

Phase 2 (Agent 角色库) 目前完成度约 **85%**，存在以下问题：

#### 已完成内容
- ✅ 12 个 Agent 角色全部定义
- ✅ 所有角色都有对应的 MD 定义文件
- ✅ Agent 加载器 (loader.py) 完整实现
- ✅ PM/Architect/TechLead/Coordinator Python 类完整实现

#### 存在的问题

| 问题 | 影响 | 严重程度 |
|------|------|----------|
| 角色实现方式不一致 | 维护困难，行为不可预测 | 高 |
| 动态加载角色功能不完整 | read_documents/act_on_requests 返回空 | 高 |
| 缺乏统一的实现规范 | 代码风格不一致 | 中 |
| 测试覆盖不足 | 质量难以保证 | 中 |

### 1.2 完善目标

**目标：将 Phase 2 完成度从 85% 提升至 100%**

```
Phase 2 完善路线图
├── 统一角色实现方式
│   ├── 所有角色使用 Python 类实现
│   └── 统一继承 Agent 基类
├── 完善角色功能
│   ├── 实现 read_documents() 方法
│   ├── 实现 act_on_requests() 方法
│   ├── 完善 leverage_expertise() 方法
│   └── 完善 produce_document() 方法
├── 统一代码规范
│   ├── 统一命名规范
│   ├── 统一文档格式
│   └── 统一测试覆盖
└── 验证和测试
    ├── 单元测试 100% 覆盖
    └── 集成测试验证
```

---

## 2. 角色实现规范

### 2.1 统一实现模板

所有角色必须遵循以下模板：

```python
"""角色名称 Agent."""

from __future__ import annotations

import time
from typing import List, Any, Dict, Optional
from agent.base import Agent
from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)


class RoleNameAgent(Agent):
    """
    角色名称 Agent
    
    职责：[职责描述]
    产出：[产出文档列表]
    
    Attributes:
        role: 角色名称
        expertise: 专业技能列表
    """
    
    def __init__(self, session=None, client=None):
        """初始化 Agent."""
        super().__init__(
            role="Role Name",
            expertise=["技能1", "技能2", "技能3"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """
        R - 阅读文档
        
        根据角色职责阅读相关文档：
        - [文档类型 1]
        - [文档类型 2]
        
        Returns:
            阅读到的文档列表
        """
        documents = []
        
        if self.document_hub:
            # 阅读特定类型的文档
            docs = await self.document_hub.list_documents(
                doc_type=DocumentType.XXX,
                limit=10,
            )
            documents.extend(docs)
        
        return documents
    
    async def act_on_requests(self) -> List[Request]:
        """
        A - 响应诉求
        
        处理分配给该角色的诉求：
        - [诉求类型 1]
        - [诉求类型 2]
        
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
                await self._handle_request(request)
                processed.append(request)
        
        return processed
    
    async def leverage_expertise(self) -> Any:
        """
        L - 发挥专业能力
        
        使用 AI 能力执行专业工作
        
        Returns:
            工作结果
        """
        result = await self.send_message("""
        作为 [角色名称]，请 [工作描述]：
        
        1. [步骤 1]
        2. [步骤 2]
        3. [步骤 3]
        
        输出结构化的结果。
        """)
        
        return result
    
    async def produce_document(self, work_result: Any) -> Document:
        """
        P - 产出文档
        
        根据工作结果产出文档
        
        Args:
            work_result: 工作结果
            
        Returns:
            产出的文档
        """
        content = self._format_document(work_result)
        
        return Document(
            id=self._generate_id("doc"),
            path="path/to/document.md",
            metadata=DocumentMetadata(
                title="文档标题",
                doc_type=DocumentType.XXX,
                author=self.role,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["标签1", "标签2"],
            ),
            content=DocumentContent(
                content=content,
                format="markdown",
            ),
        )
    
    async def help_requests(self) -> List[Request]:
        """
        H - 发布诉求
        
        向其他角色发布协作诉求
        
        Returns:
            发布的诉求列表
        """
        requests = []
        
        # 诉求 1
        requests.append(Request(
            id=self._generate_id("req"),
            type=RequestType.COLLABORATION,
            priority=RequestPriority.HIGH,
            from_agent=self.role,
            to_agent="Other Role",
            subject="诉求主题",
            content="诉求内容",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        ))
        
        return requests
    
    def _format_document(self, work_result: Any) -> str:
        """格式化文档内容."""
        return f"""# 文档标题

## 1. 概述

{work_result if isinstance(work_result, str) else str(work_result)}

## 2. 详细内容

[详细内容]
"""
    
    async def _handle_request(self, request: Request):
        """处理单个诉求."""
        # 根据诉求类型分发处理
        pass
```

### 2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase + Agent | `FrontendDeveloperAgent` |
| 文件名 | snake_case.py | `frontend_developer.py` |
| MD 文件 | snake_case.md | `frontend_developer.md` |
| 方法名 | snake_case | `read_documents` |
| 私有方法 | _snake_case | `_handle_request` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES` |

### 2.3 文档字符串规范

所有公共方法必须有文档字符串，格式如下：

```python
async def read_documents(self) -> List[Document]:
    """
    R - 阅读文档
    
    根据角色职责阅读相关文档，支持：
    - 需求文档
    - 设计文档
    - 技术文档
    
    Returns:
        List[Document]: 阅读到的文档列表
        
    Raises:
        DocumentHubError: 文档中心访问失败
        
    Example:
        >>> agent = FrontendDeveloperAgent()
        >>> docs = await agent.read_documents()
        >>> print(len(docs))
        5
    """
```

---

## 3. 角色详细设计

### 3.1 Frontend Developer Agent

#### 3.1.1 职责定义

```python
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
```

#### 3.1.2 Read 实现

```python
async def read_documents(self) -> List[Document]:
    """
    R - 阅读文档
    
    阅读内容：
    - PRD 文档 (了解功能需求)
    - 架构设计文档 (了解技术约束)
    - UI/UX 设计稿 (了解界面要求)
    - API 文档 (了解接口定义)
    """
    documents = []
    
    if self.document_hub:
        # 阅读 PRD
        prd_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.PRD,
            limit=5,
        )
        documents.extend(prd_docs)
        
        # 阅读架构设计
        arch_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.ARCHITECTURE,
            limit=5,
        )
        documents.extend(arch_docs)
        
        # 阅读 API 文档
        api_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.API_DOC,
            limit=10,
        )
        documents.extend(api_docs)
    
    return documents
```

#### 3.1.3 Act 实现

```python
async def act_on_requests(self) -> List[Request]:
    """
    A - 响应诉求
    
    处理诉求：
    - API 对接请求 (from Backend Developer)
    - UI 实现请求 (from Product Manager)
    - 前端 Bug 修复请求 (from QA Engineer)
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

async def _handle_api_request(self, request: Request):
    """处理 API 对接请求"""
    # 解析 API 定义
    # 实现前端 API 调用
    # 更新状态
    pass

async def _handle_ui_request(self, request: Request):
    """处理 UI 实现请求"""
    # 分析 UI 需求
    # 设计组件结构
    # 实现组件代码
    pass

async def _handle_bug_fix(self, request: Request):
    """处理 Bug 修复"""
    # 分析 Bug 描述
    # 定位问题代码
    # 修复并验证
    pass
```

#### 3.1.4 Leverage 实现

```python
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
```

#### 3.1.5 Produce 实现

```python
async def produce_document(self, work_result: Any) -> Document:
    """P - 产出文档"""
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
```

#### 3.1.6 Help 实现

```python
async def help_requests(self) -> List[Request]:
    """H - 发布诉求"""
    requests = []
    
    # 请求 API 接口定义
    requests.append(Request(
        id=self._generate_id("req"),
        type=RequestType.COLLABORATION,
        priority=RequestPriority.HIGH,
        from_agent=self.role,
        to_agent="Backend Developer",
        subject="请求 API 接口定义",
        content="请提供 API 接口定义文档，包括接口路径、请求参数、响应格式",
        created_at=int(time.time()),
        updated_at=int(time.time()),
    ))
    
    # 请求 UI 设计确认
    requests.append(Request(
        id=self._generate_id("req"),
        type=RequestType.REVIEW,
        priority=RequestPriority.NORMAL,
        from_agent=self.role,
        to_agent="Product Manager",
        subject="UI 设计确认",
        content="请确认前端组件设计是否符合需求",
        created_at=int(time.time()),
        updated_at=int(time.time()),
    ))
    
    return requests
```

---

### 3.2 Backend Developer Agent

#### 3.2.1 职责定义

```python
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
```

#### 3.2.2 Read 实现

```python
async def read_documents(self) -> List[Document]:
    """
    R - 阅读文档
    
    阅读内容：
    - PRD 文档 (了解业务需求)
    - 架构设计文档 (了解系统架构)
    - 数据库设计文档 (了解数据模型)
    - API 设计文档 (了解接口规范)
    """
    documents = []
    
    if self.document_hub:
        # 阅读 PRD
        prd_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.PRD,
            limit=5,
        )
        documents.extend(prd_docs)
        
        # 阅读架构设计
        arch_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.ARCHITECTURE,
            limit=5,
        )
        documents.extend(arch_docs)
        
        # 阅读技术设计
        tech_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.TECH_DESIGN,
            limit=5,
        )
        documents.extend(tech_docs)
    
    return documents
```

#### 3.2.3 Act 实现

```python
async def act_on_requests(self) -> List[Request]:
    """
    A - 响应诉求
    
    处理诉求：
    - API 开发请求 (from Frontend Developer)
    - 业务逻辑实现请求 (from Product Manager)
    - 后端 Bug 修复请求 (from QA Engineer)
    - 性能优化请求 (from Tech Lead)
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

async def _handle_api_development(self, request: Request):
    """处理 API 开发请求"""
    # 分析 API 需求
    # 设计 API 接口
    # 实现业务逻辑
    # 编写单元测试
    pass

async def _handle_performance_optimization(self, request: Request):
    """处理性能优化请求"""
    # 分析性能瓶颈
    # 优化查询语句
    # 添加缓存
    # 优化代码
    pass
```

#### 3.2.4 Leverage 实现

```python
async def leverage_expertise(self) -> Any:
    """
    L - 发挥专业能力
    
    执行后端开发工作：
    1. 设计 API 接口
    2. 实现业务逻辑
    3. 设计数据库模型
    4. 优化性能
    5. 编写测试
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
```

#### 3.2.5 Produce 实现

```python
async def produce_document(self, work_result: Any) -> Document:
    """P - 产出文档"""
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
```

---

### 3.3 QA Engineer Agent

#### 3.3.1 职责定义

```python
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
```

#### 3.3.2 Read 实现

```python
async def read_documents(self) -> List[Document]:
    """
    R - 阅读文档
    
    阅读内容：
    - PRD 文档 (了解功能需求)
    - API 文档 (了解接口定义)
    - 代码文档 (了解实现细节)
    - 之前的测试报告
    """
    documents = []
    
    if self.document_hub:
        # 阅读 PRD
        prd_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.PRD,
            limit=5,
        )
        documents.extend(prd_docs)
        
        # 阅读 API 文档
        api_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.API_DOC,
            limit=10,
        )
        documents.extend(api_docs)
        
        # 阅读测试用例
        test_docs = await self.document_hub.list_documents(
            doc_type=DocumentType.TEST_CASE,
            limit=10,
        )
        documents.extend(test_docs)
    
    return documents
```

#### 3.3.3 Act 实现

```python
async def act_on_requests(self) -> List[Request]:
    """
    A - 响应诉求
    
    处理诉求：
    - 测试请求 (from Product Manager)
    - Bug 验证请求 (from Developer)
    - 回归测试请求 (from Tech Lead)
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

async def _handle_test_request(self, request: Request):
    """处理测试请求"""
    # 分析测试范围
    # 设计测试用例
    # 执行测试
    # 生成测试报告
    pass

async def _handle_bug_verification(self, request: Request):
    """处理 Bug 验证"""
    # 重现 Bug
    # 验证修复
    # 更新 Bug 状态
    pass

async def _handle_regression_test(self, request: Request):
    """处理回归测试"""
    # 选择回归测试用例
    # 执行回归测试
    # 生成回归测试报告
    pass
```

#### 3.3.4 Leverage 实现

```python
async def leverage_expertise(self) -> Any:
    """
    L - 发挥专业能力
    
    执行测试工作：
    1. 分析需求和功能
    2. 设计测试用例
    3. 识别测试风险
    4. 制定测试策略
    5. 规划测试资源
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
```

---

### 3.4 Code Reviewer Agent

```python
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
        super().__init__(
            role="Code Reviewer",
            expertise=["代码审查", "设计模式", "代码规范", "重构", "最佳实践"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            # 阅读代码文档
            code_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.CODE,
                limit=20,
            )
            documents.extend(code_docs)
        
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
                if "审查" in request.subject or "Review" in request.subject:
                    await self._handle_code_review(request)
                processed.append(request)
        
        return processed
    
    async def _handle_code_review(self, request: Request):
        """处理代码审查"""
        # 检查代码质量
        # 检查代码规范
        # 检查安全问题
        # 提出改进建议
        pass
```

---

### 3.5 Doc Writer Agent

```python
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
        super().__init__(
            role="Doc Writer",
            expertise=["技术写作", "文档组织", "Markdown", "API 文档"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            # 阅读所有文档类型
            all_docs = await self.document_hub.list_documents(limit=50)
            documents.extend(all_docs)
        
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
                if "文档" in request.subject:
                    await self._handle_documentation(request)
                processed.append(request)
        
        return processed
```

---

### 3.6 DevOps Agent

```python
class DevOpsAgent(Agent):
    """
    运维工程师 Agent
    
    职责：
    - 部署应用
    - 配置 CI/CD
    - 监控系统
    - 日志管理
    - 故障处理
    
    产出：
    - deploy/Deploy.md
    - deploy/CI_CD_Config.md
    - deploy/Monitoring.md
    """
    
    def __init__(self, session=None, client=None):
        super().__init__(
            role="DevOps Engineer",
            expertise=["Docker", "Kubernetes", "CI/CD", "监控", "日志"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            # 阅读架构设计
            arch_docs = await self.document_hub.list_documents(
                doc_type=DocumentType.ARCHITECTURE,
                limit=5,
            )
            documents.extend(arch_docs)
        
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
                if "部署" in request.subject:
                    await self._handle_deployment(request)
                elif "监控" in request.subject:
                    await self._handle_monitoring(request)
                processed.append(request)
        
        return processed
```

---

### 3.7 Security Agent

```python
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
        super().__init__(
            role="Security Engineer",
            expertise=["安全审计", "渗透测试", "安全编码", "合规"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            # 阅读架构和代码
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
        """A - 响应诉求"""
        processed = []
        
        if self.request_board:
            pending = await self.request_board.get_requests_for_agent(
                agent_role=self.role,
                status=RequestStatus.PENDING,
            )
            
            for request in pending:
                if "安全" in request.subject:
                    await self._handle_security_audit(request)
                processed.append(request)
        
        return processed
```

---

### 3.8 Full Stack Developer Agent

```python
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
        super().__init__(
            role="Full Stack Developer",
            expertise=["前端", "后端", "数据库", "部署", "DevOps"],
            session=session,
            client=client,
        )
    
    async def read_documents(self) -> List[Document]:
        """R - 阅读文档"""
        documents = []
        
        if self.document_hub:
            # 阅读 PRD 和设计文档
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
        """A - 响应诉求"""
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
```

---

## 4. 实现计划

### 4.1 任务分解

| 优先级 | 任务 | 文件 | 预计时间 | 状态 |
|--------|------|------|----------|------|
| P0 | 创建实现规范文档 | `PHASE2_DESIGN.md` | 1h | ✅ |
| P0 | Frontend Developer Agent | `frontend_developer.py` | 2h | 待开始 |
| P0 | Backend Developer Agent | `backend_developer.py` | 2h | 待开始 |
| P0 | QA Engineer Agent | `qa_engineer.py` | 2h | 待开始 |
| P1 | Code Reviewer Agent | `code_reviewer.py` | 1.5h | 待开始 |
| P1 | Doc Writer Agent | `doc_writer.py` | 1.5h | 待开始 |
| P1 | DevOps Agent | `devops.py` | 1.5h | 待开始 |
| P1 | Security Agent | `security.py` | 1.5h | 待开始 |
| P1 | Full Stack Developer Agent | `fullstack_developer.py` | 1.5h | 待开始 |
| P2 | 更新 others.py | `others.py` | 0.5h | 待开始 |
| P2 | 更新 __init__.py | `__init__.py` | 0.5h | 待开始 |
| P2 | 单元测试 | `tests/test_roles.py` | 3h | 待开始 |
| P2 | 集成测试 | `tests/test_integration.py` | 2h | 待开始 |
| **总计** | | | **20h** | |

### 4.2 实施顺序

```
第 1 天 (8h)
├── 创建设计文档 ✅
├── Frontend Developer Agent (2h)
├── Backend Developer Agent (2h)
└── QA Engineer Agent (2h)

第 2 天 (8h)
├── Code Reviewer Agent (1.5h)
├── Doc Writer Agent (1.5h)
├── DevOps Agent (1.5h)
├── Security Agent (1.5h)
└── Full Stack Developer Agent (1.5h)

第 3 天 (4h)
├── 更新 others.py (0.5h)
├── 更新 __init__.py (0.5h)
├── 单元测试 (2h)
└── 集成测试 (1h)
```

---

## 5. 测试计划

### 5.1 单元测试

每个角色需要测试：

```python
# tests/test_roles.py

@pytest.mark.asyncio
async def test_frontend_developer_agent():
    """测试前端开发 Agent"""
    agent = FrontendDeveloperAgent()
    
    # 测试属性
    assert agent.role == "Frontend Developer"
    assert "HTML/CSS/JavaScript" in agent.expertise
    
    # 测试方法
    docs = await agent.read_documents()
    assert isinstance(docs, list)
    
    result = await agent.leverage_expertise()
    assert result is not None
    
    doc = await agent.produce_document(result)
    assert doc.metadata.doc_type == DocumentType.CODE
```

### 5.2 集成测试

```python
# tests/test_integration.py

@pytest.mark.asyncio
async def test_all_agents_can_be_created():
    """测试所有 Agent 都可以创建"""
    from agent.roles import (
        ProductManagerAgent,
        SystemArchitectAgent,
        TechLeadAgent,
        FrontendDeveloperAgent,
        BackendDeveloperAgent,
        FullStackDeveloperAgent,
        QAAgent,
        CodeReviewerAgent,
        DocWriterAgent,
        DevOpsAgent,
        SecurityAgent,
        CoordinatorAgent,
    )
    
    agents = [
        ProductManagerAgent(),
        SystemArchitectAgent(),
        TechLeadAgent(),
        FrontendDeveloperAgent(),
        BackendDeveloperAgent(),
        FullStackDeveloperAgent(),
        QAAgent(),
        CodeReviewerAgent(),
        DocWriterAgent(),
        DevOpsAgent(),
        SecurityAgent(),
        CoordinatorAgent(),
    ]
    
    assert len(agents) == 12
    for agent in agents:
        assert agent is not None
        assert agent.role is not None
        assert len(agent.expertise) > 0
```

### 5.3 测试覆盖率目标

- 代码覆盖率：>= 80%
- 功能覆盖率：100%
- 所有公共方法：100%

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 所有 12 个角色使用 Python 类实现
- [ ] 每个角色实现完整的 Ralph Loop 方法
- [ ] 所有角色都有对应的 MD 定义文件
- [ ] 角色间协作关系清晰

### 6.2 代码质量

- [ ] 代码符合 PEP 8 规范
- [ ] 所有公共方法有文档字符串
- [ ] 类型注解完整
- [ ] 无 lint 错误

### 6.3 测试验收

- [ ] 单元测试覆盖率 >= 80%
- [ ] 所有测试通过
- [ ] 集成测试通过

### 6.4 文档验收

- [ ] 设计文档完整
- [ ] API 文档更新
- [ ] README 更新

---

## 7. 风险和缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 实现工作量超出预期 | 高 | 中 | 优先完成核心角色，其他角色简化实现 |
| 测试用例设计困难 | 中 | 低 | 参考 Phase 1 测试用例 |
| 角色间协作逻辑复杂 | 高 | 中 | 简化协作流程，逐步完善 |

---

> 最后更新：2026-03-13
> 状态：待实施
> 负责人：待分配
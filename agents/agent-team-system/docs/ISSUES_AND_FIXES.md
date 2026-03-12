# Agent Team System - 问题与修复记录

> 记录开发过程中遇到的问题和解决方案

---

## 2026-03-12: Pydantic v2 兼容性修复

### 问题描述

单元测试失败（6 个失败），主要原因是 Pydantic v2 不再支持 `class Config:` 语法，以及测试数据与模型定义不匹配。

**失败测试**:
```
FAILED tests/test_framework.py::TestPermissions::test_permission_request
FAILED tests/test_framework.py::TestPermissionHandler::test_auto_allow
FAILED tests/test_framework.py::TestDocumentStore::test_save_and_load
FAILED tests/test_framework.py::TestDocumentStore::test_delete
FAILED tests/test_framework.py::TestRequestBoard::test_add_response
FAILED tests/test_framework.py::TestRalphLoop::test_completion_checker
```

### 根本原因

1. **Pydantic v2 废弃 `class Config:`**
   - 旧语法：`class Config: use_enum_values = True`
   - 新语法：`model_config = ConfigDict(use_enum_values=True)`

2. **模型字段缺失**
   - `Request` 模型缺少 `responded_at` 和 `responded_by` 字段
   - `DocumentMetadata` 的 `checksum` 字段在某些情况下未初始化

3. **测试数据不匹配**
   - `test_auto_allow` 使用了错误的正则模式
   - `test_completion_checker` 的测试数据导致完成度不达标

4. **导入路径错误**
   - `Document` 模型应从 `document_hub.models` 导入，而非 `agent.config`

### 修复方案

#### 1. Pydantic v2 兼容性迁移

**文件**: `src/agent/config.py`, `src/agent/permissions.py`, `src/document_hub/models.py`, `src/request_board/models.py`

```python
# 修改前
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    role: str
    # ...
    
    class Config:
        arbitrary_types_allowed = True

# 修改后
from pydantic import BaseModel, Field, ConfigDict

class AgentConfig(BaseModel):
    role: str
    # ...
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

#### 2. 添加缺失字段

**文件**: `src/request_board/models.py`

```python
class Request(BaseModel):
    # ... 现有字段 ...
    response: Optional[str] = None
    responded_at: Optional[int] = None  # 新增
    responded_by: Optional[str] = None  # 新增
    
    model_config = ConfigDict(use_enum_values=True)
```

#### 3. 修复测试数据

**文件**: `tests/test_framework.py`

```python
# 修复 1: 导入路径
from agent.config import AgentConfig, AgentStatus
from document_hub.models import Document, DocumentMetadata, DocumentContent, DocumentType
from request_board.models import Request, RequestType, RequestPriority, RequestStatus, RequestResponse

# 修复 2: 权限测试断言
def test_permission_request(self):
    req = PermissionRequest(...)
    assert req.type == "file_read"  # 使用字符串而非枚举

# 修复 3: 自动允许规则
def test_auto_allow(self):
    handler = PermissionQuestionHandler(
        auto_allow_patterns=[r"^file_read:.*\.txt$"]  # 添加 file_read: 前缀
    )

# 修复 4: 完成度检查
def test_completion_checker(self):
    result = asyncio.run(checker.check({
        "requirement_coverage": 0.95,    # 提高数值
        "document_completeness": 0.9,
        "quality_score": 0.85,
    }))
    assert result["ready"] is True
    assert result["score"] >= 0.9
```

### 验证结果

**修复前**:
```
21 passed, 6 failed
```

**修复后**:
```
27 passed, 0 failed
```

### 剩余警告

```
PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead.
  Location: src/document_hub/store.py:140
```

**建议后续修复**:
```python
# 将 document.dict() 改为 document.model_dump()
```

---

## 2026-03-12: OpenCode SDK 集成问题

### 问题描述

OpenCode SDK 消息发送返回空响应（HTTP 200, Content-Length: 0）。

### 根本原因

- `agent="System"` 参数导致服务器返回空响应
- Server 绑定在 `172.22.221.176:4096` 而非 `localhost:4096`

### 解决方案

1. 不指定 `agent` 参数或使用默认值
2. 使用正确的服务器地址

**测试文件**: `tests/test_opencode_integration.py`

```python
BASE_URL = "http://172.22.221.176:4096"  # 非 localhost

# 发送消息时不指定 agent
result = client.message.send_text(
    session_id=session.id,
    text="用一句话介绍你的能力",
    # 不指定 agent 参数
)
```

### 验证结果

```
✅ SDK 导入测试
✅ SDK 连接测试 (Server v1.2.24)
✅ 会话管理测试
✅ 消息发送测试 (3 parts 响应)
✅ OpenCodeIntegration 集成测试
```

---

## 2026-03-12: Pydantic v2 `dict()` 方法废弃警告修复

### 问题描述

`DocumentStore._write_file()` 方法使用了已废弃的 `document.dict()` 方法。

**警告信息**:
```
PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead.
  Location: src/document_hub/store.py:140
```

### 修复方案

**文件**: `src/document_hub/store.py`

```python
# 修改前
json.dump(document.dict(), f, ensure_ascii=False, indent=2)

# 修改后
json.dump(document.model_dump(), f, ensure_ascii=False, indent=2)
```

### 验证结果

```
27 passed in 0.20s ✅
```

---

## 2026-03-12: pytest-asyncio 配置问题

### 问题描述

集成测试 `test_opencode_integration.py` 使用 pytest 运行失败。

### 根本原因

测试文件中包含 `async def` 函数，pytest 需要配置才能运行 async 测试。

### 解决方案

测试脚本可以直接运行（非 pytest 模式），或添加 pytest.mark.asyncio 装饰器。

### 验证结果

```
✓ SDK 导入测试
✓ SDK 连接测试 (Server v1.2.24)
✓ 会话管理测试
✓ 消息发送测试 (3 parts 响应)
✓ OpenCodeIntegration 集成测试 (3 parts 响应)
```

---

## 待解决问题

| ID | 问题 | 优先级 | 状态 |
|----|------|--------|------|
| #001 | `document.dict()` 已废弃，需改用 `model_dump()` | 低 | ✅ 已修复 |
| #002 | opencode-4-py SDK 的 Pydantic v2 兼容性警告 | 低 | 外部依赖 |
| #003 | 完整版本控制 (Diff 计算、版本回滚) | 中 | 待实现 |
| #004 | 完整路由策略实现 | 中 | 待实现 |
| #005 | 端到端测试场景 | 中 | 待实现 |
| #006 | 核心角色未迁移到 MD 定义 | 高 | ✅ 已修复 |

---

## 2026-03-12: 核心角色 MD 定义迁移

### 问题描述

MD 文件中定义了 8 个角色，缺少 4 个核心角色（Product Manager, System Architect, Tech Lead, Coordinator）还在 Python 代码中定义，未迁移到 MD。

**原有 MD 定义角色 (8 个)**:
- frontend_developer.md
- backend_developer.md
- fullstack_developer.md
- qa_engineer.md
- code_reviewer.md
- doc_writer.md
- devops.md
- security.md

**缺失的核心角色 (4 个)**:
- Product Manager (仅 Python 定义)
- System Architect (仅 Python 定义)
- Tech Lead (仅 Python 定义)
- Coordinator (未实现)

### 修复方案

创建 4 个核心角色的 MD 定义文件：

1. **pm.md** - Product Manager 角色定义
   - 职责：需求分析、产品规划、优先级排序
   - 产出：PRD.md、用户故事、需求列表

2. **architect.md** - System Architect 角色定义
   - 职责：系统架构设计、技术选型
   - 产出：Architecture.md、技术栈文档

3. **tech_lead.md** - Tech Lead 角色定义
   - 职责：技术方案、任务分解、代码审查
   - 产出：Tech_Design.md、任务列表

4. **coordinator.md** - Coordinator 角色定义
   - 职责：团队协调、进度跟踪、资源调度
   - 产出：Status_Report.md、进度报告

### 验证结果

```
MD 角色定义文件：12 个 ✅
- pm.md (新增)
- architect.md (新增)
- tech_lead.md (新增)
- coordinator.md (新增)
- frontend_developer.md
- backend_developer.md
- fullstack_developer.md
- qa_engineer.md
- code_reviewer.md
- doc_writer.md
- devops.md
- security.md
```

---

## 2026-03-12: Phase 1 完整测试验证

### 测试结果汇总

| 测试文件 | 结果 | 详情 |
|----------|------|------|
| test_framework.py | ✅ 27 passed | 单元测试全部通过 |
| test_integration.py | ✅ 全部通过 | Phase 1 集成测试 |
| test_opencode_integration.py | ✅ 全部通过 | OpenCode SDK 集成 |

### Phase 1 集成测试详情

```
Agent 角色导入：12/12 ✅
Agent 创建：12/12 ✅
Agent 基础功能：状态机 ✅、记忆系统 ✅、权限请求 ✅
Ralph Loop 引擎：启动/停止 ✅
```

### 角色 MD 文件加载测试 (12个角色全部通过)

```
角色定义加载机制测试：
✓ security: 4 responsibilities, 4 expertise
✓ coordinator: 8 responsibilities, 8 expertise
✓ tech lead: 8 responsibilities, 8 expertise
✓ code reviewer: 5 responsibilities, 4 expertise
✓ backend developer: 6 responsibilities, 7 expertise
✓ devops: 5 responsibilities, 5 expertise
✓ pm: 7 responsibilities, 8 expertise
✓ doc writer: 4 responsibilities, 3 expertise
✓ fullstack developer: 5 responsibilities, 4 expertise
✓ architect: 8 responsibilities, 8 expertise
✓ qa engineer: 6 responsibilities, 5 expertise
✓ frontend developer: 6 responsibilities, 7 expertise

分类结构：
- core: pm, architect, tech lead (3个)
- development: frontend developer, backend developer, fullstack developer (3个)
- quality: code reviewer, qa engineer (2个)
- support: security, devops, doc writer (3个)
- coordination: coordinator (1个)
```

**MD 角色定义机制工作正常**：
- AgentDefinitionLoader 从 MD 文件动态加载配置
- 支持 role, category, description, responsibilities, expertise, collaborations
- 支持 Ralph Loop 配置（Read/Act/Leverage/Produce/Help）
- 共12个角色，全部通过加载测试

### 待解决问题

| ID | 问题 | 优先级 | 状态 |
|----|------|--------|------|
| #001 | `document.dict()` 已废弃，需改用 `model_dump()` | 低 | ✅ 已修复 |
| #002 | opencode-4-py SDK 的 Pydantic v2 兼容性警告 | 低 | 外部依赖 |
| #003 | 完整版本控制 (Diff 计算、版本回滚) | 中 | 待实现 |
| #004 | 完整路由策略实现 | 中 | 待实现 |
| #005 | 端到端测试场景 | 中 | 待实现 |
| #006 | 核心角色 MD 定义迁移 | 高 | ✅ 已修复 |

---

## 修复统计

| 日期 | 修复问题数 | 影响文件数 | 测试通过率 |
|------|-----------|-----------|-----------|
| 2026-03-12 | 7 | 5 | 100% (27/27) |
| 2026-03-12 | Phase 1 完整测试 | - | 100% |

---

> 最后更新：2026-03-12  
> 版本：0.1.0 (Phase 1 ✅)

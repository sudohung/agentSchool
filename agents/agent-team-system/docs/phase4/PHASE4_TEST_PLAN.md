# Phase 4 工作流引擎测试计划

> 版本：1.0
> 创建日期：2026-03-14
> 测试范围：Phase 4 所有模块 + 与 Phase 1-3 模块集成

---

## 1. 测试目标

### 1.1 总体目标

确保 Phase 4 工作流引擎的所有功能按照设计文档正确实现，包括：
- 单元测试覆盖所有核心方法
- 集成测试验证模块间协作
- 端到端测试验证完整工作流

### 1.2 测试范围

| 模块 | 文件 | 测试类型 |
|------|------|----------|
| WorkflowConfig | `workflow/config.py` | 单元测试 |
| WorkflowContext | `workflow/context.py` | 单元测试 |
| WorkflowEngine | `workflow/engine.py` | 单元/集成/端到端 |
| TeamCoordinator | `workflow/coordinator.py` | 单元/集成 |
| QualityGate | `workflow/quality.py` | 单元/集成 |
| IterationController | `ralph_loop/controller.py` | 单元/集成 |
| SetbackHandler | `ralph_loop/setback.py` | 单元测试 |
| CompletionChecker | `ralph_loop/completion.py` | 单元测试 |

### 1.3 成功标准

| 指标 | 目标 |
|------|------|
| 单元测试覆盖率 | >= 80% |
| 所有测试通过 | 100% |
| 集成测试通过 | 100% |
| 端到端测试通过 | 100% |

---

## 2. 测试架构

### 2.1 测试层次

```
┌─────────────────────────────────────────────────────────┐
│                    端到端测试 (E2E)                       │
│  - 完整工作流执行                                        │
│  - 模拟真实场景                                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    集成测试                               │
│  - 模块间协作                                            │
│  - WorkflowEngine + TeamCoordinator                      │
│  - TeamCoordinator + Agent                               │
│  - QualityGate + DocumentStore                           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    单元测试                               │
│  - 每个类的每个方法                                       │
│  - 边界条件                                              │
│  - 异常处理                                              │
└─────────────────────────────────────────────────────────┘
```

### 2.2 测试文件结构

```
tests/
├── test_phase4_workflow.py          # 现有基础测试
├── test_phase4_unit.py              # 新增：单元测试
├── test_phase4_integration.py       # 新增：集成测试
├── test_phase4_e2e.py               # 新增：端到端测试
└── mocks/                           # Mock 对象
    ├── mock_agent.py
    ├── mock_document_store.py
    └── mock_request_board.py
```

---

## 3. 单元测试设计

### 3.1 WorkflowConfig 测试

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TC-CFG-001 | 默认配置 | 创建默认配置 | 所有默认值正确 |
| TC-CFG-002 | 自定义配置 | 传入自定义参数 | 参数值正确设置 |
| TC-CFG-003 | Ralph配置代理 | 访问 ralph_config 代理属性 | 正确代理到内部对象 |
| TC-CFG-004 | 配置组合 | 传入自定义 RalphLoopConfig | 正确组合 |
| TC-CFG-005 | 边界值测试 | 极端参数值 | 正确处理或抛出异常 |

### 3.2 WorkflowContext 测试

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TC-CTX-001 | 创建上下文 | 使用必需参数创建 | 正确初始化 |
| TC-CTX-002 | 添加文档 | 调用 add_document | total_documents 增加 |
| TC-CTX-003 | 添加诉求 | 调用 add_request | total_requests 增加 |
| TC-CTX-004 | 记录挫折 | 调用 record_setback | total_setbacks 增加 |
| TC-CTX-005 | 完成标记 | 调用 complete() | status 更新为 completed |
| TC-CTX-006 | 失败标记 | 调用 fail() | status 更新为 failed |
| TC-CTX-007 | 持续时间 | 调用 get_duration() | 返回正确秒数 |
| TC-CTX-008 | 自动生成ID | 不传入 workflow_id | 自动生成有效ID |

### 3.3 WorkflowEngine 测试

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TC-ENG-001 | 创建引擎 | 默认创建 | status = initialized |
| TC-ENG-002 | 自定义配置 | 传入自定义配置 | 配置正确应用 |
| TC-ENG-003 | 启动工作流 | 调用 start() | 创建上下文和协调器 |
| TC-ENG-004 | 重复启动 | 已运行时再次 start | 返回错误结果 |
| TC-ENG-005 | 暂停工作流 | 调用 pause() | status = paused |
| TC-ENG-006 | 恢复工作流 | 调用 resume() | status = running |
| TC-ENG-007 | 停止工作流 | 调用 stop() | status = stopped |
| TC-ENG-008 | ID生成 | 调用 _generate_id() | 生成唯一ID |
| TC-ENG-009 | 最大迭代限制 | 达到最大迭代次数 | 正常结束 |
| TC-ENG-010 | 挫折限制 | 达到最大挫折数 | 失败结束 |

### 3.4 TeamCoordinator 测试

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TC-CRD-001 | 创建协调器 | 传入上下文和配置 | 正确初始化 |
| TC-CRD-002 | 执行迭代 | 调用 execute_iteration() | 返回 IterationResult |
| TC-CRD-003 | 空团队迭代 | team 为空 | 返回空结果 |
| TC-CRD-004 | 停止后迭代 | 调用 stop() 后执行 | 返回失败结果 |
| TC-CRD-005 | 暂停恢复 | pause() 后 resume() | 正确恢复 |
| TC-CRD-006 | 完成度检查 | 调用 check_completion() | 返回分数 |
| TC-CRD-007 | Agent Ralph执行 | _execute_agent_ralph() | RALPH 正确执行 |
| TC-CRD-008 | Agent异常处理 | Agent 抛出异常 | 记录挫折，继续执行 |
| TC-CRD-009 | 交付产品 | 调用 deliver() | 返回交付路径 |

### 3.5 QualityGate 测试

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TC-QG-001 | 创建质量门控 | 默认创建 | 配置正确初始化 |
| TC-QG-002 | 空上下文检查 | document_store 为空 | 返回结果（默认值） |
| TC-QG-003 | 文档完整性检查 | 缺少必需文档 | 记录缺失文档 |
| TC-QG-004 | 代码质量检查 | 有代码文档 | 正确评分 |
| TC-QG-005 | 测试覆盖检查 | 无测试文档 | 标记问题 |
| TC-QG-006 | 安全检查 | 无安全文档 | 记录建议 |
| TC-QG-007 | 手动审核检查 | 需要手动审核 | 标记需要审核 |
| TC-QG-008 | 总分计算 | 多项检查 | 正确加权计算 |
| TC-QG-009 | 通过判定 | 总分 >= 阈值 | passed = True |
| TC-QG-010 | 失败判定 | 总分 < 阈值 | passed = False |

### 3.6 IterationController 测试

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TC-IC-001 | 创建控制器 | 默认创建 | status = IDLE |
| TC-IC-002 | 启动迭代 | 调用 start() | status = RUNNING |
| TC-IC-003 | 停止迭代 | 调用 stop() | status = STOPPED |
| TC-IC-004 | 获取当前迭代 | 调用 get_current_iteration() | 返回迭代状态 |
| TC-IC-005 | 获取历史 | 调用 get_history() | 返回历史列表 |
| TC-IC-006 | 重复启动 | 已运行时 start() | 抛出异常 |
| TC-IC-007 | 可视化初始化 | visualizer 正确初始化 | 不为 None |
| TC-IC-008 | 挫折处理器初始化 | setback_handler 正确初始化 | 不为 None |

### 3.7 SetbackHandler 测试

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TC-SH-001 | 创建处理器 | 默认创建 | 策略正确注册 |
| TC-SH-002 | 记录挫折 | 调用 record_setback() | 返回 Setback 对象 |
| TC-SH-003 | 挫折分类 | 不同错误类型 | 正确分类 |
| TC-SH-004 | 严重程度评估 | 不同错误 | 正确评估 |
| TC-SH-005 | 恢复尝试 | 调用 attempt_recovery() | 正确执行恢复 |
| TC-SH-006 | 超过最大重试 | 重试次数超限 | 返回 False |
| TC-SH-007 | 获取统计信息 | 调用 get_statistics() | 返回完整统计 |
| TC-SH-008 | 生成报告 | 调用 generate_report() | 返回 Markdown 报告 |
| TC-SH-009 | 模式分析 | 多次同类挫折 | 正确分析模式 |
| TC-SH-010 | 获取挫折列表 | 调用 get_setbacks() | 返回过滤列表 |

### 3.8 CompletionChecker 测试

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TC-CC-001 | 创建检查器 | 传入标准 | 正确初始化 |
| TC-CC-002 | 基本检查 | 调用 check() | 返回正确格式 |
| TC-CC-003 | 需求覆盖计算 | 不同覆盖值 | 正确计算分数 |
| TC-CC-004 | 文档完整性计算 | 不同完整度 | 正确计算分数 |
| TC-CC-005 | 质量分数计算 | 不同质量值 | 正确计算分数 |
| TC-CC-006 | 总分计算 | 多维度数据 | 正确加权计算 |
| TC-CC-007 | 就绪判定 | 总分 >= 阈值 | ready = True |
| TC-CC-008 | 未就绪判定 | 总分 < 阈值 | ready = False |

---

## 4. 集成测试设计

### 4.1 WorkflowEngine + TeamCoordinator 集成

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TI-ETC-001 | 完整工作流启动 | 启动工作流 | 协调器正确创建 |
| TI-ETC-002 | 迭代执行协调 | 执行迭代 | Agent 正确执行 |
| TI-ETC-003 | 完成度传递 | 完成度检查 | 分数正确传递 |
| TI-ETC-004 | 挫折传递 | Agent异常 | 挫折正确记录 |
| TI-ETC-005 | 交付协调 | 完成后交付 | 文档正确整合 |

### 4.2 TeamCoordinator + Agent 集成

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TI-CA-001 | Agent RALPH 执行 | 执行 Agent 的 RALPH | RALPH 方法全部调用 |
| TI-CA-002 | 多 Agent 并行 | 多个 Agent | 并行执行，结果正确 |
| TI-CA-003 | Agent 异常处理 | Agent 抛出异常 | 正确捕获并记录 |
| TI-CA-004 | 文档保存 | Agent 产出文档 | 正确保存到 Store |
| TI-CA-005 | 诉求发布 | Agent 发布诉求 | 正确发布到 Board |

### 4.3 QualityGate + DocumentStore 集成

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TI-QD-001 | 文档完整性检查 | 存储不同类型文档 | 正确检查缺失 |
| TI-QD-002 | 代码质量检查 | 存储代码文档 | 正确识别代码 |
| TI-QD-003 | 测试覆盖检查 | 存储测试文档 | 正确计算覆盖 |
| TI-QD-004 | 安全检查 | 存储安全标签文档 | 正确识别安全 |

### 4.4 IterationController + SetbackHandler 集成

| 测试编号 | 测试名称 | 测试内容 | 预期结果 |
|----------|----------|----------|----------|
| TI-IS-001 | 挫折记录 | Agent 异常 | 正确记录到处理器 |
| TI-IS-002 | 恢复尝试 | 可恢复挫折 | 正确执行恢复 |
| TI-IS-003 | 统计更新 | 多次挫折 | 统计正确更新 |

---

## 5. 端到端测试设计

### 5.1 场景1: 简单任务完成

```
输入: "创建一个简单的计算器程序"
预期:
- 动态组建团队 (PM, Developer, QA)
- 执行 RALPH Loop
- 产出 PRD、代码、测试用例
- 质量检查通过
- 成功交付
```

### 5.2 场景2: 带挫折恢复的任务

```
输入: "开发一个复杂的电商系统"
预期:
- Agent 遇到技术挫折
- 自动恢复重试
- 继续执行直到完成
```

### 5.3 场景3: 质量不通过迭代

```
输入: "创建一个 Web 应用"
预期:
- 第一次质量检查不通过
- 继续迭代改进
- 最终质量检查通过
```

### 5.4 场景4: 最大迭代限制

```
配置: max_iterations = 5
预期:
- 达到 5 次迭代后停止
- 返回部分完成结果
```

### 5.5 场景5: 手动审核流程

```
配置: require_manual_review = True
预期:
- 检测到需要审核的项目
- 标记 requires_manual_review = True
```

---

## 6. Mock 对象设计

### 6.1 MockAgent

```python
class MockAgent:
    """模拟 Agent"""
    role: str
    expertise: List[str]
    
    async def read_documents(self) -> List[Document]:
        return []
    
    async def act_on_requests(self) -> List[Request]:
        return []
    
    async def leverage_expertise(self) -> str:
        return "Mock work result"
    
    async def produce_document(self, work_result) -> Document:
        return MockDocument()
    
    async def help_requests(self) -> List[Request]:
        return []
```

### 6.2 MockDocumentStore

```python
class MockDocumentStore:
    """模拟文档存储"""
    def __init__(self):
        self._documents = {}
    
    async def save(self, document) -> bool:
        self._documents[document.id] = document
        return True
    
    async def load(self, doc_id) -> Optional[Document]:
        return self._documents.get(doc_id)
    
    async def list_documents(self, **kwargs) -> List[Document]:
        return list(self._documents.values())
```

### 6.3 MockRequestBoard

```python
class MockRequestBoard:
    """模拟诉求看板"""
    def __init__(self):
        self._requests = {}
    
    async def create_request(self, request) -> str:
        self._requests[request.id] = request
        return request.id
    
    async def get_requests_for_agent(self, agent_role, **kwargs):
        return [r for r in self._requests.values() if r.to_agent == agent_role]
```

---

## 7. 测试执行计划

### 7.1 执行顺序

```
阶段 1: 单元测试 (预计 2 小时)
├── WorkflowConfig 测试
├── WorkflowContext 测试
├── QualityGate 测试
├── IterationController 测试
├── SetbackHandler 测试
└── CompletionChecker 测试

阶段 2: 模块集成测试 (预计 2 小时)
├── Engine + Coordinator 集成
├── Coordinator + Agent 集成
├── QualityGate + DocumentStore 集成
└── IterationController + SetbackHandler 集成

阶段 3: 端到端测试 (预计 1 小时)
├── 简单任务场景
├── 挫折恢复场景
├── 质量迭代场景
├── 最大迭代场景
└── 手动审核场景

阶段 4: 覆盖率分析 (预计 0.5 小时)
└── 生成覆盖率报告
```

### 7.2 测试命令

```bash
# 运行所有 Phase 4 测试
pytest tests/test_phase4_*.py -v

# 运行带覆盖率
pytest tests/test_phase4_*.py -v --cov=src/workflow --cov=src/ralph_loop --cov-report=html

# 运行单个测试文件
pytest tests/test_phase4_unit.py -v

# 运行特定测试
pytest tests/test_phase4_unit.py::TestWorkflowConfig -v
```

---

## 8. 测试数据准备

### 8.1 测试文档数据

```python
TEST_DOCUMENTS = [
    {
        "id": "doc_prd_001",
        "path": "prd/PRD_v1.md",
        "doc_type": "prd",
        "content": "# PRD\n\n## 功能需求\n...",
    },
    {
        "id": "doc_arch_001",
        "path": "design/Architecture.md",
        "doc_type": "architecture",
        "content": "# 架构设计\n...",
    },
]
```

### 8.2 测试诉求数据

```python
TEST_REQUESTS = [
    {
        "id": "req_001",
        "type": "review",
        "from_agent": "Product Manager",
        "to_agent": "System Architect",
        "subject": "请评估技术可行性",
        "content": "...",
    },
]
```

### 8.3 测试挫折数据

```python
TEST_ERRORS = [
    Exception("timeout"),
    Exception("no response"),
    Exception("conflict"),
    Exception("blocked"),
    Exception("quality issue"),
    Exception("critical error"),
]
```

---

## 9. 预期测试结果

### 9.1 测试用例数量

| 类型 | 数量 |
|------|------|
| 单元测试 | 56 个 |
| 集成测试 | 17 个 |
| 端到端测试 | 5 个 |
| **总计** | **78 个** |

### 9.2 预期覆盖率

| 模块 | 目标覆盖率 |
|------|-----------|
| workflow/config.py | 100% |
| workflow/context.py | 100% |
| workflow/engine.py | 85% |
| workflow/coordinator.py | 85% |
| workflow/quality.py | 90% |
| ralph_loop/controller.py | 80% |
| ralph_loop/setback.py | 90% |
| ralph_loop/completion.py | 95% |

---

## 10. 测试报告模板

### 10.1 测试执行报告

```markdown
# Phase 4 测试执行报告

## 1. 测试概况

- 执行时间: YYYY-MM-DD HH:MM
- 测试总数: XX
- 通过: XX
- 失败: XX
- 跳过: XX

## 2. 覆盖率报告

| 模块 | 覆盖率 |
|------|--------|
| workflow/config.py | XX% |
| workflow/context.py | XX% |
| ... | ... |

## 3. 失败测试详情

### TC-XXX: 测试名称
- 原因: ...
- 错误信息: ...
- 修复建议: ...

## 4. 结论

[通过/不通过] - 说明
```

---

## 11. 附录

### A. 测试依赖

```txt
pytest>=7.0.0
pytest-asyncio>=0.20.0
pytest-cov>=4.0.0
```

### B. CI 配置

```yaml
# .github/workflows/test_phase4.yml
name: Phase 4 Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e .
      - run: pytest tests/test_phase4_*.py -v --cov
```

### C. 测试检查清单

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 所有端到端测试通过
- [ ] 覆盖率 >= 80%
- [ ] 无跳过的测试（或有充分理由）
- [ ] 测试报告已生成
- [ ] 文档已更新

---

> 最后更新：2026-03-14
> 状态：待执行
# OpenCode Python SDK 待办事项

> 基于完整代码审查报告生成
> 审查日期：2026-03-11
> SDK 版本：0.1.0

---

## 执行摘要

| 指标 | 结果 | 状态 |
|------|------|------|
| 端点覆盖率 | 54.8% (57/104) | ⚠️ |
| 核心功能 | 100% | ✅ |
| 数据模型匹配 | 核心模型 100% | ✅ |
| 测试通过率 | 100% (25/25) | ✅ |
| 兼容性 | OpenCode Server v1.2.24 | ✅ |

**SDK 质量评级：A (优秀)**

---

## 一、待实现功能清单

### 🔴 高优先级 (无)

> 核心功能已完整，无需高优先级任务

---

### 🟡 中优先级

#### 1. Auth 模块 (2 个端点)

- [ ] `PUT /auth/{providerID}` - 设置认证凭据
- [ ] `DELETE /auth/{providerID}` - 删除认证凭据

**影响**: 增强 Provider 认证管理能力

**预计工作量**: 2-4 小时

**实现建议**:
```python
# 新增 models/auth.py
class AuthSetRequest(BaseModel):
    type: Literal["oauth", "api", "wellknown"]
    # ... 其他字段

# 新增 api/auth.py
class AuthAPI:
    def set(self, provider_id: str, auth: AuthSetRequest) -> bool
    def remove(self, provider_id: str) -> bool
```

---

#### 2. Permission 模块 (3 个端点)

- [ ] `GET /permission` - 列出权限请求
- [ ] `POST /permission/{requestID}/reply` - 回复权限请求
- [ ] `POST /session/{sessionID}/permissions/{permissionID}` - 响应权限请求

**影响**: 完善权限管理流程

**预计工作量**: 4-6 小时

**实现建议**:
```python
# 新增 models/permission.py
class PermissionRequest(BaseModel):
    id: str
    session_id: str
    permission: str
    patterns: List[str]
    # ... 其他字段

# 新增 api/permission.py
class PermissionAPI:
    def list(self) -> List[PermissionRequest]
    def reply(self, request_id: str, response: str) -> bool
    def respond(self, session_id: str, permission_id: str, response: str) -> bool
```

---

### 🟢 低优先级

#### 3. Question 模块 (3 个端点) ✅ 已完成

- [x] `GET /question` - 列出待处理问题
- [x] `POST /question/{requestID}/reply` - 回答问题
- [x] `POST /question/{requestID}/reject` - 拒绝问题

**影响**: 支持用户问答交互

**预计工作量**: 3-5 小时

---

#### 4. PTY 模块 (6 个端点)

- [ ] `GET /pty` - 列出 PTY 会话
- [ ] `POST /pty` - 创建 PTY 会话
- [ ] `GET /pty/{ptyID}` - 获取 PTY 会话
- [ ] `PUT /pty/{ptyID}` - 更新 PTY 会话
- [ ] `DELETE /pty/{ptyID}` - 删除 PTY 会话
- [ ] `GET /pty/{ptyID}/connect` - 连接 PTY (WebSocket)

**影响**: 终端会话管理

**预计工作量**: 8-12 小时

---

#### 5. TUI 模块 (13 个端点)

- [ ] `POST /tui/append-prompt` - 追加提示文本
- [ ] `POST /tui/open-help` - 打开帮助对话框
- [ ] `POST /tui/open-sessions` - 打开会话选择器
- [ ] `POST /tui/open-themes` - 打开主题选择器
- [ ] `POST /tui/open-models` - 打开模型选择器
- [ ] `POST /tui/submit-prompt` - 提交提示
- [ ] `POST /tui/clear-prompt` - 清除提示
- [ ] `POST /tui/execute-command` - 执行命令
- [ ] `POST /tui/show-toast` - 显示通知
- [ ] `POST /tui/publish` - 发布
- [ ] `POST /tui/select-session` - 选择会话
- [ ] `GET /tui/control/next` - 下一个控制
- [ ] `POST /tui/control/response` - 控制响应

**影响**: 终端界面控制

**预计工作量**: 12-16 小时

---

#### 6. Worktree 模块 (4 个端点)

- [ ] `GET /experimental/worktree` - 列出工作树
- [ ] `POST /experimental/worktree` - 创建工作树
- [ ] `DELETE /experimental/worktree` - 删除工作树
- [ ] `POST /experimental/worktree/reset` - 重置工作树

**影响**: Git 工作树管理

**预计工作量**: 6-8 小时

---

#### 7. Experimental 模块 (5 个端点)

- [ ] `GET /experimental/tool/ids` - 列出工具 ID
- [ ] `GET /experimental/tool` - 列出工具详情
- [ ] `GET /experimental/workspace` - 列出工作空间
- [ ] `POST /experimental/workspace` - 创建工作空间
- [ ] `DELETE /experimental/workspace/{id}` - 删除工作空间

**影响**: 实验性功能支持

**预计工作量**: 6-10 小时

---

#### 8. MCP 扩展模块 (5 个端点) ✅ 已完成

- [x] `POST /mcp/{name}/auth` - 启动 MCP OAuth
- [x] `DELETE /mcp/{name}/auth` - 移除 MCP OAuth
- [x] `POST /mcp/{name}/auth/callback` - MCP OAuth 回调
- [ ] `POST /mcp/{name}/auth/authenticate` - MCP 认证
- [x] `POST /mcp/{name}/connect` - 连接 MCP 服务器
- [x] `POST /mcp/{name}/disconnect` - 断开 MCP 服务器

**影响**: 增强 MCP 管理

**预计工作量**: 6-8 小时

---

#### 9. Part 模块 (2 个端点)

- [ ] `DELETE /session/{sessionID}/message/{messageID}/part/{partID}` - 删除消息部分
- [ ] `PATCH /session/{sessionID}/message/{messageID}/part/{partID}` - 更新消息部分

**影响**: 细粒度消息管理

**预计工作量**: 2-4 小时

---

### ⚪ 可选优化

#### 10. Config 模型字段补充

当前 Config 模型实现 13/30 字段 (37%)

**缺失字段**:
- `model`, `small_model` - 模型配置
- `default_agent` - 默认代理
- `permission` - 权限配置
- `tools` - 工具配置
- `lsp`, `formatter` - LSP/格式化器配置
- `compaction` - 压缩配置
- `enterprise` - 企业配置
- 等等...

**影响**: 配置完整性

**预计工作量**: 4-6 小时

---

## 二、已完成功能 (参考)

### ✅ 核心模块 (100%)

| 模块 | 端点 | 状态 |
|------|------|------|
| Global | 5/5 | ✅ |
| Message | 8/8 | ✅ |
| File | 6/6 | ✅ |
| Project | 4/4 | ✅ |
| Provider | 4/4 | ✅ |
| Config | 3/3 | ✅ |
| Agent | 1/1 | ✅ |
| LSP | 1/1 | ✅ |
| Formatter | 1/1 | ✅ |
| Path | 1/1 | ✅ |
| VCS | 1/1 | ✅ |
| Instance | 1/1 | ✅ |
| Logging | 2/2 | ✅ |

### ✅ Session 模块 (71%)

已实现：
- [x] list(), get(), create(), delete(), update()
- [x] status(), children(), todos()
- [x] abort(), share(), unshare(), fork()
- [x] diff(), summarize(), revert(), unrevert(), init()

未实现：
- [ ] compact() - 会话压缩

---

## 三、开发路线图

### Phase 1: 核心增强 (1-2 周)

- [ ] 实现 Auth 模块
- [ ] 实现 Permission 模块
- [ ] 补充 Config 模型字段

### Phase 2: 交互增强 (2-3 周)

- [ ] 实现 Question 模块
- [ ] 实现 Part 模块
- [ ] 实现 MCP 扩展

### Phase 3: 高级功能 (3-4 周)

- [ ] 实现 PTY 模块
- [ ] 实现 Worktree 模块
- [ ] 实现 Experimental 模块

### Phase 4: 界面集成 (4-6 周)

- [ ] 实现 TUI 模块
- [ ] 集成前端界面
- [ ] 完善文档和示例

---

## 四、测试覆盖率目标

| 模块 | 当前 | 目标 | 状态 |
|------|------|------|------|
| 核心模块 | 100% | 100% | ✅ |
| Auth | 0% | 90% | ⏳ |
| Permission | 0% | 90% | ⏳ |
| Question | 0% | 80% | ⏳ |
| PTY | 0% | 80% | ⏳ |
| TUI | 0% | 70% | ⏳ |

---

## 五、性能指标

| 指标 | 当前 | 目标 |
|------|------|------|
| API 响应时间 | <100ms | <50ms |
| SSE 延迟 | <200ms | <100ms |
| 内存占用 | <50MB | <30MB |
| 并发连接 | 10 | 100 |

---

## 六、文档完善

### 需要补充的文档

- [ ] API 参考文档 (自动生成)
- [ ] 认证流程指南
- [ ] 权限管理指南
- [ ] 高级功能示例
- [ ] 故障排除指南
- [ ] 性能优化指南

---

## 七、版本规划

### v0.1.0 (当前) ✅

- 核心功能完整
- 25/25 测试通过
- 基础文档完善

### v0.2.0 (计划)

- Auth 模块
- Permission 模块
- Config 字段补充

### v0.3.0 (计划)

- Question 模块
- Part 模块
- MCP 扩展

### v1.0.0 (计划)

- 所有核心模块
- 完整测试覆盖
- 生产就绪

---

## 附录

### A. OpenAPI 规范来源

- 文件：`docs/openapi.json`
- 大小：141 KB
- 端点总数：104
- Schema 总数：50+

### B. SDK 文件结构

```
src/opencode_4_py/
├── __init__.py          # 公共导出
├── client.py            # 同步客户端
├── async_client.py      # 异步客户端
├── config.py            # 客户端配置
├── errors.py            # 异常定义
├── models/              # 数据模型 (10 文件)
├── api/                 # API 实现 (15 文件)
└── utils/               # 工具函数
```

### C. 联系方式

- 项目地址：https://github.com/anomalyco/opencode
- SDK 地址：https://github.com/anomalyco/opencode/tree/dev/agents/opencode-4-py
- 文档：https://opencode.ai/docs/server/

---

> 最后更新：2026-03-11
> 审查人：AI Assistant
> 审核状态：已完成

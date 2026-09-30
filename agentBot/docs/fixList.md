# agentBot 代码审查问题清单（fixList）

## Round 1

### FIX-001: replyQuestion 依赖不存在的 SDK API（P0）

**File**: `agentBot/src/agent/opencode-agent.js:109-120`

**Problem**: `client.question.reply` 在已安装的 SDK（1.18.33，v1 gen 风格）中不存在（仅 v2 1.14.40 有），运行时必然抛 TypeError，question 闭环实际失效。且 answers 的正确形状是 `string[][]`（每个 question 对应一个选中 label 数组），当前传的是 `[message]`。

**Fix**: 改用原生 fetch 调 `${OPENCODE_BASE_URL}/question/{requestID}/reply`，body 为 `{ answers: [[label]] }`，每个问题一条答案。

### FIX-002: 待处理交互拦截命令，/permit 永远无法执行（P0）

**File**: `agentBot/src/events/interaction-manager.js:90-127`、`agentBot/src/handlers/message-handler.js:67-71`

**Problem**: `routeReply` 在命令路由之前执行。权限请求 pending 时用户发 `/permit:once` 会被当作普通回复消费掉（提示"请用 /permit"），命令死锁无法到达；question pending 时发 `/new` 会被当答案提交给 question.reply。

**Fix**: `routeReply` 对以 `/` 开头的消息直接返回 false，放行给命令路由。

### FIX-003: question 多问题场景答案错位（P0）

**File**: `agentBot/src/events/interaction-manager.js`

**Problem**: `event.properties.questions` 可能有多个问题，当前只给第一个问题回答案（`answers: [message]`），其余问题丢失，AI 侧将一直阻塞。

**Fix**: 按问题数量生成答案数组；若用户回复恰好是某问题的选项 label，按选项匹配，否则每个问题都用该文本作答。

### FIX-004: 串行锁条目永不清理，内存泄漏（P1）

**File**: `agentBot/src/agent/session-manager.js:159-169`

**Problem**: `#sessionLocks.set(sessionId, task.catch(()=>{}))` 存入的是新 Promise，而 finally 中用 `=== task` 比较，恒为 false，锁条目永不删除，随会话数无限增长。

**Fix**: 先保存 `const guarded = task.catch(()=>{})`，以 guarded 入表并比较删除。

### FIX-005: message-handler 未使用的导入（P1）

**File**: `agentBot/src/handlers/message-handler.js:6-7`

**Problem**: `BotConfig`、`PermissionAction` 导入后未使用。

**Fix**: 删除。

### FIX-006: opencode-listener 未使用的导入（P1）

**File**: `agentBot/src/events/opencode-listener.js:12`

**Problem**: `sendTextMessage` 导入后未使用（实际使用在 interaction-manager）。

**Fix**: 删除。

### FIX-007: SessionManager.abort() 死代码且逻辑有误（P1）

**File**: `agentBot/src/agent/session-manager.js:194-198`

**Problem**: 全项目无人调用；且允许 agentKey 与 sessionId 不匹配组合，调用会 abort 到错误的 agent。

**Fix**: 删除该方法（统一走 abortSession）。

### FIX-008: CommandRouter.route 的 interaction 参数从未使用（P1）

**File**: `agentBot/src/handlers/commands.js:151-154`

**Problem**: JSDoc 声称 interaction 含 getPending/setPending/removePending（实际不存在），参数在方法体内也从未使用，误导调用方。

**Fix**: 移除参数，同步修改调用处 `message-handler.js:74`。

### FIX-009: 事件订阅失败后无法恢复（P1）

**File**: `agentBot/src/events/opencode-listener.js:54-66`、`agentBot/src/index.js:35-39`

**Problem**: OpenCode 服务未就绪或 SSE 断开时 `subscribe` 抛出/流结束，监听永久失效，仅打印一条错误，机器人事件功能静默死亡。

**Fix**: start() 增加带指数退避的自动重连循环。

### FIX-010: session.idle 后流式"思考中"卡片残留（P2）

**File**: `agentBot/src/events/opencode-listener.js:136-141`

**Problem**: 事件流建了"🤔 思考中"卡片，session.idle 只删状态不处理消息，残留一张只有 reasoning 的卡片；与 message-handler 的 Thinking 卡片重复展示。

**Fix**: session.idle 时撤回流式卡片（recallMessage），最终回复仍写回 message-handler 的 Thinking 卡片。

### FIX-011: /reply 命令注释与实现不符（P3）

**File**: `agentBot/src/handlers/commands.js:132`

**Problem**: 注释写"noReply 模式下的应答通道"，实际就是一次普通阻塞 prompt。

**Fix**: 修正注释。

### FIX-012: 交互事件前的 500ms 魔法等待（P3）

**File**: `agentBot/src/events/opencode-listener.js:149,158`

**Problem**: 魔法数字散落两处，无说明。

**Fix**: 提取常量 `EVENT_DISPATCH_DELAY` 并注释用途。

### FIX-013: InteractionManager.question reply 重复实现（P2）

**File**: `agentBot/src/events/interaction-manager.js` / `agentBot/src/agent/opencode-agent.js`

**Problem**: Round 1 修复后在 InteractionManager 与 OpencodeAgent 各留了一份 fetch 实现。

**Fix**: 收敛到 OpencodeAgent.replyQuestion，InteractionManager 仅调用。

### FIX-014: commands.js #log 死方法（P3）

**File**: `agentBot/src/handlers/commands.js:22`

**Problem**: 定义后从未调用。

**Fix**: 删除。

### FIX-015: replyQuestion 的 sessionId 参数未使用（P3）

**File**: `agentBot/src/agent/opencode-agent.js:111`

**Problem**: HTTP URL 仅需要 requestId，sessionId 参数无效。

**Fix**: 移除参数，同步更新调用处。

### FIX-016: PendingInteraction.NONE 死常量（P3）

**File**: `agentBot/src/constants.js`

**Problem**: 定义后无引用。

**Fix**: 删除。

### Round 1
- [x] FIX-001: replyQuestion 依赖不存在的 SDK API
- [x] FIX-002: 待处理交互拦截命令
- [x] FIX-003: question 多问题答案错位
- [x] FIX-004: 串行锁条目永不清理
- [x] FIX-005: message-handler 未使用导入
- [x] FIX-006: opencode-listener 未使用导入
- [x] FIX-007: SessionManager.abort() 死代码
- [x] FIX-008: route 的 interaction 参数未使用
- [x] FIX-009: 事件订阅失败后无法恢复
- [x] FIX-010: session.idle 后流式卡片残留
- [x] FIX-011: /reply 注释不符
- [x] FIX-012: 500ms 魔法等待

### Round 2
- [x] FIX-013: question reply 重复实现收敛
- [x] FIX-014: #log 死方法
- [x] FIX-015: replyQuestion 无效参数
- [x] FIX-016: NONE 死常量

### Round 3
无新问题（仅剩余注释类 P3，已停止迭代）

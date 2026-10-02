# agentBot - 飞书 × OpenCode Agent 机器人

从 `plugins/fxbot` + `plugins/feishu-bot` 重构而来的飞书机器人，接入 OpenCode 作为 AI 引擎。

## 核心功能

| 功能 | 说明 |
|---|---|
| 飞书消息接入 | WebSocket 长连接收消息，支持私聊 / 群聊@机器人 |
| AI 对话 | 消息转发给 OpenCode Session，回复写回飞书卡片 |
| 多模型切换 | `agents.json` 配置驱动，按群独立切换 Agent |
| 思考过程流式展示 | 订阅 `message.part.updated`，节流更新 reasoning 到卡片 |
| 工具提问闭环 | `question.asked` 转发用户，回复自动调用 `question.reply` 回传 |
| 权限请求闭环 | `permission.asked` 转发用户，`/permit:once\|always\|reject` 响应 |
| 会话管理 | `/new` 重置、`/sessions` 列表、`/session:<id>` 切换、`/abort` 中断 |
| 异常通知 | 会话错误/重试通过聊天卡片 + Webhook 双通道通知 |
| 安全控制 | 消息去重、过期消息丢弃、群黑名单（`config/ban.json`） |

## 命令列表

```
/new                 重置会话
/agents              列出可用 Agent
/model:<key>         切换 Agent 模型（兼容旧命令 /instant:<key>）
/sessions            列出会话
/session:<id>        切换会话
/abort               中断当前会话
/permit:<action>     响应权限请求（once/always/reject）
/reply:<内容>        直接发送应答
/help                显示帮助
```

## 整体流程

```mermaid
flowchart TD
    A[飞书用户发消息] --> B[WS 网关<br/>去重/过期丢弃]
    B --> C{过滤链}
    C -->|群消息未@| X1[丢弃]
    C -->|黑名单| X2[丢弃]
    C -->|通过| D[消息处理器]
    D --> E{存在待处理交互?<br/>question/permission}
    E -->|是| F[作为答案/权限响应回传 OpenCode]
    E -->|否| G{是否 / 命令}
    G -->|是| H[命令路由执行<br/>new/model/sessions/...]
    G -->|否| I[SessionManager<br/>串行锁排队]
    I --> J[OpenCode Agent<br/>session.prompt]
    J --> K[回复写回飞书卡片]
    L[OpenCode 事件流] --> M{事件类型}
    M -->|message.part.updated| N[流式更新思考卡片]
    M -->|session.idle| O[清理流式状态]
    M -->|question.asked| P[转发提问到聊天<br/>等待用户回复闭环]
    M -->|permission.asked| Q[转发权限请求<br/>等待 /permit 闭环]
    M -->|session.error| R[卡片+Webhook 告警]
```

## 目录结构

```
agentBot/
├── package.json
├── .env.example            # 环境变量模板
├── config/
│   ├── agents.json         # Agent/模型注册表（新增模型改这里）
│   └── ban.json            # 群黑名单
└── src/
    ├── index.js            # 应用装配入口
    ├── constants.js        # 枚举常量
    ├── config/bot-config.js        # 环境配置与校验
    ├── feishu/
    │   ├── feishu-gateway.js       # WS 长连接 + 消息去重
    │   ├── message-sender.js       # 消息发送/更新/撤回（带重试）
    │   └── chat-service.js         # 群管理 API
    ├── handlers/
    │   ├── filters.js              # 过滤链
    │   ├── commands.js             # 命令路由（策略注册表）
    │   └── message-handler.js      # 消息编排
    ├── events/
    │   ├── opencode-listener.js    # 事件订阅主循环
    │   └── interaction-manager.js  # question/permission 闭环
    ├── api/                        # Agent API（供其他智能体经 MCP 调用）
    │   ├── mcp-server.js           # MCP Streamable HTTP（JSON-RPC 2.0）
    │   ├── api-session-manager.js  # 会话凭证生成/绑定映射/持久化
    │   └── task-queue.js           # 同步/异步任务队列 + 反问闭环
    ├── agent/
    │   ├── opencode-agent.js       # OpenCode 策略实现
    │   ├── agent-registry.js       # 配置驱动注册表（单一 client）
    │   ├── role-registry.js        # 职能注册表（roles.json 热重载）
    │   ├── instance-pool.js        # 多 OpenCode 实例 client 池
    │   └── session-manager.js      # 会话映射/上下文/串行锁
    └── webhook/webhook-sender.js   # Webhook 通知
```

## 配置管理页（8081）

启动后访问 `http://<host>:8081`：

- **OpenCode 服务地址**：修改后保存会自动重启服务（Docker `restart: always` 自动拉起）
- **Agent 模型列表**：增删改模型（key/provider/model/说明），保存后**热生效**，无需重启
- **默认 Agent**：新会话使用的模型
- **实例注册表 / 职能列表**：Agent API 通道使用的多 OpenCode 实例与职能管理，保存后热生效
- 可选安全：设置环境变量 `ADMIN_TOKEN` 后，API 需携带 `x-admin-token` 请求头

配置持久化在 `config/bot.json`（优先于环境变量），`OPENCODE_BASE_URL` 环境变量仅作初始兜底。

## Agent API（MCP，供其他智能体调用）

agentBot 同时以 MCP Server 形式对外提供服务（默认端口 8082，Docker 部署为 8083），
opencode / codex 等支持 MCP 的智能体可将其挂载为工具服务器：

| 工具 | 说明 |
|---|---|
| `list_roles` | 获取可用职能列表（管理页可配置） |
| `apply_session` | 按职能申请会话，返回 `callerSessionId`（格式：职能key_uuid），调用方自行保存 |
| `chat` | 向指定会话发消息；默认异步返回 `taskId` 用 `get_result` 轮询，`wait=true` 同步等待 |
| `get_result` | 轮询任务结果（pending / waiting_input（agent 反问）/ done / failed） |
| `close_session` | 主动释放会话凭证 |

- 同一 `callerSessionId` 的请求串行执行；不同凭证并行（受全局并发上限约束）
- 不同凭证即不同会话，可同时持有多个职能的会话按需指定
- 每个职能可独立配置 OpenCode 实例与模型（管理页），留空用全局配置
- 会话空闲超时自动清理（默认 24h）；绑定关系持久化，服务重启后凭证仍有效

## Docker 部署

```bash
cd agentBot
cp .env.example .env    # 填写 FEISHU_APP_ID / FEISHU_APP_SECRET

# 一键部署（构建 + 启动，自动重启）
bash deploy.sh

# 或手动
docker compose up -d --build
docker logs -f agent-bot
```

`docker-compose.yml` 已配置：
- `restart: always`：进程崩溃/宿主机重启后自动拉起
- `./config:/app/config` 卷挂载：配置页修改持久化到宿主机
- 日志轮转（10MB × 3）
- 健康检查（HEALTHCHECK）

## 快速开始

```bash
cd agentBot
npm install
cp .env.example .env    # 填写 FEISHU_APP_ID / FEISHU_APP_SECRET
npm start
```

## 相对旧版的改进

1. **配置驱动**：模型列表、默认 Agent、服务地址全部外置（`agents.json` + `.env`），消除 10+ 个硬编码 Agent 与 4 个重复 client。
2. **修复坏锁**：`session-manager.js` 以 sessionId 为粒度实现真正的串行队列（旧版锁代码被注释一半，存在不可达代码）。
3. **交互闭环**：`question.asked` 的用户回复通过 SDK `question.reply` 回传（旧版只发通知，回复当普通消息丢失）；权限响应支持新旧两版 SDK 自动降级。
4. **修复未 await**：卡片 `patch` 更新正确等待并处理错误（旧版 `.then().catch()` 吞错）。
5. **单一职责**：拆分旧版 ChatManager 神类为 `ChatService`（群 API）+ `SessionManager`（会话/上下文）+ `InteractionManager`（交互闭环）。
6. **清理死代码**：移除 `permission.asked1` 分支、未使用的 `createOpencode` 导入、写死的默认 chatId/IP。
7. **健壮性**：消息发送带指数退避重试、事件处理逐条隔离异常、配置启动时校验并快速失败。

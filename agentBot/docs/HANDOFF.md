# agentBot 交接文档（HANDOFF）

> 交接时间：2026-09-30 ｜ 交接来源：本容器内 opencode 会话
> 目标读者：接手的 agent，请先通读本文档再动手。

## 一、项目背景

用户要求将旧飞书机器人（`/workspace/agentSchool/agentSchool/plugins/fxbot/client/feishu-client.js` + `plugins/feishu-bot/`）重构为新项目 **`/workspace/agentSchool/agentSchool/agentBot/`**。

旧版问题：10+ 硬编码 Agent、4 个重复 client、坏锁代码、question/permission 交互断头、ChatManager 神类、大量死代码。

## 二、已完成的工作（不要重做）

### 2.1 项目结构（全部已实现并测试通过）

```
agentBot/
├── package.json            # ESM, deps: @larksuiteoapi/node-sdk ^1.59, @opencode-ai/sdk ^1.14.40(实际装1.18.33), dotenv
├── .env                    # 已配置真实飞书凭证（勿提交/勿泄露）
├── .env.example
├── config/
│   ├── bot.json            # 运行时配置：opencodeBaseUrl + agents + defaultKey（配置页读写此文件）
│   ├── agents.json         # 旧配置（迁移兜底，可忽略）
│   └── ban.json            # 群黑名单
├── src/
│   ├── index.js            # 装配入口：飞书网关 + OpenCode 监听 + AdminServer(8081)
│   ├── constants.js        # 枚举
│   ├── config/bot-config.js
│   ├── feishu/             # gateway(WS长连接+去重)、message-sender(重试)、chat-service(群API)
│   ├── agent/              # opencode-agent、agent-registry(热重载)、session-manager(串行锁)
│   ├── handlers/           # filters、commands(命令路由)、message-handler(编排)
│   ├── events/             # opencode-listener(自动重连)、interaction-manager(question/permission闭环)
│   ├── webhook/webhook-sender.js
│   └── admin/admin-server.js  # 8081 配置管理页
├── Dockerfile / docker-compose.yml / .dockerignore / deploy.sh
└── docs/fixList.md         # 16 个已修复问题清单
```

### 2.2 关键技术结论（重要，避免踩坑）

1. **OpenCode 服务器 API 版本**：`172.22.221.176:4097` 是新版 API（`/session/{sessionID}/message`，body 为 `{model:{providerID,modelID}, parts:[...]}`）。SDK 1.18.33 的调用方式与之兼容（path 参数名不影响实际 URL）。**旧 provider（0~4 号）全部没有 API key，prompt 必 500 "UnknownError"**。
2. **唯一可用的模型提供方是 `fuyao`（Fuyao AI Gateway）**，key 内置于服务端配置，模型：fuyao-coding-high/max、fuyao-work-low/high/max、fuyao-data-medium/low/xhigh。已实测 `fuyao-coding-high` 对话成功（200）。
3. `config/bot.json` 当前内容：`opencodeBaseUrl=http://172.22.221.176:4097`，6 个 fuyao agent，默认 main。
4. 飞书连接用 WS 长连接模式（无需公网回调），凭证在 `.env`。
5. 代码 review 已完成 3 轮（见 docs/fixList.md，16 项全部修复）：坏锁、命令被交互拦截、question answers 形状（须为 string[][]）等。
6. **配置页热重载**：改模型 → 立即生效；改 URL → 保存后 3s 进程退出，靠 Docker restart:always 拉起。
7. 端口：配置页默认 8081（`ADMIN_PORT` 可改）；本沙箱 8081 被占用，本地验证用 8082。

## 三、当前运行状态

- 机器人进程正在本容器运行：`ADMIN_PORT=8082 node src/index.js`（PID 5119，日志 /tmp/agentbot.log）
- 飞书长连接 ✓、OpenCode 事件订阅 ✓、配置页 8082 ✓
- 用户已在飞书验证过收消息和报错提示链路；fuyao 模型切换后**尚待用户最终确认对话正常**

## 四、剩余工作（按优先级）

### W1. Docker 部署（核心待办）
本容器无 Docker daemon，需要你在**有 Docker 的机器**上执行：
```bash
cd /workspace/agentSchool/agentSchool/agentBot   # 若文件系统不共享，先从本路径拷贝整个 agentBot 目录
cp .env.example .env   # 已有 .env 则跳过（注意：.env 含真实凭证，不在 git 中）
bash deploy.sh          # 构建 + up -d，restart: always
docker logs -f agent-bot
```
验证：容器自启（docker inspect 查 RestartCount/restart policy）、配置页 http://<host>:8081 可访问、修改模型热生效、修改 URL 自动重启拉起。

### W2. 端到端验证
- 飞书私聊/群聊@机器人 对话（fuyao 模型）
- `/help` `/agents` `/model:max` `/new` `/abort` 命令
- 工具提问（question）回复闭环、权限请求 `/permit:once|always|reject` 闭环
- 思考过程流式卡片展示与撤回

### W3. 可选加固
- ADMIN_TOKEN 设置（防内网裸奔）
- 会话映射/处理标记当前在内存，容器重启丢失（可考虑持久化）
- message.part.updated 流式卡片与 Thinking 卡片双展示的体验优化

## 五、操作手册摘要

命令：`/new` `/agents` `/model:<key>`（兼容 `/instant:`）`/sessions` `/session:<id>` `/abort` `/permit:<once|always|reject>` `/reply:<内容>` `/help`

架构流程：飞书 WS 收消息 → 去重/过滤(群@/黑名单) → 交互路由(question/permission优先) → 命令路由 → SessionManager(串行锁) → OpenCode prompt → 回复写回卡片；OpenCode 事件流 → 流式更新/提问/权限/异常 → 飞书卡片 + webhook。

## 六、注意事项

- `.env` 含真实飞书密钥，任何输出/提交都不要泄露
- 不要修改 `plugins/` 下旧项目（保留作参照）
- 修改代码后运行 `node --check` 做语法校验（ESM）
- git 未提交，等用户明确说"提交"再提交

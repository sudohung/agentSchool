# agentBot 安装指南

飞书机器人服务：通过飞书**长连接**接收消息，转发给 opencode 执行，再回复到飞书；同时提供管理页和 MCP 接口。兼容 opencode v1/v2 协议。

---

## 1. 前置条件

- Docker 20.10+、Docker Compose v2
- 一个可用的 opencode 服务（`http://<host>:4096`；v2 需 API 密码）
- 一个飞书**自建应用**，并完成：
  - 启用机器人能力
  - 事件订阅方式选择 **“使用长连接接收事件/回调”**（无需公网 IP）
  - 开通消息相关权限（接收/发送单聊、群聊消息，读取消息内容等）
- 构建镜像需要访问 npm registry

## 2. 创建共享网络

agentBot 要与 opencode 容器互通：

```bash
docker network inspect agent-net >/dev/null 2>&1 || docker network create agent-net
```

## 3. 准备飞书凭证（不入库）

```bash
mkdir -p ~/.config/agentConfig && chmod 700 ~/.config/agentConfig
cat > ~/.config/agentConfig/feishu.env <<'EOF'
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
chmod 600 ~/.config/agentConfig/feishu.env
```

> `docker-compose.yml` 已通过 `env_file` 引用该文件的**绝对路径**。
> 新环境路径不同时，修改 compose 里的 `/root/.config/agentConfig/feishu.env` 为实际路径。

## 4. 配置运行参数

```bash
cd agentBot
cp .env.example .env
```

编辑 `.env`：

```ini
# opencode 服务地址（同网络用容器名；跨主机用 IP/域名）
OPENCODE_BASE_URL=http://opencode-app:4096
# opencode v2 必须；v1 留空
OPENCODE_PASSWORD=<OPENCODE_SERVER_PASSWORD>
OPENCODE_PROVIDER=qwenplatform
OPENCODE_DEFAULT_AGENT=main
```

> `.env` 已被 `.gitignore` 的 `**/.env` 忽略，**不要提交**。

## 5. 配置模型列表 `config/bot.json`

`bot.json` 优先级高于 `.env`，其中的 `opencodeBaseUrl` 会覆盖环境变量。`provider/model` 必须与 opencode 的 `opencode.json` 中定义的 provider 一致：

```json
{
  "opencodeBaseUrl": "http://opencode-app:4096",
  "defaultKey": "main",
  "agents": [
    { "key": "main", "provider": "qwenplatform", "model": "qwen4-max-preview", "description": "默认" },
    { "key": "q2",   "provider": "qwenplatform", "model": "qwen4-max" }
  ],
  "security": { "maskSensitive": false }
}
```

- `defaultKey` 必须是 `agents` 中存在的 key
- 管理页（8082）保存后会热更新并写回此文件（`./config` 已挂载持久化）

## 6. 构建与启动

```bash
cd agentBot
# 若 BuildKit 不可用：export DOCKER_BUILDKIT=0
docker compose up -d --build

# 查看日志
docker logs -f agent-bot
```

端口映射（`docker-compose.yml`）：

| 宿主机 | 容器 | 用途 |
|---|---|---|
| 8082 | 8081 | 配置管理页 / Admin API |
| 8083 | 8083 | MCP 服务（`/mcp`） |

## 7. 验证

日志中应出现：

```
[Gateway] 飞书长连接已就绪
[info]: [ '[ws]', 'ws client ready' ]
[AgentRegistry] 已加载 N 个 Agent（http://opencode-app:4096），默认: main
[McpServer] MCP 服务已启动: http://0.0.0.0:8083/mcp
```

健康检查：

```bash
curl -s http://127.0.0.1:8082/api/config
# 返回当前 opencodeBaseUrl 与 agents 配置
```

然后在飞书里 @机器人 发一条消息，应收到 AI 回复。

## 8. 运行机制与自愈（v2 环境）

- `HealthMonitor` 每 30s 探活 opencode；实例恢复/重启后自动重连事件流
- opencode 重启导致旧会话失效时，飞书链路与 API 链路都会**自动重建会话并重试一次**
- 可调参数（`.env`）：
  - `AGENTBOT_HEALTH_INTERVAL_MS`（默认 30000）
  - `AGENTBOT_HEALTH_FAILURES`（默认 2）

## 9. 常见问题

| 现象 | 排查 |
|---|---|
| 日志只有 `event-dispatch is ready`，无 `ws client ready` | 飞书后台事件订阅未切到“长连接”，或 appId/secret 错误 |
| `[AgentRegistry]` 加载失败 / 连接超时 | `opencodeBaseUrl` 不通；确认两容器都在 `agent-net` |
| 401 / 认证失败 | 未配置 `OPENCODE_PASSWORD` 或值与 `OPENCODE_SERVER_PASSWORD` 不一致 |
| 管理页 404 | 访问的是 8082（宿主机映射），不是 8081 |
| 会话报 `session not found` | 已内置自愈；若仍失败，检查 opencode 是否可用 |
| 群聊无响应 | 检查机器人是否被 @、群聊消息权限是否开通 |

## 10. 升级 / 卸载

```bash
cd agentBot
docker compose up -d --build     # 升级
docker compose down              # 停止（配置与 ./config 保留）
```
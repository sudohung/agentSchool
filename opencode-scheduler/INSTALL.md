# opencode-scheduler 安装指南

opencode 定时任务调度 daemon：支持 cron / 一次性任务，执行 bash 命令或 AI prompt（交给 opencode 执行），结果回传 opencode 会话并可触发飞书 webhook；自带 Web 管理页与 MCP 工具。兼容 opencode v1/v2。

---

## 1. 前置条件

- Docker 20.10+、Docker Compose v2
- 一个可用的 opencode 服务（`opencode serve`，默认 4096；v2 需 API 密码）
- 与 opencode 容器在同一 Docker 网络（本仓库统一用 `agent-net`）

## 2. 目录与关键文件

```
opencode-scheduler/
├── Dockerfile
├── docker-compose.yml     # 已配好网络/资源限制
├── .env                   # 本地密钥（gitignore，不入库）
├── src/                   # 调度引擎 / 执行器 / MCP / HTTP
└── public/               # Web 管理页
```

## 3. 创建网络与本地配置

```bash
docker network inspect agent-net >/dev/null 2>&1 || docker network create agent-net
```

在 `opencode-scheduler/` 下创建 `.env`（**已被 `**/.env` 忽略，勿提交**）：

```ini
# opencode v2 的 API 鉴权密码（对应 opencode 的 OPENCODE_SERVER_PASSWORD）；v1 可留空
OPENCODE_PASSWORD=<opencode-api-password>
```

## 4. 检查 `docker-compose.yml`

默认已按本仓库环境配置，新环境主要确认三处：

```yaml
environment:
  OPENCODE_BASE_URL: http://opencode-app:4096   # 指向你的 opencode 容器/地址
  OPENCODE_PASSWORD: ${OPENCODE_PASSWORD:-}     # 由 .env 注入
  AI_DEFAULT_MODEL: qwenplatform/auto           # 格式 provider/model-id
volumes:
  - /root/workspace/agentSchool:/workspace      # bash 任务工作目录，按需修改
```

已内置的运行时保护：

| 配置 | 值 | 说明 |
|---|---|---|
| `deploy.resources.limits.memory` | 256M | 实测空闲约 40–50MiB，留足任务余量 |
| `deploy.resources.limits.cpus` | 0.5 | |
| `NODE_OPTIONS` | `--max-old-space-size=128` | 限制 V8 堆 |
| `MAX_CONCURRENCY` | 2 | 全局并发上限 |

> 不要同时写 `pids_limit` 和 `deploy.resources.limits.pids`，Compose 会报冲突。

## 5. 构建与启动

```bash
cd opencode-scheduler
# 若 BuildKit 不可用：export DOCKER_BUILDKIT=0
docker compose up -d --build
docker ps --filter name=oc-scheduler
```

## 6. 验证

```bash
# 健康检查：opencode 为 connected 表示已连上
curl -s http://127.0.0.1:8080/api/health
# {"ok":true,"opencode":"connected"}
```

跑一个 bash 任务（不消耗模型）：

```bash
ID=$(curl -s -X POST http://127.0.0.1:8080/api/jobs -H 'Content-Type: application/json' \
  -d '{"name":"smoke","type":"bash","scheduleType":"once","runAt":"2027-01-01T00:00:00+08:00","command":"echo ok && date"}' \
  | node -pe 'JSON.parse(require("fs").readFileSync(0)).id')

curl -s -X POST http://127.0.0.1:8080/api/jobs/$ID/run
```

跑一个 AI 任务（验证 v2 鉴权 + 模型）：

```bash
ID=$(curl -s -X POST http://127.0.0.1:8080/api/jobs -H 'Content-Type: application/json' \
  -d '{"name":"ai-smoke","type":"ai","scheduleType":"once","runAt":"2027-01-01T00:00:00+08:00","prompt":"只回复两个字：在的","model":"qwenplatform/auto","timeoutMs":90000}' \
  | node -pe 'JSON.parse(require("fs").readFileSync(0)).id')

curl -s -m 150 -X POST http://127.0.0.1:8080/api/jobs/$ID/run
# status=success，output="在的"
```

- 管理页：`http://<host>:8080`
- 注意：v1 的 AI 任务通过“轮询 + 静默 8s”判定完成，最少约 8–13s

## 7. 在 opencode 上配置 MCP

编辑 `~/.config/opencode/opencode.json`（与 opencode 共用），新增：

```json
{
  "mcp": {
    "scheduler": {
      "type": "remote",
      "url": "http://172.18.0.1:8080/mcp",
      "enabled": true
    }
  }
}
```

URL 选择（关键）：

| opencode 部署方式 | 推荐 URL |
|---|---|
| 容器，且与 scheduler 同在 `agent-net` | `http://oc-scheduler:8080/mcp` |
| 容器 + 宿主机 CLI 都要用（推荐） | `http://<agent-net 网关>:8080/mcp`（本环境 `172.18.0.1`） |
| opencode 在宿主机运行 | `http://127.0.0.1:8080/mcp` 或宿主 LAN IP |

> 网关 IP 可用 `docker network inspect agent-net --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}'` 获取，重建网络后可能变化。

生效与验证：

```bash
# opencode 容器内（v2）
docker exec opencode-app opencode reload
docker exec opencode-app opencode mcp list
# 期望：✓ scheduler connected

# 宿主机 opencode（v1/v2 客户端）
opencode mcp list
# 期望：✓ scheduler connected
```

可用工具（9 个）：`instance_register`、`instance_list`、`job_add`、`job_list`、`job_get`、`job_pause`、`job_resume`、`job_delete`、`job_run`。

> 设计约束：agent 创建任务前应先 `instance_register` 注册自己的 opencode 实例（baseUrl + sessionId），结果才能回传到原会话。

## 8. 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| `/api/health` 显示 `unreachable` | `OPENCODE_BASE_URL` 不通；确认容器同网络、端口正确 |
| AI 任务报 401 | v2 未配 `OPENCODE_PASSWORD`，或值与 `OPENCODE_SERVER_PASSWORD` 不一致 |
| AI 任务报“无法识别协议” | 地址指向了网页/网关而非 opencode server（v2 SPA 会返回 HTML 200，必须校验 JSON） |
| MCP `connected` 但工具不生效 | 修改配置后执行 `opencode reload`；opencode 启动时 scheduler 未就绪的话需重载 |
| 服务从 v1 升到 v2 后行为异常 | 版本探测缓存 5 分钟，重启 scheduler 或调用 `invalidateVersionCache` |
| bash 任务找不到文件 | 任务在**调度器容器内**执行，路径须落在挂载的 `/workspace` 下 |
| compose 报 `pids_limit` 冲突 | 删除 `pids_limit`，仅保留 `deploy.resources.limits` |

## 9. 数据与升级

- 任务与执行历史：命名卷 `oc-scheduler-data`（SQLite `/data/scheduler.db`）
- 超长输出落盘：`/data/outputs`
- 升级：

```bash
cd opencode-scheduler
docker compose up -d --build   # 复用同名卷，任务不丢
```
# opencode-scheduler

opencode 定时任务调度 daemon：支持 cron 循环与一次性定时任务，支持 bash 命令与 AI prompt（交给源 opencode 执行）两种任务类型，执行结果自动回传 opencode 会话，并可触发飞书 webhook 通知。提供 MCP 工具接口（供 opencode 管理任务）与 Web 管理页面。

## 架构

```
opencode (创建任务) ──MCP──▶ ┌─────────────────────────────┐
                             │  opencode-scheduler (容器)   │
  Web 管理页 :8080  ────────▶│  调度引擎 / 执行器 / 通知器   │
                             │  SQLite: /data/scheduler.db │
                             └──────────┬──────────────────┘
                                        │ HTTP (Server API)
                                 opencode server :4096
                                 （结果回传原会话/新建会话 + 飞书）
```

## 快速开始

```bash
# 构建镜像
docker build -t opencode-scheduler .

# 运行（host 的 opencode server 默认通过 host.docker.internal 访问）
docker run -d --name oc-scheduler \
  -p 8080:8080 \
  -v oc-scheduler-data:/data \
  --add-host=host.docker.internal:host-gateway \
  -e OPENCODE_BASE_URL=http://host.docker.internal:4096 \
  opencode-scheduler
```

- Web 管理页: http://localhost:8080
- MCP 端点: http://localhost:8080/mcp (Streamable HTTP)

在 opencode 中接入（`~/.config/opencode/opencode.json`）：

```json
{
  "mcp": {
    "scheduler": {
      "type": "remote",
      "url": "http://localhost:8080/mcp",
      "enabled": true
    }
  }
}
```

接入后 opencode 可使用 7 个工具：`job_add` / `job_list` / `job_get` / `job_pause` / `job_resume` / `job_delete` / `job_run`。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | 8080 | HTTP 端口（API/UI/MCP 同端口） |
| `DB_PATH` | /data/scheduler.db | SQLite 路径 |
| `OUTPUT_DIR` | /data/outputs | 超长输出落盘目录 |
| `OPENCODE_BASE_URL` | http://127.0.0.1:4096 | opencode Server 地址 |
| `OPENCODE_DIRECTORY` | - | 新建会话时的项目目录（可选） |
| `AI_TIMEOUT_MS` | 600000 | AI 任务默认超时 |
| `BASH_TIMEOUT_MS` | 300000 | bash 任务默认超时 |
| `MAX_CONCURRENCY` | 3 | 全局并发上限 |
| `NOTIFY_MAX_BYTES` | 8192 | 回传消息文本阈值，超出截断并落盘 |
| `DEFAULT_WORKDIR` | /workspace | bash 默认工作目录 |
| `TZ` | Asia/Shanghai | 时区（影响 cron 计算） |

## 任务类型与执行流程

### bash 任务
在容器内执行 shell 命令（如需操作宿主机文件，挂载卷到容器），捕获 stdout/stderr 作为结果。

### ai 任务（内置 agent 执行实例）
1. 优先复用任务绑定的源会话（`sessionId`），会话不存在则通过 `POST /session` 新建；
2. `POST /session/{id}/message` 提交 prompt（可按任务覆盖 `model`，格式 `provider/model-id`）；
3. 订阅 opencode `GET /event` SSE，等待 `session.idle` 判定本轮 agent 执行完成；
4. 拉取会话消息提取最后一轮 assistant 文本作为最终结果；
5. 结果落库 → 通知器回传原会话（会话不存在则新建）→ 按配置触发飞书 webhook。

## 结果通知规则

- **失败 / 超时 / 错过(missed)**：总是通知；
- **成功**：仅当任务开启 `notifyOnSuccess` 时通知；
- 回传内容超长（> 8KB）时截断，完整输出落盘并在消息中附文件路径；
- 同一任务上一轮未结束时跳过本轮（记 `skipped`）；全局并发达上限同样跳过。

## 一次性任务错过补偿

调度器离线/容器重启期间错过执行时间的一次性任务：标记 `completed` + 记录 `missed` 执行 + 发送 missed 通知（不补执行过期任务）。

## REST API（管理页使用）

```
GET    /api/health
GET    /api/jobs
POST   /api/jobs            # 创建任务（字段同 MCP job_add）
GET    /api/jobs/:id
PUT    /api/jobs/:id        # 更新
DELETE /api/jobs/:id
POST   /api/jobs/:id/run    # 手动触发
POST   /api/jobs/:id/pause
POST   /api/jobs/:id/resume
GET    /api/jobs/:id/executions
GET    /api/executions      # 全部执行历史
GET    /api/cron/preview?expr=0 9 * * 1-5   # cron 未来 5 次执行时间预览
```

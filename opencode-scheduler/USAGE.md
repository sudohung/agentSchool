# opencode-scheduler 使用手册

> opencode 定时任务调度系统：让 opencode 在对话中创建、管理定时作业，任务执行结果自动回传 opencode 会话，并可触发飞书等外部通知。

---

## 目录

1. [系统简介与架构](#1-系统简介与架构)
2. [部署](#2-部署)
3. [接入 opencode（MCP）](#3-接入-opencodemcp)
4. [Web 管理页](#4-web-管理页)
5. [创建任务：参数详解](#5-创建任务参数详解)
6. [MCP 工具详解（对话中管理任务）](#6-mcp-工具详解对话中管理任务)
7. [任务执行与结果通知机制](#7-任务执行与结果通知机制)
8. [REST API 参考](#8-rest-api-参考)
9. [环境变量参考](#9-环境变量参考)
10. [典型使用场景示例](#10-典型使用场景示例)
11. [运维与数据管理](#11-运维与数据管理)
12. [常见问题 FAQ](#12-常见问题-faq)

---

## 1. 系统简介与架构

opencode-scheduler 是一个**独立于 opencode 进程常驻运行**的调度 daemon，以 Docker 容器方式部署。opencode 会话关闭/重启不影响已注册任务的执行。

```
┌─────────────────────────────────────────────────────┐
│           opencode-scheduler (Docker 容器)           │
│                                                     │
│  ┌──────────────┐   ┌──────────────┐  ┌──────────┐ │
│  │ 调度引擎      │   │ MCP Server   │  │ Web 管理页│ │
│  │ cron+一次性  │   │ 7 个管理工具  │  │  :8080   │ │
│  └──────┬───────┘   └──────────────┘  └──────────┘ │
│  ┌──────▼──────────────────────────────────────────┐│
│  │  SQLite 存储（任务定义 / 执行历史） /data        ││
│  └─────────────────────────────────────────────────┘│
│  执行器: bash | ai(内置 agent 实例)                  │
│  通知器: opencode 会话回传 | 飞书 webhook            │
└──────────────┬──────────────────────────────────────┘
               │ HTTP（opencode Server API, 默认 :4096）
        ┌──────▼──────┐
        │   opencode  │
        │   server    │
        └─────────────┘
```

**两种任务类型：**

| 类型 | 说明 | 结果来源 |
|---|---|---|
| `bash` | 在容器内执行 shell 命令 | 命令的 stdout + stderr |
| `ai` | 向 opencode 提交 prompt，由 AI agent 执行（内置 agent 执行实例：自动创建/复用会话 → 提交 prompt → 监听 SSE 等待执行完成 → 提取最终回复） | 最后一轮 assistant 文本 |

---

## 2. 部署

### 2.1 前置条件

- 宿主机已安装 Docker（20.10+）
- 有一个可访问的 **opencode Server**（`opencode serve` 启动的 HTTP 服务，默认端口 4096）

> ⚠️ 如果还没有运行 opencode server，先在宿主机执行：
> ```bash
> opencode serve --port 4096   # 监听 127.0.0.1
> # 或监听所有网卡：opencode serve --hostname 0.0.0.0 --port 4096
> ```

### 2.2 构建镜像

```bash
cd /root/workspace/opencode-scheduler
docker build -t opencode-scheduler:1.0.0 .
```

### 2.3 运行容器

```bash
docker run -d \
  --name oc-scheduler \
  --restart unless-stopped \
  -p 8080:8080 \
  -v oc-scheduler-data:/data \
  --add-host=host.docker.internal:host-gateway \
  -e OPENCODE_BASE_URL=http://host.docker.internal:4096 \
  -e TZ=Asia/Shanghai \
  opencode-scheduler:1.0.0
```

关键参数说明：

| 参数 | 作用 |
|---|---|
| `-v oc-scheduler-data:/data` | 持久化数据库与输出文件，容器重建不丢任务 |
| `--add-host=host.docker.internal:host-gateway` | 让容器能访问宿主机上的 opencode server |
| `-e OPENCODE_BASE_URL=...` | 指向宿主机 opencode Server 地址 |

**如果 opencode server 与调度器部署在不同机器**，把 `OPENCODE_BASE_URL` 指向那台机器的地址（要求网络可达）。

### 2.4 使用 docker compose（推荐）

项目自带 `docker-compose.yml`：

```bash
cd /root/workspace/opencode-scheduler
docker compose up -d
```

### 2.5 验证部署

```bash
# 健康检查（opencode 字段为 connected 表示已连上 opencode server）
curl http://localhost:8080/api/health
# 期望: {"ok":true,"opencode":"connected"}
```

浏览器打开 `http://172.22.221.176:8080`（本机可用 `http://localhost:8080`）看到 Web 管理页即部署成功。

---

## 3. 接入 opencode（MCP）

编辑 opencode 配置文件 `~/.config/opencode/opencode.json`，在 `mcp` 段新增：

```json
{
  "mcp": {
    "scheduler": {
      "type": "remote",
      "url": "http://172.22.221.176:8080/mcp",
      "enabled": true
    }
  }
}
```

> 调度器绑定 `0.0.0.0:8080`，本机与其他电脑均可通过 `http://172.22.221.176:8080` 访问（Web 管理页与 MCP 同地址）。不在同一网段的电脑需保证到该 IP 的网络路由可达。

重启 opencode 后，在任意会话中即可让 AI 管理定时任务，例如：

> 「帮我创建一个定时任务，每天早上 9 点检查 /workspace 下所有 git 仓库的未提交变更，结果回传到这个会话」

> 「看一下现在有哪些定时任务」

> 「把『每日巡检』这个任务暂停」

> 「手动跑一次『磁盘检查』任务」

---

## 4. Web 管理页

访问 `http://<宿主机IP>:8080`：

- **任务列表**：名称、类型（bash/ai）、调度表达式、状态（active/paused/completed）、下次执行时间
- **新建任务**：表单填写，cron 表达式实时预览未来 5 次执行时间
- **操作**：执行（手动触发）/ 暂停 / 恢复 / 编辑 / 删除
- **执行历史**：最近 100 条，含状态、耗时、输出摘要、错误信息
- **顶部连接状态**：显示与 opencode server 的连通性

---

## 5. 创建任务：参数详解

### 通用参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `name` | ✓ | 任务名称（唯一标识用途，建议语义化） |
| `type` | ✓ | `bash` 或 `ai` |
| `scheduleType` | ✓ | `cron`（循环）或 `once`（一次性） |
| `sessionId` | 可选 | 源 opencode 会话 ID，结果回传该会话；**不填或会话已失效则自动新建会话** |
| `timeoutMs` | 可选 | 超时毫秒数，bash 默认 300000（5 分钟），ai 默认 600000（10 分钟） |
| `maxRetries` | 可选 | 失败重试次数，默认 1 |
| `feishuWebhook` | 可选 | 飞书机器人 webhook 地址，通知会额外推送到飞书 |
| `notifyOnSuccess` | 可选 | 默认 false；开启后成功也发通知（失败/超时/missed **总是**通知） |

### 调度参数

| scheduleType | 参数 | 格式示例 |
|---|---|---|
| `cron` | `cronExpr` | 5 段标准表达式：`分 时 日 月 周`，如 `0 9 * * 1-5`（工作日每天 9 点） |
| `once` | `runAt` | ISO 时间：`2026-10-01T09:00:00+08:00` |

常用 cron 示例：

| 表达式 | 含义 |
|---|---|
| `*/5 * * * *` | 每 5 分钟 |
| `0 * * * *` | 每小时整点 |
| `0 9 * * 1-5` | 工作日每天 9:00 |
| `30 8 * * *` | 每天 8:30 |
| `0 0 * * 1` | 每周一 0 点 |

### bash 任务参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `command` | ✓ | 要执行的 shell 命令（`/bin/bash` 执行，支持管道等语法） |
| `workdir` | 可选 | 工作目录，默认容器内 `/workspace`。**注意：命令在容器内执行**，需操作宿主机文件请通过挂载卷访问 |

### ai 任务参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `prompt` | ✓ | 提交给 opencode 的提示词，写清楚要做什么、输出什么 |
| `model` | 可选 | 覆盖模型，格式 `provider/model-id`（如 `fuyao/fuyao-coding-low`），不填用 opencode 会话默认模型 |

---

## 6. MCP 工具详解（对话中管理任务）

opencode 接入后可使用 7 个工具：

| 工具 | 功能 | 关键参数 |
|---|---|---|
| `job_add` | 创建任务 | 见第 5 节参数表 |
| `job_list` | 列出全部任务 | 无 |
| `job_get` | 查询单个任务详情 | `id` |
| `job_pause` | 暂停任务（停止调度） | `id` |
| `job_resume` | 恢复暂停的任务 | `id` |
| `job_delete` | 删除任务及执行历史 | `id` |
| `job_run` | 手动立即执行一次（不影响调度计划），返回结果摘要 | `id` |

### 对话示例

**创建每天巡检任务并回传当前会话：**

> 「创建定时任务：名称『每日系统巡检』，bash 类型，每天 9 点执行，命令 `df -h && free -m && uptime`，结果回传这个会话（sessionId 填当前会话 ID），失败时发飞书 https://open.feishu.cn/open-apis/bot/v2/hook/xxx」

**创建 AI 巡检任务：**

> 「创建 ai 类型定时任务：每周一早上 8 点用 prompt『检查 /workspace 下所有项目的 git status，汇总未提交和未推送的变更，输出简报』执行」

**查结果：**

> 「『每日系统巡检』任务上次执行结果是什么」

---

## 7. 任务执行与结果通知机制

### 执行流程

```
定时触发/手动触发
   │
   ├─ 同一任务上轮未结束? ──是──▶ 记录 skipped，跳过本轮
   ├─ 全局并发 ≥ MAX_CONCURRENCY? ─是─▶ 记录 skipped，跳过本轮
   │
   ▼
执行（bash 子进程 / AI agent 实例）
   │
   ▼
结果落库（executions 表）
   │
   ▼
通知：shouldNotify = (status != success) || notifyOnSuccess
   │ 1. 回传 opencode 会话：
   │    - 任务绑定的会话存在 → 发到原会话
   │    - 不存在/未绑定 → POST /session 新建会话发送
   │ 2. 配置了飞书 webhook → 推送飞书
```

### 通知内容格式

```
✅ 定时任务通知 [每日系统巡检]
状态: success | 耗时: 1.2s

--- 执行结果 ---
（命令输出或 AI 回复文本）

完整输出: /data/outputs/xxx.log   （内容超 8KB 截断时附完整文件路径）
```

### 执行状态含义

| 状态 | 含义 |
|---|---|
| `success` | 执行成功 |
| `failed` | 执行失败（命令非 0 退出 / AI 调用出错） |
| `timeout` | 超过 timeoutMs 被终止 |
| `skipped` | 上轮未结束或并发受限，本轮未执行 |
| `missed` | 一次性任务在调度器离线期间错过了预定时间（标记 completed，不补执行，发 missed 通知） |

### AI 任务执行细节

1. 复用绑定会话（`sessionId` 校验存在），否则新建会话（标题为 `定时 AI 任务: <任务名>`）；
2. prompt 会附带任务上下文头部（`[opencode-scheduler 定时任务触发]`）；
3. 提交后订阅 opencode `GET /event` SSE，收到该会话的 `session.idle` 事件判定本轮完成；
4. 拉取会话消息，取最后一轮 assistant 文本作为结果（模型调用出错会透出错误信息）；
5. 等待超时（默认 10 分钟）则中断并记 `timeout`。

---

## 8. REST API 参考

所有接口返回 JSON。管理页与 MCP 均基于此层。

```
GET    /api/health                    # 健康检查：{ok, opencode: connected|unreachable}
GET    /api/jobs                      # 任务列表
POST   /api/jobs                      # 创建任务（字段见第 5 节，camelCase）
GET    /api/jobs/:id                  # 任务详情
PUT    /api/jobs/:id                  # 更新任务（部分字段可省略）
DELETE /api/jobs/:id                  # 删除任务及历史
POST   /api/jobs/:id/run              # 手动触发（同步等待执行完成，返回结果）
POST   /api/jobs/:id/pause            # 暂停
POST   /api/jobs/:id/resume           # 恢复
GET    /api/jobs/:id/executions       # 该任务执行历史（最近 50 条）
GET    /api/executions                # 全部执行历史（最近 100 条）
GET    /api/cron/preview?expr=0 9 * * *   # cron 预览未来 5 次执行时间
```

curl 示例：

```bash
# 创建 bash 任务
curl -X POST http://localhost:8080/api/jobs -H 'content-type: application/json' -d '{
  "name": "磁盘检查",
  "type": "bash",
  "scheduleType": "cron",
  "cronExpr": "0 9 * * *",
  "command": "df -h | awk '\''$5+0 > 80 {print $0}'\''",
  "feishuWebhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
}'

# 手动触发
curl -X POST http://localhost:8080/api/jobs/<id>/run

# cron 预览
curl 'http://localhost:8080/api/cron/preview?expr=0%209%20*%20*%201-5'
```

---

## 9. 环境变量参考

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | `8080` | HTTP 端口（REST/Web/MCP 同端口） |
| `DB_PATH` | `/data/scheduler.db` | SQLite 数据库路径 |
| `OUTPUT_DIR` | `/data/outputs` | 超长输出落盘目录 |
| `OPENCODE_BASE_URL` | `http://127.0.0.1:4096` | opencode Server 地址 |
| `OPENCODE_DIRECTORY` | （空） | 新建会话时指定的项目目录 |
| `AI_DEFAULT_MODEL` | （空） | AI 任务默认模型（`provider/model-id`），任务未指定 model 时使用。**建议配置一个当前用户有权限的模型**，否则使用 opencode 会话默认模型（可能无权限报 403） |
| `AI_TIMEOUT_MS` | `600000` | AI 任务默认超时（10 分钟） |
| `BASH_TIMEOUT_MS` | `300000` | bash 任务默认超时（5 分钟） |
| `MAX_CONCURRENCY` | `3` | 全局同时执行任务数上限 |
| `NOTIFY_MAX_BYTES` | `8192` | 通知文本阈值，超出截断并落盘 |
| `DEFAULT_WORKDIR` | `/workspace` | bash 任务默认工作目录 |
| `TZ` | `Asia/Shanghai` | 时区（影响 cron 计算与显示） |

---

## 10. 典型使用场景示例

### 场景 1：每日代码巡检（AI 任务，结果回传会话）

| 字段 | 值 |
|---|---|
| name | 每日代码巡检 |
| type | ai |
| scheduleType / cronExpr | cron / `0 9 * * 1-5` |
| prompt | 检查 /workspace 下所有 git 仓库的 status 与最近提交，输出不超过 10 行的简报 |
| sessionId | 当前会话 ID（结果回到对话里） |
| notifyOnSuccess | true |

### 场景 2：定时数据备份（bash 任务 + 失告警）

| 字段 | 值 |
|---|---|
| name | 数据库备份 |
| type | bash |
| scheduleType / cronExpr | cron / `30 2 * * *` |
| command | mysqldump ... > /data/backup/db-$(date +%F).sql |
| feishuWebhook | 机器人 webhook（失败时飞书告警） |

### 场景 3：一次性发布后检查（once）

| 字段 | 值 |
|---|---|
| name | 发布后 30 分钟检查 |
| type | bash |
| scheduleType / runAt | once / `2026-10-01T14:30:00+08:00` |
| command | curl -s -o /dev/null -w '%{http_code}' https://xxx/healthz |

### 场景 4：让 opencode 定时自检并向会话汇报（AI 任务）

| 字段 | 值 |
|---|---|
| name | 会话自检 |
| type | ai |
| prompt | 汇总当前工作目录近期改动，若有风险点请详细说明 |
| sessionId | 当前会话 ID |

---

## 11. 运维与数据管理

### 数据备份

所有状态都在 `/data` 卷中：

```bash
# 备份
docker exec oc-scheduler cp /data/scheduler.db /data/scheduler.db.bak
docker run --rm -v oc-scheduler-data:/data -v $PWD:/backup alpine \
  tar czf /backup/scheduler-data.tar.gz -C /data .

# 恢复
docker run --rm -v oc-scheduler-data:/data -v $PWD:/backup alpine \
  sh -c 'cd /data && tar xzf /backup/scheduler-data.tar.gz'
```

### 日志

```bash
docker logs -f oc-scheduler          # 跟踪日志
docker logs oc-scheduler 2>&1 | grep ERROR
```

### 升级

```bash
cd /root/workspace/opencode-scheduler
docker build -t opencode-scheduler:新版本 .
docker rm -f oc-scheduler
# 重新 docker run（复用同名数据卷，任务不丢失）
```

### 停止/清理

```bash
docker stop oc-scheduler       # 停止（任务暂停调度；重启后恢复；错过的一次性任务发 missed 通知）
docker rm oc-scheduler         # 删除容器（数据卷保留）
docker volume rm oc-scheduler-data   # 彻底清除数据（谨慎）
```

---

## 12. 常见问题 FAQ

**Q1：健康检查显示 `opencode: unreachable`？**
检查 `OPENCODE_BASE_URL` 是否正确、opencode server 是否在运行、容器到该地址的网络是否连通（跨机部署需用真实 IP）。会话回传在 unreachable 时会失败，但任务仍会执行并记录历史。

**Q2：结果没有回传到我当前的会话？**
确认创建任务时 `sessionId` 填的是当前会话 ID（可在对话里让 opencode 用当前会话 ID 创建）。未填或会话已删除时，系统会自动新建一个会话来接收通知。

**Q3：bash 任务里访问不到宿主机文件？**
命令在容器内执行。需要宿主机文件时在 `docker run` 时挂载，例如 `-v /root/workspace:/workspace`，任务里用容器内路径访问。

**Q4：AI 任务执行很慢/超时？**
AI 任务耗时取决于模型与任务复杂度。可在创建任务时调大 `timeoutMs`（如 1800000 = 30 分钟），或用 `model` 指定更快的模型。

**Q5：cron 表达式时区不对？**
容器 TZ 默认 `Asia/Shanghai`；如需其他时区，设置环境变量 `TZ` 并重建容器。

**Q6：同一个任务会并发执行吗？**
不会。同一任务上轮未结束时本轮记 `skipped` 跳过；全局并发受 `MAX_CONCURRENCY`（默认 3）限制。

**Q7：一次性任务到了时间但容器没在运行？**
重启后该任务被标记 `completed`、记录一条 `missed` 执行并发送 missed 通知，不会补执行过期的任务。

**Q8：飞书通知没有收到？**
- 检查任务的 `feishuWebhook` 是否正确、机器人是否还在有效期；
- 成功状态默认**不**发通知，需开启 `notifyOnSuccess`；
- 查看执行结果里 `notifyInfo.feishuError` 字段的具体错误。

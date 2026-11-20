# opencode 安装指南（opencodeSpace-java）

本目录提供两套镜像：

| 镜像 | Dockerfile | 用途 |
|---|---|---|
| `opencodespace-opencode:2.3.2` | `Dockerfile.base` | 基础镜像：Node 22 + opencode v2 CLI（`opencode serve`） |
| `opencodespace-opencode-for-java:2.3.2` | `Dockerfile` | 在基础镜像上追加 OpenJDK 8 + Maven 3.9.16（阿里云源） |

> 说明：`native-opencode:2.3.2` = 基础镜像 8 层 + `/static` 等 2 层，属于可选变体；本文以基础镜像/Java 变体为准。

---

## 1. 前置条件

- Docker 20.10+ 与 Docker Compose v2
- 可访问 npm registry（构建时安装 opencode）
- 可访问 `mirrors.aliyun.com`（Java 镜像拉 Maven）
- 一个 opencode 配置目录 `~/.config/opencode/`（含 provider/API Key，**不要提交到仓库**）

## 2. 构建镜像

```bash
cd opencodeSpace-java

# 若提示 BuildKit/buildx 缺失，使用经典构建器
export DOCKER_BUILDKIT=0

# 1) 基础镜像（含 opencode CLI）
docker build -f Dockerfile.base -t opencodespace-opencode:2.3.2 .

# 2) Java 变体（可选，需要 Java/Maven 任务时）
docker build -t opencodespace-opencode-for-java:2.3.2 .

# 验证
docker run --rm --entrypoint opencode opencodespace-opencode:2.3.2 --version
# 期望输出：opencode v2.3.2
```

## 3. 准备 opencode 配置

配置文件放在宿主机 `~/.config/opencode/opencode.json`（**含 API Key，勿入库**）：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "qwenplatform": {
      "npm": "@ai-sdk/anthropic",
      "name": "Qianwen AI Platform",
      "options": {
        "baseURL": "https://<your-endpoint>/anthropic/v1",
        "apiKey": "<your-api-key>"
      },
      "models": {
        "auto": { "name": "Auto" }
      }
    }
  }
}
```

> opencode v2 会自动把 `provider` 迁移为 `providers`（内存态），无需手动改格式。

## 4. 启动 opencode 服务

先创建共享网络（agentBot / scheduler 都会接入）：

```bash
docker network inspect agent-net >/dev/null 2>&1 || docker network create agent-net
```

启动容器（**务必先创建好 `opencode.json`，否则 Docker 会把文件挂载点建成目录**）：

```bash
docker run -d --name opencode-app \
  --network agent-net --network-alias opencode-app \
  -p 4096:4096 \
  -e OPENCODE_SERVER_PASSWORD='<访问密码>' \
  -v /root/.config/opencode/opencode.json:/root/.config/opencode/opencode.json:ro \
  -v /root/.config/opencode/agents:/root/.config/opencode/agents:ro \
  -v /root/.config/opencode/skills:/root/.config/opencode/skills:ro \
  -v /root/workspace/agentSchool:/workspace \
  --restart unless-stopped \
  --memory 768m --cpus 1.0 \
  opencodespace-opencode:2.3.2
```

要点：

- `-e OPENCODE_SERVER_PASSWORD` 是 **API 鉴权密码**（HTTP Basic，用户名固定 `opencode`），agentBot/scheduler 都必须使用它
- 容器内 `/root/.config/opencode/service.json` 里的 password 是 Web 内部密码，**不是** API 密码，别混用
- opencode 空闲内存约 400–450MB，建议 `--memory 768m` 起步

## 5. 验证

v2 的 SPA 会对任意路径返回 HTML 200，**不能只看状态码**，要校验 JSON / 401：

```bash
# 带密码访问 API
curl -s -u "opencode:<访问密码>" http://127.0.0.1:4096/api/info
# 正常返回 {"version":"2.x.x",...}

# 不带密码应返回 401（说明服务在线且鉴权生效）
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4096/api/info
```

## 6. 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| `Unable to find image 'opencodespace-opencode:2.3.2'` | 先按第 2 步构建基础镜像 |
| 配置未生效 | 确认挂载的是文件而非目录；v2 改完 MCP 等配置可执行 `docker exec opencode-app opencode reload` |
| 401 Unauthorized | 密码不对，检查 `OPENCODE_SERVER_PASSWORD`，不要用 `service.json` 里的值 |
| 端口占用 | 改 `-p <宿主端口>:4096`，并同步 agentBot/scheduler 的 `OPENCODE_BASE_URL` |
| 构建很慢/失败 | 设置 `DOCKER_BUILDKIT=0`；确认可访问 npm 与阿里云镜像 |

## 7. 与其它项目的关系

```
opencode-app(:4096)  ◀── agentBot(:8082/:8083)      飞书机器人
                     ◀── oc-scheduler(:8080)       定时任务 / MCP
```

三个容器需在同一 `agent-net` 网络，后两者通过 `http://opencode-app:4096` 访问。
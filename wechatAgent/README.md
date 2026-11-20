# wechatAgent — 微信小程序 × OpenCode AI 助手

原生微信小程序（零构建）+ 独立 Node.js 后端，接入已有 OpenCode 实例做 AI 引擎。
**代码完全独立实现，不复用 agentBot 任何代码**（仅在协议层参考了 OpenCode 的 v1/v2 接口行为）。

```
wechatAgent/
├── project.config.json        微信开发者工具项目配置（含 AppID）
├── miniprogram/               小程序前端（WXML/WXSS/JS，无构建步骤）
│   ├── app.js / app.json / app.wxss
│   ├── config.js              ★ 后端地址配置
│   ├── utils/
│   │   ├── request.js         普通 HTTP 请求（带 token、统一错误）
│   │   ├── stream.js          ★ 流式对话客户端（enableChunked + onChunkReceived）
│   │   ├── auth.js            登录态管理
│   │   └── storage.js         本地存储
│   └── pages/
│       ├── index/             会话列表
│       ├── chat/              对话页（打字机效果）
│       └── settings/          连接状态 / 引擎健康 / 开发说明
├── preview/                   H5 预览页（浏览器里看真实交互与流式，非小程序本体）
└── server/                    独立后端（Node.js ≥ 20，零第三方依赖）
    ├── config.example.json    ★ 配置模板
    ├── config.json            实际配置（复制自模板）
    ├── src/
    │   ├── index.js           启动入口
    │   ├── config.js          配置加载（环境变量可覆盖）
    │   ├── constants.js       枚举与常量
    │   ├── http/              路由、响应、HTTP 服务
    │   ├── auth/              token 签名、微信登录
    │   ├── store/             JSON 持久化（原子写入）
    │   ├── opencode/          OpenCode 客户端、事件总线、事件归一化
    │   ├── chat/              一轮问答的执行器（流式转发）
    │   └── routes/api.js      API 路由定义
    └── test/                  单元测试、端到端测试、流式模拟器
```

## 一、快速开始

### 1. 启动后端

```bash
cd server
cp config.example.json config.json   # 首次
node src/index.js
```

看到下面的日志即成功：

```
[Boot] 服务已启动 http://0.0.0.0:8090
[Boot] 小程序 AppID: wx7da1d84bfa65e857
[Bus] 事件流已连接(default) http://172.22.221.176:4097/event
```

> 远端引擎不可达时，可用本机自己的 OpenCode 实例当引擎，见 [LOCAL_ENGINE.md](LOCAL_ENGINE.md)。

### 2. 打开小程序

微信开发者工具 → 导入项目 → 选择 `wechatAgent` 目录（不是 `miniprogram` 子目录）。

**必须勾选**：详情 → 本地设置 → 「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」。
本项目 `project.config.json` 已设 `urlCheck: false`，但开发者工具仍建议手动确认。

### 3. 改后端地址

编辑 `miniprogram/config.js`：

```js
const ENV = {
    BASE_URL: 'http://127.0.0.1:8090',   // 改成你的后端地址
    ...
};
```

## 二、配置说明

`server/config.json`：

| 字段 | 说明 |
|---|---|
| `port` / `host` | 监听端口，默认 8090（避开已有的 4096-4103/8080/8082/8083） |
| `defaultEngine` | 默认引擎 key |
| `engines` | OpenCode 实例表，每个含 `baseUrl` / `version` / `password` / `directory` |
| `engines.*.version` | `auto`（探测 `/api/info`）/ `v1` / `v2` |
| `engines.*.password` | v2 实例的 `OPENCODE_SERVER_PASSWORD`，v1 留空 |
| `engines.*.directory` | v2 实例的会话工作目录，v1 一般留空 |
| `models` | 模型选择器，`providerID` + `modelID`；`default` 条目配了具体模型则优先使用，未配置时回退引擎默认模型 |
| `wechat.appId` | 小程序 AppID |
| `wechat.appSecret` | 小程序 AppSecret（**不要提交到仓库**） |
| `chat.systemPrompt` | 系统提示词 |
| `chat.turnTimeoutMs` | 单轮生成超时，默认 5 分钟 |
| `chat.heartbeatMs` | 流式心跳间隔，默认 15 秒 |

环境变量优先级高于配置文件：`PORT`、`HOST`、`WECHAT_APP_ID`、`WECHAT_APP_SECRET`、
`OPENCODE_BASE_URL`、`OPENCODE_PASSWORD`、`OPENCODE_VERSION`、`AUTH_SECRET`、`AGENT_DATA_DIR`。

### 登录模式

AppID 已配置为 `wx7da1d84bfa65e857`，AppSecret 已填入 `server/config.json`：

| 条件 | 模式 | 行为 |
|---|---|---|
| 有 `code` | `wechat` | `wx.login` → code → `code2session` → openid |
| 无 `code`（且 `allowDevLogin`） | `dev` | 用小程序端生成的 `deviceId` 派生稳定 openid |
| 无 `code`（且未开 `allowDevLogin`） | — | 返回 400，提示缺少 code |

`allowDevLogin` 是本地调试兜底：开发者工具里可能拿不到有效 code，开启后可继续调试。
**生产环境务必设为 `false`**（或删掉该字段），否则任何人都能伪造 `deviceId` 登录。

现有配置：

```json
"wechat": {
  "appId": "wx7da1d84bfa65e857",
  "appSecret": "…",
  "allowDevLogin": true
}
```

> 已实测：真实 code 链路会把微信的错误原样透传（例如 `40029 invalid code`），
> 说明 AppID/AppSecret 是有效的。正式发布前请把 `allowDevLogin` 关掉，
> 并把 AppSecret 改成环境变量 `WECHAT_APP_SECRET` 注入，不要留在仓库里。

## 三、流式实现要点

小程序端 `utils/stream.js` 是核心：

```js
const task = wx.request({
    url: '.../messages',
    method: 'POST',
    enableChunked: true,        // 必须显式开启
    responseType: 'arraybuffer',
    success: ..., fail: ...,
});

// 必须在 request 返回后立刻挂载，不能等 success
task.onChunkReceived((res) => {
    buffer += decoder.push(res.data);
    // 按 \n 切 NDJSON 帧
});
```

四个容易踩的坑，代码里都处理了：

1. **不能等 `success` 挂载** `onChunkReceived` —— 那时流已经结束。
2. **`onChunkReceived` 没有「结束」事件** —— 靠协议里自带的 `done` 帧判定。
3. **chunk 会切碎多字节字符** —— `utils/stream.js` 用带状态的增量 UTF-8 解码器，
   在 1/2/3 字节切分点上都验证过中文、emoji 不乱码。
4. **高频 `setData` 会卡** —— 对话页用 60ms 节流批量刷新，且只 setData 单条消息路径。

服务端约定 **NDJSON**（一行一帧），并显式设置 `X-Accel-Buffering: no` 防止 Nginx 缓冲：

| 帧 | 含义 |
|---|---|
| `{"t":"start","sessionId","messageId","engine"}` | 开始 |
| `{"t":"delta","text"}` | 正文增量 |
| `{"t":"reasoning","text"}` | 思考过程增量 |
| `{"t":"tool","tool","status","title"}` | 工具调用状态 |
| `{"t":"question","id","questions"}` | 引擎反向提问（表单） |
| `{"t":"permission","id","action"}` | 权限申请 |
| `{"t":"ping","ts"}` | 心跳 |
| `{"t":"done","status":"done\|aborted\|error\|timeout","error?"}` | 终态 |

## 四、API

除 `GET /api/health`、`POST /api/auth/login` 外，全部要求 `Authorization: Bearer <token>`。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 服务与引擎健康 |
| POST | `/api/auth/login` | 登录（`code` + `deviceId`） |
| GET | `/api/bootstrap` | 用户、引擎列表、模型列表 |
| GET | `/api/sessions` | 会话列表 |
| POST | `/api/sessions` | 新建会话（`engine` / `title`） |
| GET | `/api/sessions/:id` | 会话详情 |
| PATCH | `/api/sessions/:id` | 重命名 |
| DELETE | `/api/sessions/:id` | 删除（同时中断生成） |
| GET | `/api/sessions/:id/messages` | 历史消息 |
| POST | `/api/sessions/:id/messages` | **流式提问（NDJSON）** |
| POST | `/api/sessions/:id/stop` | 停止生成 |
| POST | `/api/sessions/:id/form` | 回复引擎表单提问 |
| POST | `/api/sessions/:id/permission` | 回复权限申请（`once`/`always`/`reject`） |

所有 `/api/sessions/:id` 接口都会校验会话归属，越权返回 403。

## 五、测试

```bash
cd server

# 单元测试（16 个用例：token、路由、存储、事件归一化）
node --test test/unit.test.js

# 端到端测试（需要后端已启动 + OpenCode 可访问，16 个用例）
node --test test/e2e.test.js

# 流式联调模拟器（用 fetch 模拟 enableChunked，含随机 1-8 字节切块）
node test/stream-simulator.cjs

# 小程序静态检查（页面四件套、事件绑定、data 字段、滚动 id、require 路径、CSS 变量）
node test/miniprogram-check.cjs
```

`stream-simulator.cjs` 会故意把响应切成 1~8 字节的小块，
用来验证「中文被 chunk 边界切开」时前端解码是否仍然正确。

`miniprogram-check.cjs` 用于替代本机缺少微信开发者工具的场景，
能发现「WXML 绑定了 JS 里不存在的方法」「滚动目标 id 写错」这类只在打开工具时才报的问题。

### 浏览器预览（无需开发者工具）

本机没有微信开发者工具时，可用 `preview/` 下的 H5 预览页查看真实交互与流式效果：

```bash
# 页面：preview/index.html（单文件，零依赖）
# 站点：已由 nginx 提供，监听 8091，/wechat-api/ 反代到 8090（关缓冲保流式）
open http://172.22.221.176:8091/
```

它是浏览器版的小程序界面，接的是**同一套后端**，用于验证交互与流式，**不是小程序本体**。
上传体验版的完整步骤见 [PREVIEW.md](PREVIEW.md)。

## 六、正式上线前必须处理

小程序**真机和正式版**有硬限制，开发者工具里能跑通不代表线上能用：

| 限制 | 说明 | 解决 |
|---|---|---|
| 域名 | 不能是 IP 或 localhost | 备案域名 + 指向后端的 DNS |
| 协议 | 必须 HTTPS | 配 SSL 证书（Nginx/Caddy 反代） |
| 端口 | 不能带端口号（443 除外） | 反向代理把 443 转到 8090 |
| 备案 | 域名需 ICP 备案 | 走云厂商备案，约 5-20 工作日 |
| 后台配置 | 需在小程序后台登记 | 开发管理 → 开发设置 → 服务器域名 → request 合法域名 |

Nginx 反代示例（**必须关缓冲**，否则打字机会一次性吐出）：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8090;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;          # 关键
    proxy_cache off;              # 关键
    chunked_transfer_encoding on;
    proxy_read_timeout 600s;
}
```

## 七、数据与安全

- 数据落在 `server/data/chat-store.json`（原子写入，损坏时自动备份为 `.broken-<时间戳>`）。
- 登录 token 是 HMAC-SHA256 签名的自包含 token，密钥首次启动生成到 `server/data/auth-secret.txt`。
- `data/` 与 `config.json` 含敏感信息，已在 `.gitignore` 中忽略。
- 每个用户只能访问自己的会话；引擎密码只存在后端，不下发到前端。
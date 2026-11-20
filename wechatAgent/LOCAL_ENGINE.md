# 本地引擎接入说明

用**本机自己的 OpenCode 实例**当 wechatAgent 的 AI 引擎，不依赖远端实例，也不需要公网隧道。
适合：远端引擎（`config.example.json` 里的 `172.22.221.176:4097/4102`）在当前网络不可达，或想完全本地开发调试的场景。

> 本文是 [README.md](README.md) 的补充篇。整体架构、API、流式协议先看主 README。

## 一、前提

| 项 | 要求 |
|---|---|
| Node.js | ≥ 20（后端零第三方依赖） |
| OpenCode | 本机有一个 v2 实例在监听 HTTP（你正在用的 `opencode serve` 就算） |
| 密码 | 该实例的 `OPENCODE_SERVER_PASSWORD`（v2 用 Basic 鉴权，用户名固定 `opencode`） |

先确认引擎可用：

```bash
curl -u "opencode:$OPENCODE_SERVER_PASSWORD" http://127.0.0.1:4096/api/info
# 返回 {"version":"2.3.2",...} 即可用；version 以 2 开头走 v2 协议
```

## 二、生成 config.json

`config.json` 已被 gitignore，每台机器自行生成。最小可用示例：

```json
{
  "port": 8090,
  "host": "0.0.0.0",
  "defaultEngine": "default",
  "engines": {
    "default": {
      "label": "本机 OpenCode v2",
      "baseUrl": "http://127.0.0.1:4096",
      "version": "v2",
      "password": "这里填 OPENCODE_SERVER_PASSWORD 的值",
      "directory": "/workspace"
    }
  },
  "models": [
    { "key": "default", "label": "Qwen4 Max Preview", "providerID": "qwenplatform", "modelID": "qwen4-max-preview" }
  ],
  "wechat": { "appId": "", "appSecret": "", "allowDevLogin": true },
  "chat": {
    "systemPrompt": "你是微信小程序里的 AI 助手，回答要简洁、条理清晰，优先给出可执行的结论。",
    "turnTimeoutMs": 300000,
    "heartbeatMs": 15000
  }
}
```

要点：

- `directory`：v2 会话的工作目录，填本机真实存在的目录（如 `/workspace`）
- `allowDevLogin: true`：本机没有微信 code，用 deviceId 开发登录。**生产必须 false**
- 密码也可以不落盘：启动时用环境变量 `OPENCODE_PASSWORD` 注入（优先级高于文件，仅作用于默认引擎）
- 本地引擎与远端引擎可共存：`engines` 里加多个条目即可，设置页会分别显示健康状态

## 三、必须给 default 模型条目配一个可用模型（踩坑记录）

**现象**：链路全通，但一提问就收到终态错误帧：

```
Free usage limit reached. Connect a provider or subscribe to OpenCode Go to keep going, or switch models.
```

**原因**：

1. 引擎不指定模型时用它的默认模型（通常是 opencode 免费模型），免费额度耗尽即报此错
2. 小程序端从不发 `modelKey`，会话永远落在 `default` 条目上

**解决**：在 `models` 的 `default` 条目里配置具体的 `providerID` + `modelID`（见上面示例）。
`resolveModel` 会优先使用 `default` 条目配置的具体模型；未配置时仍回退引擎默认模型（向后兼容）。

查本机引擎有哪些模型：

```bash
curl -s -u "opencode:$OPENCODE_SERVER_PASSWORD" http://127.0.0.1:4096/api/model
# data[] 里每项的 providerID / modelID 即可填入配置
```

## 四、启动与验证

```bash
cd wechatAgent/server
node src/index.js
```

看到这两行即引擎接通：

```
[Boot] 服务已启动 http://0.0.0.0:8090
[Bus] 事件流已连接(default) http://127.0.0.1:4096/api/event
```

三步验证：

```bash
# 1. 健康检查：engines[0].ok === true
curl http://127.0.0.1:8090/api/health

# 2. 单元测试（不需要引擎）
node --test test/unit.test.js

# 3. 端到端测试（默认连 http://127.0.0.1:8090，含真实流式问答）
node --test test/e2e.test.js
```

e2e 全绿即代表：登录 → 建会话 → 流式提问（`start/reasoning/delta/done` 帧）→ 停止/删除 全链路在本机引擎上可用。

## 五、让小程序连本地后端

编辑 `miniprogram/config.js`：

```js
BASE_URL: 'http://127.0.0.1:8090',
```

微信开发者工具导入 `wechatAgent` 目录，勾选「不校验合法域名…」（`project.config.json` 已设 `urlCheck: false`）。
游客模式拿不到有效 code 时，`allowDevLogin: true` 会自动降级为开发登录，不影响调试。

> 真机预览/体验版仍需 HTTPS 备案域名或临时隧道，见 [PREVIEW.md](PREVIEW.md)。本地引擎只解决「引擎在哪」，不解决「手机怎么连」。

## 六、注意

- 引擎就是你自己的 OpenCode 实例：wechatAgent 创建的会话会真实出现在该实例里（工作目录由 `directory` 决定），调试完可在小程序里删除会话
- `config.json`、`data/` 均含敏感信息且已 gitignore，**不要提交**
- 引擎重启后事件流会自动重连；若协议版本变化，重启后端即可

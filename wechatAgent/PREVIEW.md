# 预览与体验版：怎么让别人看到效果

三种看到效果的方式，按「真实程度」从低到高：

| 方式 | 真实程度 | 门槛 |
|---|---|---|
| H5 预览页（浏览器） | 交互与流式一致，非小程序本体 | 无，已就绪 |
| **微信开发者工具模拟器** | **真实小程序运行时**，WXML/WXSS/JS 真跑 | 无，已在本机装好 |
| 体验版（微信扫码） | 真机 | 上传私钥 + 公网 HTTPS 域名 |

---

## 路径零：微信开发者工具模拟器（真实小程序）

本机已安装 Linux 移植版微信开发者工具（`msojocs/wechat-web-devtools-linux`，v2.02.2609250），
用 Xvfb 无头运行，可直接跑真实小程序代码。

### 已装内容

| 项 | 位置 |
|---|---|
| 开发者工具 | `/opt/wechat-devtools`（bin 下有 `wechat-devtools`、`wechat-devtools-cli`） |
| 虚拟显示 | `Xvfb :99`（1600×1000×24） |
| 启动脚本 | `/tmp/opencode/wx/start.sh` |
| 截图脚本 | `/tmp/opencode/wx/shot.sh` |
| 安装脚本 | `/tmp/opencode/wx/install.sh` |

### 启动

```bash
# 1. 确保虚拟屏在跑（脚本会自动起）
Xvfb :99 -screen 0 1600x1000x24 &

# 2. 启动工具（约 20~30 秒起来），同时开 CDP 端口方便自动化
cd /opt/wechat-devtools
DISPLAY=:99 nohup ./bin/wechat-devtools --no-sandbox --disable-gpu \
    --remote-debugging-port=9222 > /tmp/opencode/wx/logs/ide.log 2>&1 &

# 3. 截图看界面
DISPLAY=:99 import -window root /tmp/opencode/wx/shot.png
```

### 已跑通的验证结果

游客模式（`touristappid`）导入 `wechatAgent` 项目后：

| 页面 | 结果 |
|---|---|
| 首页 | 会话列表渲染正常，可新建对话 |
| 对话页 | 发问 → 三点等待动画 → 思考过程折叠块 → **正文逐段流式追加** → 收尾 |
| 设置页 | 后端「已连接」、登录模式、用户 ID、两个引擎均「在线」 |

截图见 `docs/screenshots/`：

- `01-index.png` 首页
- `02-chat-streaming.png` 流式生成中（打字机）
- `04-chat-done.png` 生成完成
- `03-settings.png` 设置页

### 两个已知坑（已处理）

1. **游客模式的 `wx.login` 返回无效 code**
   `code2session` 会回 `invalid code`。后端 `allowDevLogin: true` 时会自动降级为开发登录，
   所以即使 `config.json` 配了真实 AppID，模拟器里也能正常进。
   生产环境把 `allowDevLogin` 设为 `false` 即可，降级路径不再生效。

2. **IDE 内置 Git 面板反复弹「没有找到 Git 仓库」**
   因为 `wechatAgent` 是 `agentSchool` 仓库的子目录。处理方式是让它建完 `.git` 后删掉，
   或者点「稍后运行」。**不要**在子目录里保留 `.git`，否则会变成嵌套仓库。

---

## 路径一：H5 预览（已就绪，浏览器直接看）

> 只用于看交互与流式效果，**不是小程序本体**，不能扫码在微信里打开。

### 访问地址

| 场景 | 地址 |
|---|---|
| 同一局域网 / 本机浏览器 | `http://172.22.221.176:8091/` |
| 本机 | `http://127.0.0.1:8091/` |

手机连同一个 WiFi 也能直接打开（H5 本身不校验域名，只有小程序才需要 HTTPS 备案域名）。

### 它做了什么

- 复用与小程序**完全同一套后端**（8090），同一个 OpenCode 引擎、同一条流式链路
- 用浏览器 `fetch` + `ReadableStream` 读 NDJSON，效果等同于小程序 `enableChunked` + `onChunkReceived`
- 页面结构、配色、文案、交互（新建/长按删除/停止生成/表单选择/权限确认）都按小程序页面 1:1 还原
- 后端地址自动跟随访问 host，所以换机器访问不用改代码

### 关键文件

| 文件 | 作用 |
|---|---|
| `agentSchool/wechatAgent/preview/index.html` | 整个预览页（单文件，无构建、无依赖） |
| `/etc/nginx/sites-available/wechat-preview` | 8091 静态站点 + `/wechat-api/` 反代到 8090（关缓冲，保流式） |

nginx 反代的核心三行（缺一个打字机就会退化成一次性输出）：

```nginx
proxy_buffering off;
proxy_cache off;
chunked_transfer_encoding on;
```

### 已验证

用 Playwright 真机尺寸（390×760）跑通：首页渲染 → 新建会话 → 发问 → 流式逐字出现 → 完整收尾 → 停止生成 → 长按删除 → 设置页引擎在线。控制台零报错。

---

## 路径二：真·小程序体验版（需要你提供一样东西）

体验版的唯一硬门槛是**小程序后台的代码上传私钥**。

### 你需要做的（约 3 分钟）

1. 打开 [微信公众平台](https://mp.weixin.qq.com) → 用 AppID `wx7da1d84bfa65e857` 对应的账号登录
2. 左侧菜单：**开发** → **开发管理** → **开发设置**
3. 找到「小程序代码上传」→ 点 **生成** → 下载私钥文件（文件名形如 `private.wx7da1d84bfa65e857.key`）
4. 把文件放到服务器：`/root/workspace/agentHarness/agentSchool/wechatAgent/server/../.keys/private.wx7da1d84bfa65e857.key`
   （目录我来建，你只要把文件放进去，或把内容贴给我）
5. 同一页面下方「IP 白名单」：把本机出口 IP `98.98.112.194` 加进去（不上白名单会报 `invalid ip`）

### 我拿到私钥后会执行

```bash
npx miniprogram-ci upload \
  --pp ./wechatAgent \
  --pkp ./.keys/private.wx7da1d84bfa65e857.key \
  --appid wx7da1d84bfa65e857 \
  --uv 0.1.0 \
  --ud "初版：会话列表 / 流式对话 / 设置"
```

上传成功后你在后台 **版本管理** 里会看到「开发版本」，点「选为体验版」生成体验二维码，扫码即可在微信里试用。

### 上传前必须改的两处

| 项 | 现状 | 必须改成 |
|---|---|---|
| `miniprogram/config.js` 的 `BASE_URL` | `http://127.0.0.1:8090` | 真机访问不到的地址，体验版也是白屏。需要公网可达的 HTTPS 域名 |
| `server/config.json` 的 `allowDevLogin` | `true` | `false`，否则任何人都能伪造 deviceId 登录 |

> 体验版虽然不校验域名白名单，但**必须是 HTTPS 且公网可达**，用 IP + 明文 HTTP 在真机上会被拦。
> 所以要走体验版，前提是先有一个能公网访问的 HTTPS 域名指向 8090。

---

## 一句话总结

- 想**现在就看到效果**：打开 `http://172.22.221.176:8091/`，手机连同一 WiFi 也行
- 想**看真实小程序**：本机已装微信开发者工具，按上面的命令启动即可（游客模式够用）
- 想**在微信里扫码试用**：给我上传私钥 + 一个公网 HTTPS 域名，我这边一条命令就能推体验版
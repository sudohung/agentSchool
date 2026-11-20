# 预览与体验版：怎么让别人看到效果

三种看到效果的方式，按「真实程度」从低到高：

| 方式 | 真实程度 | 门槛 |
|---|---|---|
| H5 预览页（浏览器） | 交互与流式一致，非小程序本体 | 无，已就绪 |
| **微信开发者工具模拟器** | **真实小程序运行时**，WXML/WXSS/JS 真跑 | 无，已在本机装好 |
| 扫码预览（`preview.cjs`） | 真机 | 二维码已生成；手机需开「调试模式」 |
| 体验版（后台选版本 v0.1.1） | 真机、可分享给他人 | 已上传；同样受域名校验限制 |

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

## 路径二：真·小程序（扫码在微信里打开）

已打通：上传私钥就位、IP 白名单生效、公网 HTTPS 隧道可达、流式未被打断。

### 上传工具链

工具链放在 `deploy/` 独立目录，**不进 `server/`**，后端保持零依赖。

```bash
cd wechatAgent/deploy
npm install          # 首次：装 miniprogram-ci
node preview.cjs     # 生成预览二维码 → deploy/out/qrcode.png
node upload.cjs 0.1.0 "版本描述"   # 上传开发版本 → 后台「选为体验版」
```

| 文件 | 作用 |
|---|---|
| `deploy/upload.cjs` | 上传「开发版本」，之后在后台版本管理里选为体验版 |
| `deploy/preview.cjs` | 直接生成扫码即开的预览二维码（面向开发者/体验成员） |
| `.keys/private.<appid>.key` | 后台上传私钥，**已被 gitignore** |
| `deploy/node_modules/`、`deploy/out/` | 依赖与产物，均不入库 |

两个脚本都设了 `setting.urlCheck: false`，否则临时隧道域名会被域名校验拦下。

> ⚠️ `urlCheck: false` 只作用于**上传编译期**，不代表真机运行时也不校验。
> 真机打开时微信仍会校验 request 合法域名，见下面「真机域名校验」一节。

### 真机域名校验（决定扫码能不能用）

微信官方规则：`不校验合法域名` 只在**开发者工具**和**手机开启调试模式**时生效。
真机扫码打开预览/体验版时：

| 条件 | 结果 |
|---|---|
| 手机已开「调试模式」 | 跳过域名校验，能连隧道，**可直接试用** |
| 手机没开调试模式 | 校验 request 合法域名 → 隧道域名不在白名单 → `url not in domain list` |

而 `*.trycloudflare.com` 不是已备案域名，**无法加入后台的 request 合法域名列表**。
所以当前这套临时隧道方案，只适合「开发者/体验成员 + 手机开调试」的试用场景，
做不到「把二维码发给任何人、扫码即用」。

打开调试模式的方式：扫二维码进入小程序后，点右上角 `···` → `开发调试` → 开启调试，
小程序会重启并跳过域名校验。

要走「任何人扫码即用」，必须先解决**已备案域名**这一条，替换 `BASE_URL` 后重新 `preview` / `upload`。

### 公网 HTTPS 通道（cloudflared 临时隧道）

真机要求 HTTPS 且公网可达，本机 8090/8888 公网不可达，故用免注册隧道：

```bash
cd /tmp/opencode
./cloudflared tunnel --url http://127.0.0.1:8090 --no-autoupdate > /tmp/opencode/cf.log 2>&1 &
grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/opencode/cf.log | head -1
```

拿到域名后写进 `miniprogram/config.js` 的 `BASE_URL`，再 `preview` / `upload`。

已验证隧道上：
- `/api/health` 返回 200，两个引擎在线
- 登录可用
- **流式逐帧到达、无缓冲**（`reasoning` 帧连续小段推送，说明打字机不会被退化成一次性输出）

> ⚠️ 临时隧道的域名在进程重启后会变。届时更新 `BASE_URL` 并重新 `preview` / `upload` 即可。
> 正式上线应换成自有已备案域名，不再依赖隧道。

### 上线前必须收紧的两处

| 项 | 现状 | 正式环境应改为 |
|---|---|---|
| `server/config.json` 的 `allowDevLogin` | `true`（游客模式降级用） | `false`，否则任何人可伪造 deviceId 登录 |
| `server/config.json` 的 AppSecret | 明文写在本地配置文件 | 走环境变量 `WECHAT_APP_SECRET`（该文件已 gitignore） |

---

## 一句话总结

- 想**现在就看到效果**：打开 `http://172.22.221.176:8091/`，手机连同一 WiFi 也行（无任何限制）
- 想**看真实小程序**：本机已装微信开发者工具，按上面的命令启动即可（游客模式够用）
- 想**在微信里扫码试用**：`cd deploy && node preview.cjs` 生成 `deploy/out/qrcode.png`，
  扫码后**需在右上角 `···` → 开发调试 → 开启调试**才能连上临时隧道
- 想**发给别人扫码即用**：卡在「已备案域名」这一条，需要先有备案域名替换 `BASE_URL`
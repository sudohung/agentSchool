---
name: 生成图片并发送到飞书
description: 用 Token Plan 文生图 API 生成图片（可选 4 宫格漫画/多轮对话），上传到飞书并发送给指定用户或群。当用户说"生成图片/画一张…然后发飞书/发我"时使用。
metadata:
  opencode/autoinvoke: true
---

# 生成图片并发送到飞书

把"文生图 → 下载校验 → 飞书上传 → 飞书发送"串成一次可复现的流程。
优先用 `scripts/generate-and-send.sh`，它已处理引号、换行、token 不回显等问题。

## 前置条件

| 用途 | 位置 / 变量 |
| --- | --- |
| 图像生成鉴权 | `/workspace/.env` 里的 `ANTHROPIC_AUTH_TOKEN` |
| 飞书应用鉴权 | `/root/.config/agentConfig/feishu.env` 里的 `FEISHU_APP_ID`、`FEISHU_APP_SECRET` |

两个文件都**只读**，不要写入；任何输出里都不要回显 token / secret。

## 快速用法

```bash
# 生成并发送给默认接收人（应用所属用户）
/workspace/.opencode/skills/feishu-image-send/scripts/generate-and-send.sh \
  --prompt "两只海鸥在海边礁石上探讨人生，黄昏暖光，写实摄影" \
  --size "1024*1024" \
  --out /workspace/seagulls.png

# 发送到某个群
... --to oc_xxxxxxxx --to-type chat_id

# 只生成不发
... --no-send

# 复用已有图片，只做飞书发送（不调用生成接口）
... --image /workspace/seagulls.png --no-generate

# 只确认已有图片路径、不发消息
... --image /workspace/seagulls.png --no-generate --no-send
```

脚本成功时会输出：图片绝对路径、实际参数、飞书 `message_id`。

## 参数（写图片描述时的要点）

- `--size`：默认 `1024*1024`；16:9 → `1664*928`，9:16 → `928*1664`，4:3 → `1472*1104`，3:4 → `1104*1472`。
- `--n`：张数，逐张下载，文件名自动加 `_1`、`_2`。
- `--seed` / `--negative`：可复现、排除内容时才传，未传则不出现在请求体。
- `--model`：默认 `qwen-image-3.0-pro`。
- 默认 `prompt_extend=false`、`watermark=false`：保持用户原意，不擅自扩写主题。

## 4 宫格 / 多轮对话漫画

一次生成比二次拼接更可靠，prompt 里要写清这些结构要素：

1. 版式：`四格漫画，2x2 网格布局，白色粗边框分隔，同一场景同一角色连贯叙事`；
2. 每格台词：**逐字写出**中文对白，并要求"对话气泡内是清晰可读的中文文字"；
3. 角色一致性：把两个角色的形象和立场各描述一遍（如"左边海鸥昂首望远方/右边海鸥低头盯薯条"），每格沿用。

模型对长中文台词偶有错字，生成后**必须读图核对**；发现错字就只重述该格台词重生成，不要靠加字补救。

## 校验（不可跳过）

1. 文件非空且是 PNG/JPEG：脚本已检查魔数（`\x89PNG` / `\xFF\xD8\xFF`）。
2. **用读图工具肉眼看一遍**：主体是否符合描述、文字是否可读、4 宫格是否真的 4 格。
3. 飞书返回 `code: 0` 才算发送成功；非 0 时把 `code` / `msg` 原样报给用户，不谎报成功。

## 失败处理

| 现象 | 处理 |
| --- | --- |
| 生成接口报某可选参数不支持 | 去掉该参数（seed / negative_prompt / watermark / n）重试 **1 次**，并说明已忽略 |
| 飞书 `code` 非 0（权限/可用范围） | 原样报错，提示检查应用的机器人权限与可用范围 |
| 上传返回 400 且提示图片格式 | 确认文件是 PNG/JPEG 且 < 10 MB |
| 不知道发给谁 | 用 `--to` 指定 open_id 或 chat_id；群列表见 `references/feishu-api.md` |

## 细节与坑

接口字段、上传/发送的请求体形状、群列表查询方式，见 `references/feishu-api.md`。

本机环境只有 busybox `sh`（没有 bash），脚本按 POSIX sh 编写；`content` 字段必须字符串化，环境变量只从上面两个只读文件读取。
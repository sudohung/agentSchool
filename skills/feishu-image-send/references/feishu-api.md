# Token Plan 文生图 + 飞书发送接口备忘

以下都是本机实测可用的形状，改参数时保持字段名不变。

## 1. 文生图

`POST https://token-plan.maas.qianwenaiapi.com/api/v1/services/aigc/multimodal-generation/generation`

请求头：`Authorization: Bearer $ANTHROPIC_AUTH_TOKEN`、`Content-Type: application/json`

```json
{
  "model": "qwen-image-3.0-pro",
  "input": {
    "messages": [
      { "role": "user", "content": [ { "text": "<prompt>" } ] }
    ]
  },
  "parameters": {
    "size": "1024*1024",
    "n": 1,
    "prompt_extend": false,
    "watermark": false
  }
}
```

- 可选项 `seed`（整数）、`negative_prompt`（字符串）：**未指定就不要出现在 JSON 里**。
- 参考图 / 图生图：`content` 数组里先放 `{"image": "<可访问 URL>"}`，再放 `{"text": "<编辑指令>"}`。本地文件必须能通过 `/static` 之类的静态服务访问，不要臆造 URL。
- 取图：`output.choices[*].message.content[*].image`（返回的是带签名的临时 URL，尽快下载）。
- 返回里 `usage.output_width/height` 可用于核对尺寸。

## 2. 飞书 tenant_access_token

`POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`

```json
{ "app_id": "<FEISHU_APP_ID>", "app_secret": "<FEISHU_APP_SECRET>" }
```

取 `tenant_access_token`，有效期约 2 小时（`expire` 秒）。缓存在临时文件即可，**不要写进工作区或日志**。

## 3. 上传图片

`POST https://open.feishu.cn/open-apis/im/v1/images`（`multipart/form-data`）

| 字段 | 值 |
| --- | --- |
| `image_type` | `message` |
| `image` | `@<本地图片路径>` |

成功：`code: 0`，`data.image_key`（形如 `img_v3_0217k_...`）。

## 4. 发送图片消息

`POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=<open_id|chat_id|email|union_id>`

```json
{
  "receive_id": "ou_xxx 或 oc_xxx",
  "msg_type": "image",
  "content": "{\"image_key\":\"img_v3_...\"}"
}
```

注意 `content` 是**字符串化的 JSON**，不是嵌套对象——这是最常见的踩坑点。

成功：`code: 0`，返回 `data.message_id`（`om_...`）和 `data.chat_id`（`oc_...`）。
发单人时 `receive_id_type=open_id`，返回的 `chat_id` 就是与该用户的单聊会话，可复用。

## 5. 查群列表（找 chat_id）

`GET https://open.feishu.cn/open-apis/im/v1/chats?page_size=50`，头带 `Authorization: Bearer <token>`。

`data.items[]` 里取 `chat_id`、`name`、`chat_mode`、`owner_id`。
注意用途：只有机器人已加入的群才会出现在这里。

## 6. 发送文本（可选）

同第 4 节，改 `"msg_type": "text"`，`content` 为 `"{\"text\":\"...\"}"`。

## 7. 常见错误

| code | 含义 | 处理 |
| --- | --- | --- |
| 99991663 / 99991661 | token 无效或过期 | 重新取 token |
| 230001 / 230002 | 接收人不存在 / 机器人不在会话 | 核对 open_id，或把机器人拉进群 |
| 234001 | 图片上传参数错误 | 检查 `image_type` 与文件格式 |
| 230020 | 触发频率限制 | 退避后重试 |
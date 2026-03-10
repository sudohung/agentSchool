# OpenCode API 速查表

## 快速参考

### 服务器信息
- 默认地址: `http://127.0.0.1:4096`
- OpenAPI 文档: `http://127.0.0.1:4096/doc`
- 健康检查: `GET /global/health`

---

## 核心 API

### Session (会话)

```
GET    /session                      # 列出会话
POST   /session                      # 创建会话
GET    /session/status               # 会话状态
GET    /session/{id}                 # 获取会话
DELETE /session/{id}                 # 删除会话
PATCH  /session/{id}                 # 更新会话
POST   /session/{id}/abort           # 中止会话
POST   /session/{id}/fork            # 分叉会话
POST   /session/{id}/share           # 分享会话
DELETE /session/{id}/share           # 取消分享
GET    /session/{id}/children        # 子会话
GET    /session/{id}/todo            # 待办列表
GET    /session/{id}/diff            # 差异
POST   /session/{id}/summarize       # 总结
POST   /session/{id}/revert          # 撤回
POST   /session/{id}/unrevert        # 恢复撤回
```

### Message (消息)

```
GET    /session/{id}/message              # 列出消息
POST   /session/{id}/message              # 发送消息 (流式)
GET    /session/{id}/message/{msgId}      # 获取消息
DELETE /session/{id}/message/{msgId}      # 删除消息
POST   /session/{id}/prompt_async         # 异步发送
POST   /session/{id}/command              # 执行命令
POST   /session/{id}/shell                # 执行Shell
```

### File (文件)

```
GET /file                # 列出文件
GET /file/content        # 读取文件
GET /file/status         # Git状态
GET /find                # 文本搜索
GET /find/file           # 文件搜索
GET /find/symbol         # 符号搜索
```

### Event (事件)

```
GET /global/event        # 全局SSE事件流
GET /event               # 项目SSE事件流
```

---

## 请求示例

### 创建会话

```bash
curl -X POST http://127.0.0.1:4096/session \
  -H "Content-Type: application/json" \
  -d '{"title": "My Session"}'
```

### 发送消息

```bash
curl -X POST http://127.0.0.1:4096/session/ses_xxx/message \
  -H "Content-Type: application/json" \
  -d '{
    "parts": [{"type": "text", "text": "Hello!"}],
    "model": {"providerID": "anthropic", "modelID": "claude-3-5-sonnet"}
  }'
```

### 读取文件

```bash
curl "http://127.0.0.1:4096/file/content?path=src/main.py"
```

### 搜索文件

```bash
curl "http://127.0.0.1:4096/find/file?query=*.py&type=file&limit=20"
```

---

## 事件类型

| 事件 | 描述 |
|------|------|
| `session.created` | 会话创建 |
| `session.updated` | 会话更新 |
| `session.deleted` | 会话删除 |
| `session.status` | 会话状态变更 |
| `session.idle` | 会话空闲 |
| `message.updated` | 消息更新 |
| `message.part.updated` | 消息部分更新 |
| `permission.asked` | 权限请求 |
| `question.asked` | 问题请求 |
| `file.edited` | 文件编辑 |
| `todo.updated` | 待办更新 |

---

## ID 前缀

| 类型 | 前缀 | 示例 |
|------|------|------|
| Session | `ses_` | `ses_abc123` |
| Message | `msg_` | `msg_xyz789` |
| Part | `prt_` | `prt_def456` |
| Permission | `per_` | `per_ghi012` |
| Question | `que_` | `que_jkl345` |

---

## 错误处理

```json
{
  "name": "NotFoundError",
  "data": { "message": "Session not found" }
}
```

```json
{
  "name": "APIError",
  "data": {
    "message": "Rate limit exceeded",
    "statusCode": 429,
    "isRetryable": true
  }
}
```
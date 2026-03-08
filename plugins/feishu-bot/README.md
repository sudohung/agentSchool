# 飞书机器人插件

这是一个 OpenCode 飞书机器人插件，支持双向通信：
- 监听飞书消息并转发给 OpenCode Agent 处理
- 将 OpenCode Agent 的处理结果发送回飞书
- 监听 OpenCode 各类事件并发送通知到飞书

## 功能特性

### 双向通信
- 📥 **接收飞书消息**: 监听飞书群聊消息，自动转发给 OpenCode Agent
- 📤 **发送处理结果**: 将 OpenCode Agent 的处理结果实时发送回飞书
- 📧 **事件通知**: 监听 OpenCode 各类事件（会话创建、完成、错误、工具执行等）
- 🔐 **权限响应**: 支持权限请求通知和响应

### 消息处理
- **智能去重**: 基于消息 ID 防止重复处理
- **时效过滤**: 自动忽略过期消息（>2 分钟）
- **防并发**: 防止同一消息被并发处理
- **临时回复**: 立即发送"处理中..."状态，提升用户体验

### 消息类型支持
- 文本消息处理
- 交互式卡片消息
- 错误消息通知
- 事件通知
- 权限请求卡片

### 命令支持
- `/new` - 重置会话
- `/instant:xxx` - 切换 Agent
- `/sessions` - 列出会话
- `/session:xxx` - 切换会话
- `/abort` - 中断会话
- `/permit:xxx` - 响应权限请求
- `/reply:xxx` - 发送消息应答

## 配置

### 环境变量

复制 `.env.example` 文件为 `.env` 并填写相应的配置：

```bash
cp .env.full.example .env.full
```

**必需配置：**
- `FEISHU_APP_ID`: 飞书应用 ID
- `FEISHU_APP_SECRET`: 飞书应用密钥

**可选配置：**
- `FEISHU_DEFAULT_CHAT_ID`: 默认通知的聊天 ID
- `OPENCODE_API_URL`: OpenCode API 地址（默认: http://localhost:4096）
- `FEISHU_MESSAGE_ID_TTL`: 消息去重时间窗口（毫秒，默认: 3600000 = 1小时）
- `FEISHU_MESSAGE_EXPIRY_TIME`: 消息过期时间（毫秒，默认: 120000 = 2分钟）
- `FEISHU_PROCESSING_TIMEOUT`: 处理超时时间（毫秒，默认: 5000 = 5秒）
- `FEISHU_LOG_LEVEL`: 日志级别（info/debug/error，默认: info）
- `FEISHU_DEBUG`: 是否启用调试模式（true/false，默认: false）

### 获取 Chat ID

1. 在飞书中创建群聊
2. 添加飞书机器人到群聊
3. 获取群聊的 `chat_id`

## 安装

### 1. 安装依赖

```bash
cd C:\Users\hung\Desktop\workspace\agentSchool\plugins\feishu-bot
npm install
```

### 2. 配置插件

在项目的 `opencode.json` 中添加：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["./plugins/feishu-bot"]
}
```

### 3. 配置环境变量

```bash
cp .env.full.example .env.full
# 编辑 .env.full 文件填写配置
```

## 监听的事件

### 会话事件
- `session.created` - 新会话创建
- `session.idle` - 会话处理完成
- `session.error` - 会话发生错误
- `session.status` - 会话状态变化
- `session.updated` - 会话更新

### 工具事件
- `tool.execute.after` - 工具执行完成

### 权限事件
- `permission.asked` - 权限请求（自动发送卡片通知）

### 其他事件
- `message.updated` - 消息更新
- `message.part.delta` - 消息部分增量
- `message.part.updated` - 消息部分更新
- `file.edited` - 文件编辑
- `question.replied` - 问题已回答
- `question.rejected` - 问题已拒绝

## 使用方式

### 飞书端使用
在飞书群聊中 @机器人 或发送包含特定关键词的消息，OpenCode Agent 会自动处理并返回结果。

### 命令消息

在飞书群聊中发送以下命令来控制会话和权限：

| 命令 | 说明 | 示例 |
|------|------|------|
| `/new` | 重置当前会话，创建新会话 | `/new` |
| `/instant:xxx` | 切换 Agent | `/instant:build` |
| `/sessions` | 列出当前 Agent 的所有会话 | `/sessions` |
| `/session:xxx` | 切换到指定会话并显示最新消息 | `/session:ses_xxx` |
| `/abort` | 中断当前会话 | `/abort` |
| `/permit:xxx` | 允许权限请求 | `/permit:per_xxx` |
| `/permit:xxx:deny` | 拒绝权限请求 | `/permit:per_xxx:deny` |
| `/reply:xxx` | 发送消息应答 | `/reply:请帮我分析这个文件` |

### 权限响应

当 OpenCode 需要外部目录/文件访问权限时，会发送权限请求卡片到飞书：
- 点击卡片上的 **✅ 允许** 或 **❌ 拒绝** 按钮
- 或使用命令 `/permit:permission_id` 允许
- 或使用命令 `/permit:permission_id:deny` 拒绝

### 事件通知
所有 OpenCode 事件都会自动发送到配置的默认聊天 ID 或事件关联的聊天 ID。

## WebSocket 长连接

- **自动重连机制**: 连接断开后自动重试
- **连接状态管理**: 防止重复连接
- **实时消息接收**: 低延迟消息处理

## 开发指南

### 调试模式
设置 `FEISHU_DEBUG=true` 可以启用详细日志输出，包括完整的 session 结构信息。

### 日志级别
通过 `FEISHU_LOG_LEVEL` 控制日志输出级别：
- `debug`: 输出所有调试信息
- `info`: 输出基本信息（默认）
- `error`: 仅输出错误信息

### 自定义通知逻辑

编辑 `feishu-plugin.js` 中的 `event` 钩子函数，添加或修改事件处理逻辑：

```javascript
event: async ({ event }) => {
    // 添加你的自定义事件处理
    if (event.type === "your-event") {
        const targetChatId = FeishuConfig.defaultChatId || event.session?.chatId;
        if (targetChatId) {
            await sendEventNotification(
                feishuClient,
                targetChatId,
                "自定义标题",
                "自定义内容"
            );
        }
    }
}
```

## 目录结构

```
feishu-bot/
├── feishu-plugin.js      # 主插件入口
├── config.js            # 配置管理
├── message-parser.js    # 消息解析器
├── message/             # 消息发送模块
│   ├── feishu-message-sender.js
│   └── index.js
├── .env.example         # 环境变量示例
└── package.json         # 依赖配置
```

## 测试

启动 OpenCode 后：
1. 在飞书群聊中发送消息测试双向通信
2. 触发 OpenCode 事件测试通知功能

## 注意事项

1. 确保飞书 AppID 和 AppSecret 正确配置
2. 确保聊天 ID 有效（可通过环境变量或事件上下文获取）
3. 需要网络连接才能发送消息
4. 敏感信息通过环境变量配置，不要硬编码
5. 生产环境中建议使用 HTTPS 地址
6. 消息去重机制会占用内存，长时间运行请注意内存使用情况

## 开发

基于 OpenCode Plugin API 开发，参考：https://opencode.ai/docs/plugins/

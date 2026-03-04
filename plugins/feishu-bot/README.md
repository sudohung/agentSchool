# 飞书通知插件

将 OpenCode 的事件通知发送到飞书。

## 功能

- 📧 监听 OpenCode 各类事件（会话创建、完成、错误、工具执行等）
- 💬 自动发送格式化消息到飞书群聊
- 🔔 实时通知项目状态变化

## 安装

### 1. 安装依赖

```bash
cd E:\workspace\xpproject\agentSchool\plugins\feishu-bot
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

或者全局配置 (`~/.config/opencode/opencode.json`)：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["E:\\workspace\\xpproject\\agentSchool\\plugins\\feishu-bot"]
}
```

## 配置飞书

### 获取 Chat ID

1. 在飞书中创建群聊
2. 添加飞书机器人到群聊
3. 获取群聊的 `chat_id`

### 修改聊天 ID

编辑 `feishu-plugin.js`，将所有 `"chat_id_here"` 替换为你的实际聊天 ID：

```javascript
await sendFeishuMessage(
    "你的 chat_id", // 替换这里
    "消息标题",
    "消息内容"
);
```

## 监听的事件

### 会话事件
- `session.created` - 新会话创建
- `session.idle` - 会话处理完成
- `session.error` - 会话发生错误

### 工具事件
- `tool.execute.after` - 工具执行完成

### 其他事件
- `message.updated` - 消息更新
- `file.edited` - 文件编辑

## 自定义通知逻辑

编辑 `feishu-plugin.js` 中的 `event` 钩子函数，添加或修改事件处理逻辑：

```javascript
event: async ({ event }) => {
    // 添加你的自定义事件处理
    if (event.type === "your-event") {
        await sendFeishuMessage(
            "chat_id",
            "自定义标题",
            "自定义内容"
        );
    }
}
```

## 消息格式

使用飞书交互式卡片，包含：
- **标题**：事件类型
- **内容**：详细信息

## 测试

启动 OpenCode 后，触发相应事件即可看到飞书通知。

## 注意事项

1. 确保飞书 AppID 和 AppSecret 正确
2. 确保聊天 ID 有效
3. 需要网络连接才能发送消息
4. 敏感信息建议通过环境变量配置

## 开发

基于 OpenCode Plugin API 开发，参考：https://opencode.ai/docs/plugins/

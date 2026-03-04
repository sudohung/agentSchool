# 飞书 OpenCode 机器人插件

## 🎯 核心设计

### OpenCode Hook 能力应用

```typescript
export const FeishuBotPlugin: Plugin = async (ctx) => {
  return {
    // 1. init() - 插件加载时调用
    async init() {
      // ✅ 启动飞书 WebSocket 长连接
      wsClient.start({ ... })
    },
    
    // 2. tool - 提供自定义工具给 Agent
    tool: {
      "feishu.send_text": tool({ ... }),
      "feishu.respond_task": tool({ ... }),
    },
    
    // 3. event - 监听 OpenCode 事件
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        // 会话完成时发送结果
      }
    },
    
    // 4. shell.env - 注入环境变量
    "shell.env": async (input, output) => {
      output.env.FEISHU_APP_ID = process.env.FEISHU_APP_ID
    }
  }
}
```

## 📋 工作流程

```
插件加载
  ↓
init() 启动飞书长连接
  ↓
监听飞书消息 (im.message.receive_v1)
  ↓
检测关键词 "opencode"
  ↓
创建 OpenCode Session
  ↓
Agent 处理任务
  ↓
session.idle 事件触发
  ↓
发送结果到飞书
```

## ⚙️ 配置步骤

### 1. 环境变量

```bash
# .env 文件
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
OPENCODE_API_URL=http://localhost:4096
```

### 2. 启用插件

```json
// opencode.json
{
  "plugin": ["./plugins/feishu-bot-plugin.ts"]
}
```

### 3. 安装依赖

```bash
npm install @larksuiteoapi/node-sdk
```

### 4. 启动 OpenCode

```bash
opencode
```

## 💬 使用方式

在飞书发送消息：

```
opencode 分析项目架构
```

或

```
@opencode 创建 README 文件
```

## 🔧 可用工具

1. **feishu.send_text** - 发送文本消息
2. **feishu.respond_task** - 响应任务结果

## 🎨 特性

✅ **自动建立长连接** - 插件加载时自动启动
✅ **无需公网IP** - 使用 WebSocket 长连接
✅ **自动映射管理** - 会话与飞书群映射
✅ **双通道响应** - Agent 工具 + 会话完成事件

## 📊 日志示例

```
[feishu-bot] 🚀 飞书机器人插件初始化中...
[feishu-bot] ✅ 飞书长连接已建立，开始监听消息
[feishu-bot] 收到飞书消息
[feishu-bot] 会话已创建: session_xxx
[feishu-bot] 任务结果已发送到飞书
```

## 🚀 完成！

插件已正确实现，使用 OpenCode 的 hook 能力自动管理飞书连接。
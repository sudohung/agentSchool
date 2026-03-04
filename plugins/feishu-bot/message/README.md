# 飞书消息发送模块

## 📖 概述

`message` 模块提供了完整的飞书消息发送功能，封装了各种类型的消息发送场景，让开发者可以更专注于业务逻辑。

## 🎯 特性

- ✅ **多种消息类型**：支持文本、交互式卡片等多种消息格式
- ✅ **场景化封装**：针对常见场景提供专用函数
- ✅ **错误处理**：完善的错误捕获和日志记录
- ✅ **类型安全**：完整的 JSDoc 类型定义
- ✅ **易于扩展**：模块化设计，便于添加新功能
- ✅ **统一响应格式**：所有发送函数均返回标准飞书 API 响应数据

## 📁 文件结构

```
message/
├── index.js                      # 模块入口，统一导出
├── feishu-message-sender.js      # 核心实现文件
└── README.md                     # 本文档
```

## 🚀 快速开始

### 1. 导入模块

```javascript
// 方式 1: 导入所有功能
import * as message from './message/index.js';

// 方式 2: 按需导入
import { 
    createFeishuClient,
    sendTextMessage,
    sendCardMessage,
    sendAIResponse
} from './message/index.js';

// 方式 3: 直接导入具体函数
import { sendTextMessage } from './message/feishu-message-sender.js';
```

### 2. 创建客户端

```javascript
import { createFeishuClient } from './message/index.js';

const feishuClient = createFeishuClient({
    appId: 'your-app-id',
    appSecret: 'your-app-secret'
});
```

### 3. 发送消息

```javascript
// 发送文本消息
await sendTextMessage(feishuClient, 'chat_id_123', '你好，这是一条文本消息');

// 发送卡片消息
await sendCardMessage(
    feishuClient, 
    'chat_id_123', 
    '这是一条卡片消息的内容',
    '卡片标题'
);
```

## 📋 API 参考

### `createFeishuClient(config)`

创建飞书客户端实例

**参数：**
- `config` {Object} - 配置对象
  - `appId` {string} - 应用 ID
  - `appSecret` {string} - 应用密钥

**返回值：**
- `lark.Client` - 飞书客户端实例

**示例：**
```javascript
const client = createFeishuClient({
    appId: 'cli_a9059178d1b8dcd1',
    appSecret: 'utn16AUDhHarUUWY2yaZScMX4OJNBY4K'
});
```

---

### `sendTextMessage(client, chatId, text)`

发送纯文本消息

**参数：**
- `client` {lark.Client} - 飞书客户端实例
- `chatId` {string} - 聊天 ID
- `text` {string} - 文本内容

**返回值：**
- `Promise<Object>` - 飞书 API 响应结果，格式：`{ code, msg, data: { message_id } }`

**示例：**
```javascript
const result = await sendTextMessage(client, 'chat_id_123', 'Hello World!');
console.log(result);
// 输出:
// {
//   code: 0,
//   msg: 'success',
//   data: {
//     message_id: 'om_1234567890abcdef'
//   }
// }
```

---

### `sendCardMessage(client, chatId, content, [title])`

发送交互式卡片消息（带默认标题）

**参数：**
- `client` {lark.Client} - 飞书客户端实例
- `chatId` {string} - 聊天 ID
- `content` {string} - 卡片内容
- `title` {string} (可选) - 卡片标题，默认为 `'消息通知'`

**返回值：**
- `Promise<Object>` - 飞书 API 响应结果，格式：`{ code, msg, data: { message_id } }`

**示例：**
```javascript
// 使用默认标题
const result = await sendCardMessage(client, 'chat_id_123', '卡片内容');
console.log(result.data.message_id); // 获取消息 ID

// 自定义标题
const result2 = await sendCardMessage(
    client, 
    'chat_id_123', 
    '详细的卡片内容...',
    '重要通知'
);
```

---

### `sendThinkingMessage(client, chatId)`

发送思考状态消息

**参数：**
- `client` {lark.Client} - 飞书客户端实例
- `chatId` {string} - 聊天 ID

**返回值：**
- `Promise<Object>` - 飞书 API 响应结果，格式：`{ code, msg, data: { message_id } }`

**用途：** 在 AI 处理过程中发送临时提示

**示例：**
```javascript
// 用户发送消息后，先回复思考状态
const result = await sendThinkingMessage(client, chatId);
console.log('思考消息已发送，ID:', result.data.message_id);
// 然后处理请求...
```

---

### `sendErrorMessage(client, chatId, errorMessage, [prefix])`

发送错误消息

**参数：**
- `client` {lark.Client} - 飞书客户端实例
- `chatId` {string} - 聊天 ID
- `errorMessage` {string} - 错误信息
- `prefix` {string} (可选) - 错误前缀，默认为 `'❌ 处理失败'`

**返回值：**
- `Promise<Object>` - 飞书 API 响应结果，格式：`{ code, msg, data: { message_id } }`

**示例：**
```javascript
// 使用默认前缀
const result = await sendErrorMessage(client, chatId, '网络连接超时');
console.log('错误消息已发送:', result.data.message_id);

// 自定义前缀
const result2 = await sendErrorMessage(
    client, 
    chatId, 
    '数据库连接失败',
    '⚠️ 系统错误'
);
```

---

### `sendAIResponse(client, chatId, userMessage, aiResponse)`

发送 AI 回复消息（自动格式化标题）

**参数：**
- `client` {lark.Client} - 飞书客户端实例
- `chatId` {string} - 聊天 ID
- `userMessage` {string} - 用户原始消息
- `aiResponse` {string} - AI 回复内容

**返回值：**
- `Promise<void>`

**特点：** 自动截取用户消息前 20 个字符作为标题

**示例：**
```javascript
const userMessage = '请帮我分析一下这段代码的问题...';
const aiResponse = '这段代码存在以下问题：1... 2... 3...';

await sendAIResponse(client, chatId, userMessage, aiResponse);
// 标题自动设置为："回复：请帮我分析一下这段代码..."
```

---

### `sendEventNotification(client, chatId, eventType, eventDescription)`

发送事件通知消息

**参数：**
- `client` {lark.Client} - 飞书客户端实例
- `chatId` {string} - 聊天 ID
- `eventType` {string} - 事件类型
- `eventDescription` {string} - 事件描述

**返回值：**
- `Promise<void>`

**示例：**
```javascript
// 会话创建通知
await sendEventNotification(
    client,
    chatId,
    'OpenCode 会话已创建',
    `项目：MyProject\n会话 ID: session-123`
);

// 工具执行通知
await sendEventNotification(
    client,
    chatId,
    '🛠️ 工具执行：FileEditor',
    '文件 example.js 已成功修改'
);
```

---

## 💡 使用场景

### 场景 1: AI 对话机器人

```javascript
import { 
    createFeishuClient,
    sendThinkingMessage,
    sendAIResponse,
    sendErrorMessage
} from './message/index.js';

async function handleUserMessage(chatId, userMessage) {
    const client = createFeishuClient(config);
    
    try {
        // 1. 发送思考状态
        await sendThinkingMessage(client, chatId);
        
        // 2. 调用 AI 服务
        const aiResponse = await callAI(userMessage);
        
        // 3. 发送 AI 回复
        await sendAIResponse(client, chatId, userMessage, aiResponse);
        
    } catch (error) {
        // 4. 发送错误消息
        await sendErrorMessage(client, chatId, error.message);
    }
}
```

### 场景 2: 事件通知系统

```javascript
import { 
    createFeishuClient,
    sendEventNotification
} from './message/index.js';

// 监听系统事件
eventEmitter.on('session.created', async (session) => {
    await sendEventNotification(
        client,
        adminChatId,
        '✨ 新会话创建',
        `用户：${session.user}\n项目：${session.project}`
    );
});

eventEmitter.on('task.completed', async (task) => {
    await sendEventNotification(
        client,
        teamChatId,
        '✅ 任务完成',
        `任务：${task.name}\n耗时：${task.duration}`
    );
});
```

### 场景 3: 多类型消息混合发送

```javascript
import { 
    createFeishuClient,
    sendTextMessage,
    sendCardMessage
} from './message/index.js';

async function sendDailyReport(chatId, report) {
    // 先发送文本摘要
    await sendTextMessage(
        client,
        chatId,
        `📊 今日完成 ${report.taskCount} 个任务`
    );
    
    // 再发送详细卡片
    await sendCardMessage(
        client,
        chatId,
        generateDetailedContent(report),
        '📈 每日工作报告'
    );
}
```

---

## 🔧 最佳实践

### 1. 错误处理

```javascript
try {
    await sendAIResponse(client, chatId, userMessage, response);
} catch (error) {
    console.error('[Feishu] 发送失败:', error);
    // 可以选择重试或记录日志
}
```

### 2. 消息去重

```javascript
const sentMessages = new Set();

async function sendMessageWithDedup(chatId, content) {
    const messageId = `${chatId}:${Date.now()}`;
    
    if (sentMessages.has(messageId)) {
        return; // 跳过重复消息
    }
    
    await sendCardMessage(client, chatId, content);
    sentMessages.add(messageId);
    
    // 5 秒后清理
    setTimeout(() => sentMessages.delete(messageId), 5000);
}
```

### 3. 批量发送优化

```javascript
async function sendBatchMessages(messages) {
    // 控制发送频率，避免触发限流
    for (let i = 0; i < messages.length; i++) {
        await sendCardMessage(client, messages[i].chatId, messages[i].content);
        
        if (i < messages.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 100)); // 间隔 100ms
        }
    }
}
```

---

## ⚠️ 注意事项

### 1. 客户端复用

```javascript
// ✅ 推荐：创建一次，重复使用
const client = createFeishuClient(config);
await sendTextMessage(client, chatId1, 'msg1');
await sendTextMessage(client, chatId2, 'msg2');

// ❌ 不推荐：每次都创建新客户端
await sendTextMessage(createFeishuClient(config), chatId1, 'msg1');
await sendTextMessage(createFeishuClient(config), chatId2, 'msg2');
```

### 2. 异步处理

```javascript
// ✅ 推荐：使用 async/await
async function sendMessage() {
    await sendTextMessage(client, chatId, 'Hello');
    console.log('发送成功');
}

// ❌ 不推荐：忽略 Promise
function sendMessage() {
    sendTextMessage(client, chatId, 'Hello'); // 无法捕获错误
    console.log('发送成功'); // 可能过早执行
}
```

### 3. 内容长度限制

```javascript
// 飞书卡片消息有长度限制，建议控制在合理范围内
const MAX_CONTENT_LENGTH = 5000;

function truncateContent(content) {
    if (content.length > MAX_CONTENT_LENGTH) {
        return content.substring(0, MAX_CONTENT_LENGTH) + '\n...(内容过长，已截断)';
    }
    return content;
}
```

---

## 🐛 常见问题

### Q1: 发送失败怎么办？

**A:** 检查以下几点：
1. AppID 和 AppSecret 是否正确
2. 聊天 ID 是否有效
3. 网络是否正常
4. 查看控制台错误日志

### Q2: 如何发送富文本消息？

**A:** 目前支持基础的交互式卡片，如需富文本可以：
```javascript
// 使用 Markdown 格式
const markdownContent = `
# 标题
**粗体文本**
*斜体文本*
- 列表项 1
- 列表项 2
`;
await sendCardMessage(client, chatId, markdownContent);
```

### Q3: 如何发送图片？

**A:** 当前版本主要支持文本和卡片，图片发送功能将在后续版本中添加。

---

## 🔄 版本历史

### v1.0.0 (2026-03-04)
- ✨ 初始版本
- ✅ 支持文本消息
- ✅ 支持交互式卡片消息
- ✅ 场景化封装函数

---

## 📚 相关资源

- [飞书开放平台文档](https://open.feishu.cn/document)
- [Lark SDK GitHub](https://github.com/larksuite/lark-nodejs)
- [消息解析器文档](../MESSAGE_PARSER_README.md)

---

**维护者**: 开发团队  
**最后更新**: 2026-03-04

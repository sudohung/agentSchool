# Agent 模块

基于策略模式和回调模式的 Agent 管理模块，支持切换不同的 AI 客户端实现，并提供丰富的回调机制。

## 核心组件

### 1. IAgentStrategy（策略接口）
定义统一的 Agent 接口，所有 Agent 实现必须遵循此接口。

### 2. OpencodeAgent（具体实现）
基于 @opencode-ai/sdk 的 OpenCode Agent 实现。

### 3. AgentManager（管理器）
- 会话管理（自动创建和缓存 session）
- 消息去重（防止重复处理）
- 顺序锁（保证同一会话消息顺序执行）
- 回调机制（支持 Agent 主动触发调用端逻辑）

## 回调事件类型

| 事件名 | 触发时机 | 参数 |
|--------|----------|------|
| `onSessionCreated` | 会话创建成功时 | `(sessionId, title)` |
| `onMessageReceived` | 消息发送给 Agent 前 | `(sessionId, message)` |
| `onMessageSent` | 消息收到响应后 | `(sessionId, message, response)` |
| `onError` | 发生错误时 | `(sessionId, error)` |
| `onCustomEvent` | 自定义事件 | `(eventName, data)` |

## 使用示例

### 基础用法

```javascript
import { createAgentManager, OpencodeAgent } from './agent/index.js';

// 创建 Agent 实例
const agent = new OpencodeAgent(client);

// 创建 Agent 管理器（带回调）
const agentManager = createAgentManager({
    agent,
    callbacks: {
        onSessionCreated: (sessionId, title) => {
            console.log(`新会话创建：${sessionId}, 标题：${title}`);
        },
        onMessageReceived: (sessionId, message) => {
            console.log(`发送消息到 ${sessionId}: ${message}`);
        },
        onMessageSent: (sessionId, message, response) => {
            console.log(`收到响应：${sessionId}`);
        },
        onError: (sessionId, error) => {
            console.error(`会话 ${sessionId} 错误：`, error.message);
        }
    }
});

// 发送消息
const sessionId = await agentManager.getSession(chatId);
const response = await agentManager.sendMessage(sessionId, '你好');
```

### 动态注册回调

```javascript
// 创建时不传回调，后续动态注册
const agentManager = createAgentManager({ agent });

// 链式调用注册
agentManager
    .registerCallback('onSessionCreated', (sessionId, title) => {
        console.log(`会话已创建：${sessionId}`);
    })
    .registerCallback('onMessageSent', (sessionId, message, response) => {
        console.log(`消息已发送：${message}`);
    });

// 注销回调
agentManager.unregisterCallback('onMessageSent');
```

### 手动触发回调

```javascript
// 在 Agent 外部手动触发回调
agentManager.triggerCallback('onCustomEvent', 'userLogin', {
    userId: '123',
    timestamp: Date.now()
});
```

### 在 feishu-plugin.js 中的完整示例

```javascript
import { createAgentManager, OpencodeAgent } from './agent/index.js';

export const OpencodeFeishuPlugin = async ({ project, agentClient, $, directory }) => {
    
    // 创建 Agent 策略实例
    const agent = new OpencodeAgent(agentClient);
    
    // 创建 Agent 管理器（带完整回调）
    const agentManager = createAgentManager({
        agent,
        processingTimeout: 30000,
        callbacks: {
            onSessionCreated: (sessionId, title) => {
                console.log(`[飞书] 新会话：${sessionId}`);
                // 可以在这里发送飞书通知
            },
            onMessageReceived: (sessionId, message) => {
                console.log(`[飞书] 发送消息：${message}`);
            },
            onMessageSent: (sessionId, message, response) => {
                console.log(`[飞书] 收到回复：${response}`);
            },
            onError: (sessionId, error) => {
                console.error(`[飞书] 错误：`, error);
                // 可以在这里发送错误通知到飞书
            }
        }
    });
    
    // 使用 agentManager 处理消息
    await handleFeishuMessage(chatId, userMessage, {
        channelClient: feishuClient,
        agentManager
    });
};
```

## 扩展新的 Agent

实现自定义 Agent 只需继承 `IAgentStrategy`：

```javascript
import { IAgentStrategy } from './agent-strategy.js';

export class ClaudeAgent extends IAgentStrategy {
    constructor(client) {
        super();
        this.client = client;
    }

    getName() {
        return 'ClaudeAgent';
    }

    async createSession(title) {
        // 实现 Claude 的会话创建逻辑
        const session = await this.client.sessions.create({ name: title });
        
        // 触发回调
        const callbacks = this.getCallbacks();
        if (callbacks?.onSessionCreated) {
            callbacks.onSessionCreated(session.id, title);
        }
        
        return session.id;
    }

    async sendMessage(sessionId, message) {
        try {
            // 触发发送前回调
            const callbacks = this.getCallbacks();
            if (callbacks?.onMessageReceived) {
                callbacks.onMessageReceived(sessionId, message);
            }

            const response = await this.client.messages.create({
                session_id: sessionId,
                content: message
            });

            // 触发发送后回调
            if (callbacks?.onMessageSent) {
                callbacks.onMessageSent(sessionId, message, response);
            }

            return response;
        } catch (error) {
            // 触发错误回调
            const callbacks = this.getCallbacks();
            if (callbacks?.onError) {
                callbacks.onError(sessionId, error);
            }
            throw error;
        }
    }
}
```

## 注意事项

1. **回调执行顺序**：同一事件的回调按注册顺序执行
2. **错误处理**：回调内部的错误会被捕获并记录，不影响主流程
3. **锁机制**：同一 sessionId 的消息会顺序执行，不同 sessionId 并行执行
4. **内存管理**：长时间运行的应用应定期调用 `clearSessionMap()` 清理过期会话

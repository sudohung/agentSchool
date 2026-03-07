import * as lark from '@larksuiteoapi/node-sdk';
import { createOpencodeClient, createOpencode } from "@opencode-ai/sdk"
import {
    handleFeishuMessage,sendCardMessage,updateMessage,sendTextMessage
} from '../../feishu-bot/message/index.js';
import { createFeishuWSClient } from '../../feishu-bot/client/index.js';
import { FeishuConfig } from '../../feishu-bot/config.js';
import { createAgentManager, OpencodeAgent } from '../../feishu-bot/agent/index.js';
// 引入webhook
import { sendWebhookMessage, sendEventNotification, sendErrorMessage } from '../../feishu-bot/webhook/webhook-sender.js';
import { createEventHandlerChain } from '../../feishu-bot/handlers/index.js';
import { createChatManager } from '../../feishu-bot/chat/index.js';


// 验证配置
if (!FeishuConfig.isValid()) {
    console.error('[FeishuBot] 缺少必要的环境变量配置：FEISHU_APP_ID 和 FEISHU_APP_SECRET');
    throw new Error('飞书机器人配置不完整');
}

// 创建 飞书 客户端（用于发送消息）
const feishuClient = new lark.Client({
    appId: FeishuConfig.appId,
    appSecret: FeishuConfig.appSecret
});

// 创建 OpenCode 客户端实例
const opencodeClient = createOpencodeClient({
  baseUrl: "http://127.0.0.1:4096",
})

const qwen35PlusClient = createOpencodeClient({
  baseUrl: "http://127.0.0.1:4096",
})
const glm5Client = createOpencodeClient({
  baseUrl: "http://127.0.0.1:4096",
})
const qwen3max202601Client = createOpencodeClient({
  baseUrl: "http://127.0.0.1:4096",
})
const kimik25Client = createOpencodeClient({
  baseUrl: "http://127.0.0.1:4096",
})

//
//const opencodeClient = await createOpencode({
//  hostname: "127.0.0.1",
//  port: 4096
//})
//console.log(`opencodeClient  ${opencodeClient}`)

console.log(`opencode sessions  ${opencodeClient}`)

// 创建 Agent 策略实例
const agent = new OpencodeAgent(opencodeClient).initModel(FeishuConfig.opencodeProvider,"qwen3.5-plus");
const bk1 = new OpencodeAgent(opencodeClient).initModel("opencode","minimax-m2.5-free");
const bk2 = new OpencodeAgent(opencodeClient).initModel("opencode","big-pickle");

const or1 = new OpencodeAgent(opencodeClient).initModel("openrouter","z-ai/glm-4.5-air:free");
const or2 = new OpencodeAgent(opencodeClient).initModel("openrouter","minimax-m2.5-free");

const cop1 = new OpencodeAgent(opencodeClient).initModel("github-copilot","gpt-5-mini");
const cop2 = new OpencodeAgent(opencodeClient).initModel("github-copilot","gpt-4o");
const cop3 = new OpencodeAgent(opencodeClient).initModel("github-copilot","gpt-4.1");



const planAgent = new OpencodeAgent(qwen35PlusClient).initModel(FeishuConfig.opencodeProvider,"glm-5");
const auxAgent = new OpencodeAgent(glm5Client).initModel(FeishuConfig.opencodeProvider,"glm-5");
const workerAgent = new OpencodeAgent(qwen3max202601Client).initModel(FeishuConfig.opencodeProvider,"qwen3-max-2026-01-23");
const subAgent = new OpencodeAgent(kimik25Client).initModel(FeishuConfig.opencodeProvider,"kimi-k2.5");

// 创建 Agent 策略实例
const agentMap = new Map();
agentMap.set("main", agent);
agentMap.set("bk1", bk1);
agentMap.set("bk2", bk2);
agentMap.set("or1", or1);
agentMap.set("cop1", cop1);
agentMap.set("cop2", cop2);
agentMap.set("cop3", cop3);
agentMap.set("planAgent", planAgent);
agentMap.set("auxAgent", auxAgent);
agentMap.set("workerAgent", workerAgent);
agentMap.set("subAgent", subAgent);

// 创建交流管理器
const chatManager = createChatManager(feishuClient);

// 创建 Agent 管理器（封装 sessionMap 和 processingMessages）
const agentManager = createAgentManager({
    agent,
    processingTimeout: FeishuConfig.messageConfig.processingTimeout,
    messageIdTtl: FeishuConfig.messageConfig.messageIdTtl,
    agentMap: agentMap, // 可选：预先定义一些 Agent 实例
    callbacks: {
        // 自定义事件回调示例
        onCustomEvent: (eventName, data) => {
            console.log(`[fxbot] 触发自定义事件：${eventName}`, data);
            
            // 根据事件类型执行不同逻辑
            switch (eventName) {
                case 'userLogin':
                    console.log(`[fxbot] 用户登录：${data.userId}`);
                    // 可以在这里发送飞书通知
                    break;
                    
                case 'taskComplete':
                    console.log(`[fxbot] 任务完成：${data.taskId}, 结果：${data.result}`);
                    // 发送任务完成通知到飞书
                    break;
                    
                case 'systemAlert':
                    console.log(`[fxbot] 系统告警：${data.level} - ${data.message}`);
                    // 发送紧急通知到飞书群
                    break;
                    
                default:
                    console.log(`[fxbot] 未知事件类型：${eventName}`);
            }
        },
        onError: (sessionId, data) => {
            console.error(`[feishuClient] 会话 ${sessionId} 发生错误:`, data);
        }
    }
});

// 创建 WebSocket feishu 客户端
const feishuWSClient = createFeishuWSClient({
    appId: FeishuConfig.appId,
    appSecret: FeishuConfig.appSecret,
    logLevel: FeishuConfig.logConfig.level,
    messageExpiryTime: FeishuConfig.messageConfig.messageExpiryTime,
    messageIdTtl: FeishuConfig.messageConfig.messageIdTtl
});

feishuWSClient.start((chatId, userMessage, messageContext) => {
    return handleFeishuMessage(chatId, userMessage, messageContext, {
        chatManager: chatManager,
        agentManager
    });
});



// 启动opencode事件监听器
;(async () => {
    const events = await opencodeClient.event.subscribe()
    // 增加一个map 记录chatId 和 mid
    const chatIdMidMap = new Map();

    const eventChain = createEventHandlerChain();
    for await (const event of events.stream) {
        // 取mapsize
        const chatSize = chatIdMidMap.size;
//        console.log(`[OpenCode] chatSize:${chatSize} ,收到事件:${event.type}`)
//        console.log("[OpenCode] 收到事件11:", JSON.stringify(event))


        // 根据事件类型发送飞书通知
        if (event.type === "message.part.updated") {
            let mid = null;
            const chatId = agentManager.getChatIdBySessionId(event.properties?.part?.sessionID)
            if (chatIdMidMap.has(chatId)) {
                mid = chatIdMidMap.get(chatId)
            }
            if (chatId) {

                 if (!mid) {
                    mid = await sendTextMessage(
                        chatManager,
                        chatId || FeishuConfig.defaultChatId || "oc_b009e81f843b41a12da1cbb083b7efd1",
                        "新会话"
                    )
                    chatIdMidMap.set(chatId, mid)
                 } else {
                     if (event.properties.part.type == "reasoning") {
                         const msg = event.properties.part.text;
                         if (msg) {
                             await updateMessage(chatManager, mid.data.message_id,"text",
                             event.properties?.part?.sessionID, msg );
                         }
                     }

                 }
            }
        }


        // 根据事件类型发送飞书通知
        if (event.type === "session.idle") {

            // 等等500ms
            await new Promise(resolve => setTimeout(resolve, 500));
            let mid = null;
            const chatId = agentManager.getChatIdBySessionId(event.properties.sessionID)
            if (chatIdMidMap.has(chatId)) {
                mid = chatIdMidMap.get(chatId)
            }
            await updateMessage(chatManager, mid.data.message_id, "text",
            event.properties.sessionID, " " );
            chatIdMidMap.delete(chatId)
        }

        await eventChain.handle(event, {  });


        // 监听session 失败事件
        if (event.type === "session.error") {
            // 等等500ms
            console.log(`[OpenCode] 收到 session.error 事件: ${JSON.stringify(event)}`);

            sendWebhookMessage(
                `会话异常：${event.properties.sessionID}`,
                `会话 ${event.properties.sessionID} 发生异常，错误信息：${event.properties.errorMessage}\n时间：${new Date().toLocaleString('zh-CN')}`
            );
        }
    }
})().catch(console.error)
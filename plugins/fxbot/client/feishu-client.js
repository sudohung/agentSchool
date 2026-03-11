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
import { createEventHandlerChain } from '../../feishu-bot/event/index.js';
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

const hostname = 'http://172.20.157.162'

// 创建 OpenCode 客户端实例
const opencodeClient = createOpencodeClient({
  baseUrl: hostname + ":4096",
})

const qwen35PlusClient = createOpencodeClient({
  baseUrl: hostname + ":4096",
})
const glm5Client = createOpencodeClient({
  baseUrl: hostname + ":4096",
})
const qwen3max202601Client = createOpencodeClient({
  baseUrl: hostname + ":4096",
})
const kimik25Client = createOpencodeClient({
  baseUrl: hostname + ":4096",
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

// 创建交流管理器（传入 agentManager 以支持 Agent 切换功能）
const chatManager = createChatManager(feishuClient, agentManager);

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
    const chatIdAskMidMap = new Map();

    const eventChain = createEventHandlerChain();
    for await (const event of events.stream) {
        // 取mapsize
        const chatSize = chatIdMidMap.size;
//        console.log(`[OpenCode] chatSize:${chatSize} ,收到事件:${event.type}`)
//        console.log("[OpenCode] 收到事件11:", JSON.stringify(event))

        let mid = null;
        let askMid = null;
        const chatId = agentManager.getChatIdBySessionId(event.properties?.part?.sessionID ||
            event.properties?.sessionID)
        if (chatIdMidMap.has(chatId)) {
            mid = chatIdMidMap.get(chatId)
        }


        if (event.type === "question.asked") {
             // 将问题发送到子消息栏给用户回复
             // {"type":"question.asked","properties":{"id":"que_cce603a9b001Hr7Y1Nl9JyjDrR","sessionID":"ses_331a00d20ffeUzLd1p6OHkgiLb","questions":[{"question":
             //    "你想切换到哪个目录？","header":"目录选择","options":[{"label":"plugins","description":"切换到 plugins 目录"},{"label":"当前目录下的其他目录","description":"切换到其他子目录"}]}],"tool":{"messageID":"msg_cce60312d001EPPkc2pjQxzLDB","callID":"call_48918c0eddfc4b4086377607"}}}
            // questions 拼接成字符串 question: [option: xxx, option: bbb]

            await new Promise(resolve => setTimeout(resolve, 1000));
            if (chatIdAskMidMap.has(chatId)) {
                askMid = chatIdAskMidMap.get(chatId)
            }
            // questions 拼接成字符串
            if (chatId && !askMid) {
                const question = event.properties.questions.map(q => `${q.question} ${q.header} ${q.options.map(o => o.label).join(",\r\t")}`)

                askMid = await sendTextMessage(
                    chatManager,
                    chatId,
                    `
                    工具提问：${event.properties.questions[0].question}，
                    问题详情：${event.properties.questions[0].header}，
                    选项：\r\t${question}，
                    请回复选项来回答问题。`,
                )
                chatIdAskMidMap.set(chatId, askMid)
            }
        }
        if (event.type === "permission.asked1") {
            await new Promise(resolve => setTimeout(resolve, 1000));
            console.log(`[OpenCode] permission.asked event, chatId:${chatId}, permission:${JSON.stringify(event)}`)
            //  {"type":"permission.asked","properties":{"id":"per_cce42f5a0001qw4cim8rataS3b","sessionID":"ses_331be5570ffeNNCoK3qbxlpuI3","permission":"externa
            //    l_directory","patterns":["C:/Users/hung/AppData/Roaming/npm/*"],"metadata":{"filepath":"C:\\Users\\hung\\AppData\\Roaming\\npm\\opencode.cmd","parentDir":"C:\\Users\\hung\\AppData\\Roaming\\npm"},"always":["C:/Users/hung/AppData/Roaming/npm/*"],"tool":{"messageID":"msg_cce42ed25001Rg9Yg0xbTIh7Xi","callID":"call_a17b6f925f5d484fac32ddaa"}}}
            // 将请求消息发给用户
            if (chatIdAskMidMap.has(chatId)) {
                askMid = chatIdAskMidMap.get(chatId)
            }
            if (chatId && !askMid) {
                askMid = await sendTextMessage(
                    chatManager,
                    chatId,
                    `工具调用权限请求：${event.properties.permission}，\n请求内容：${event.properties.patterns}，\n 是否允许？`,
                )
                chatIdAskMidMap.set(chatId, askMid)
            }
        }

        if (event.type === "message.part.updated") {
            console.log(`[OpenCode] ======= message.part.updated event, chatId:${chatId}, mid:${mid}, askMid:${askMid}, event:${JSON.stringify(event)}`)
            if (chatId) {
                if (!mid) {
                    mid = await sendTextMessage(
                        chatManager,
                        chatId || FeishuConfig.defaultChatId || "oc_b009e81f843b41a12da1cbb083b7efd1",
                        "新会话"
                    )
                    chatIdMidMap.set(chatId, mid)
                }else {
                     if (event.properties.part.type == "reasoning") {
                         const msg = event.properties.part.text;
                         if (msg) {
                             await updateMessage(chatManager, mid.data.message_id,"text",
                             event.properties?.part?.sessionID, msg );
                         }
                    }
                }
            }
        } else if (event.type === "session.idle") {
            if (mid) {
                console.log(`[OpenCode] session.idle:${JSON.stringify(mid)} }`)
                // 等等500ms
                await new Promise(resolve => setTimeout(resolve, 500));
                const chatId = agentManager.getChatIdBySessionId(event.properties.sessionID)
                await updateMessage(chatManager, mid.data.message_id, "text",
                event.properties.sessionID, " " );
                chatIdMidMap.delete(chatId)
            }
        } else {
            // 所有其他事件都交给责任链处理
            await eventChain.handle(event, { 
                notify: async (title, content) => {
                    // 获取当前会话对应的 chatId
                    const sessionId = event.properties?.sessionID;
                    const chatId = agentManager.getChatIdBySessionId(sessionId);
                    if (!chatId) {
                        console.warn(`[Feishu] 未找到会话 ${sessionId} 对应的 chatId`);
                        return false;
                    }
                    // 将 title 和 content 合并为一条纯文本消息（移除 markdown 格式）
                    const plainContent = content.replace(/\*\*/g, ''); // 移除 ** 标记
                    return await sendCardMessage(chatManager, chatId, plainContent, title);
                },
                notifyWebhook: async (title, content) => {
                    return await sendWebhookMessage(title, content);
                },
                chatManager, agentManager
            });
        }
    }
})().catch(console.error)
import * as lark from '@larksuiteoapi/node-sdk';
import { createOpencodeClient } from "@opencode-ai/sdk"
import {
    handleFeishuMessage,sendCardMessage
} from '../../feishu-bot/message/index.js';
import { createFeishuWSClient } from '../../feishu-bot/client/index.js';
import { FeishuConfig } from '../../feishu-bot/config.js';
import { createAgentManager, OpencodeAgent } from '../../feishu-bot/agent/index.js';


const baseConfig = {
    appId: 'cli_a9059178d1b8dcd1',
    appSecret: 'utn16AUDhHarUUWY2yaZScMX4OJNBY4K'
};

const feishuClient = new lark.Client(baseConfig);

const opencodeClient = createOpencodeClient({
  baseUrl: "http://127.0.0.1:4096",
})

console.log(`opencode sessions  ${opencodeClient}`)

// 创建 Agent 策略实例
const agent = new OpencodeAgent(opencodeClient);

// 创建 Agent 管理器（封装 sessionMap 和 processingMessages）
const agentManager = createAgentManager({
    agent,
    processingTimeout: FeishuConfig.messageConfig.processingTimeout,
    messageIdTtl: FeishuConfig.messageConfig.messageIdTtl,
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

feishuWSClient.start((chatId, userMessage) => {
    return handleFeishuMessage(chatId, userMessage, {
        channelClient: feishuClient,
        agentManager
    });
});



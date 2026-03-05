import * as lark from '@larksuiteoapi/node-sdk';
import { createOpencodeClient } from "@opencode-ai/sdk"
import {
    handleFeishuMessage
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
    messageIdTtl: FeishuConfig.messageConfig.messageIdTtl
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



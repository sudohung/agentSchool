import * as lark from '@larksuiteoapi/node-sdk';
import { createOpencode, createOpencodeClient } from "@opencode-ai/sdk"
import {
    handleFeishuMessage,
    sendEventNotification,
    sendErrorMessage
} from '../../feishu-bot/message/index.js';
import { createFeishuWSClient } from '../../feishu-bot/client/index.js';
import { FeishuConfig } from '../../feishu-bot/config.js';


const baseConfig = {
    appId: 'cli_a9059178d1b8dcd1',
    appSecret: 'utn16AUDhHarUUWY2yaZScMX4OJNBY4K'
};

// 存储会话映射，用于双向通信
const sessionMap = new Map();
// 防重处理标记
const processingMessages = new Set();

const feishuClient = new lark.Client(baseConfig);

const opencodeClient = createOpencodeClient({
  baseUrl: "http://127.0.0.1:4096",
})

console.log(`opencode sessions  ${opencodeClient}`)



// 创建 WebSocket feishu 客户端
// 创建飞书长连接客户端实例
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
        agentClient: opencodeClient,
        sessionMap,
        processingMessages
    });
});



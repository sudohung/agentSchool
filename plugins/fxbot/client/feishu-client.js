import * as lark from '@larksuiteoapi/node-sdk';
import { createOpencode, createOpencodeClient } from "@opencode-ai/sdk"
import {
    sendThinkingMessage,
    sendErrorMessage,
    sendAIResponse,
    sendEmptyResponse,
    updateMessage,
    recallMessage,
    sendEventNotification
} from '../../feishu-bot/message/index.js';
import { createFeishuWSClient } from '../../feishu-bot/client/index.js';
import { FeishuConfig } from '../../feishu-bot/config.js';


const baseConfig = {
    appId: 'cli_a9059178d1b8dcd1',
    appSecret: 'utn16AUDhHarUUWY2yaZScMX4OJNBY4K'
};

// 存储会话映射，用于双向通信
const sessionMap = new Map();

const feishuClient = new lark.Client(baseConfig);
//const opencodeClient = await createOpencode({
//  hostname: "127.0.0.1",
//  port: 5096,
//  config: {
//    model: "CodingPlanX/qwen3.5-plus",
//  },
//})

const opencodeClient = createOpencodeClient({
  baseUrl: "http://127.0.0.1:4096",
})

console.log(`opencode sessions  ${opencodeClient}`)


/**
 * 处理飞书收到的消息（转发给 OpenCode AI）
 */
async function handleFeishuMessage(chatId, userMessage) {
    // 创建唯一标识防止重复处理
    const messageKey = `${chatId}:${userMessage}`;

    try {

        console.log(`[feishu -> OpenCode] 处理消息：${userMessage}`);

        // 先发送思考状态
        const res = await sendThinkingMessage(feishuClient, chatId);
        console.log(`[Feishu -> OpenCode] 处理think消息：${JSON.stringify(res)}`);


        // 创建或获取会话
        let sessionId = sessionMap.get(chatId);
        if (!sessionId) {
            const session = await opencodeClient.session.create({
                body: { title: `feishu-${chatId}-${Date.now()}` }
            });

        // 打印完整的 session 结构用于调试
        if (FeishuConfig.isDebugEnabled()) {
            console.log(`${FeishuConfig.getLogPrefix()} === Session 完整结构 ===`);
            console.log(`${FeishuConfig.getLogPrefix()} session:`, JSON.stringify(session, null, 2));
            console.log(`${FeishuConfig.getLogPrefix()} session.id:`, session.id);
            console.log(`${FeishuConfig.getLogPrefix()} session.data:`, session.data);
            console.log(`${FeishuConfig.getLogPrefix()} session.path:`, session.path);
            console.log(`${FeishuConfig.getLogPrefix()} ======================`);
        }

            // 正确获取 session ID，检查多种可能的字段名
            sessionId = session.id || session.data?.id || session.path?.id;

            if (!sessionId) {
                console.error('[Feishu] Session 创建成功但未获取到 ID:', session);
                throw new Error('无法获取 Session ID');
            }

            console.log(`[feishu] 创建新会话：${sessionId}`);
            sessionMap.set(chatId, sessionId);
        }

        // 发送消息给 OpenCode AI
        const result = await opencodeClient.session.prompt({
            path: { id: sessionId },
            body: {
                parts: [{ type: "text", text: userMessage }],
            },
        });

        // 打印完整的 result 结构用于调试

            // 提取 AI 回复
            const { aiResponse, otherParts } = extractAIResponse(result, userMessage);

        // 回复到飞书
//            recallMessage(feishuClient, res.data.message_id);
            await sendAIResponse(feishuClient, chatId, userMessage, JSON.stringify(result.data));
//        await updateMessage(feishuClient, res.data.message_id, userMessage, aiResponse);

    } catch (error) {
        console.error(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 处理失败:`, error.message);
        console.error(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 处理失败 stack:`, error.stack);
        if (FeishuConfig.isDebugEnabled()) {
            console.error(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 错误详情:`, error);
        }
        await sendErrorMessage(feishuClient, chatId, error.message);
    } finally {
        // 清理处理标记
        setTimeout(() => {
            console.log(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 清理处理标记: ${messageKey}`);
        }, FeishuConfig.messageConfig.processingTimeout); // 使用配置中的超时时间
    }
}

// 创建 WebSocket feishu 客户端
// 创建飞书长连接客户端实例
const feishuWSClient = createFeishuWSClient({
    appId: FeishuConfig.appId,
    appSecret: FeishuConfig.appSecret,
    logLevel: FeishuConfig.logConfig.level,
    messageExpiryTime: FeishuConfig.messageConfig.messageExpiryTime,
    messageIdTtl: FeishuConfig.messageConfig.messageIdTtl
});
feishuWSClient.start(handleFeishuMessage);

//const wsClient = new lark.WSClient({...baseConfig, loggerLevel: lark.LoggerLevel.debug});

// 飞书客户端链接
//wsClient.start({
//  // 处理「接收消息」事件，事件类型为 im.message.receive_v1
//  eventDispatcher: new lark.EventDispatcher({}).register({
//    'im.message.receive_v1': async (data) => {
//      const {
//        message: { chat_id, content}
//      } = data;
//
//      // 解析用户消息
//      const userMessage = JSON.parse(content).text;
//
//      // 调用 OpenCode SDK 处理消息
//      let aiResponse = '新年好';
//
//      // 调用 OpenCode SDK 处理消息
//      await sendAIResponse(feishuClient, chat_id, userMessage, aiResponse);
//
//      // 示例操作：接收消息后，调用「发送消息」API 进行消息回复。
//      await feishuClient.im.v1.message.create({
//        params: {
//          receive_id_type: "chat_id"
//        },
//        data: {
//          receive_id: chat_id,
//          content: lark.messageCard.defaultCard({
//            title: `回复：${userMessage}`,
//            content: aiResponse
//          }),
//          msg_type: 'interactive'
//        }
//      });
//    }
//  })
//});


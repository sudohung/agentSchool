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

const baseConfig = {
    appId: 'cli_a9059178d1b8dcd1',
    appSecret: 'utn16AUDhHarUUWY2yaZScMX4OJNBY4K'
};

const larkClient = new lark.Client(baseConfig);
//const opencodeClient = await createOpencode({
//  hostname: "127.0.0.1",
//  port: 5096,
//  config: {
//    model: "CodingPlanX/qwen3.5-plus",
//  },
//})

const opencodeClient = createOpencodeClient({
  baseUrl: "http://localhost:4096",
})

console.log(`opencode sessions  ${opencodeClient}`)

// 创建 WebSocket feishu 客户端
const wsClient = new lark.WSClient({...baseConfig, loggerLevel: lark.LoggerLevel.debug});

// 飞书客户端链接
wsClient.start({
  // 处理「接收消息」事件，事件类型为 im.message.receive_v1
  eventDispatcher: new lark.EventDispatcher({}).register({
    'im.message.receive_v1': async (data) => {
      const {
        message: { chat_id, content}
      } = data;
      
      // 解析用户消息
      const userMessage = JSON.parse(content).text;

      // 调用 OpenCode SDK 处理消息
      let aiResponse = '新年好';

      // 调用 OpenCode SDK 处理消息
      await sendAIResponse(larkClient, chat_id, userMessage, aiResponse);

      // 示例操作：接收消息后，调用「发送消息」API 进行消息回复。
      await larkClient.im.v1.message.create({
        params: {
          receive_id_type: "chat_id"
        },
        data: {
          receive_id: chat_id,
          content: lark.messageCard.defaultCard({
            title: `回复：${userMessage}`,
            content: aiResponse
          }),
          msg_type: 'interactive'
        }
      });
    }
  })
});


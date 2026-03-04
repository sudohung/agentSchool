import * as lark from '@larksuiteoapi/node-sdk';
import { createOpencodeClient } from "@opencode-ai/sdk"

const baseConfig = {
    appId: 'cli_a9059178d1b8dcd1',
    appSecret: 'utn16AUDhHarUUWY2yaZScMX4OJNBY4K'
};

const larkClient = new lark.Client(baseConfig);

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


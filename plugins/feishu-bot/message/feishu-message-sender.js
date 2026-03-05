/**
 * 飞书消息发送模块
 * 负责处理和发送各种类型的飞书消息
 */

import * as lark from '@larksuiteoapi/node-sdk';

/**
 * 飞书客户端配置类型
 * @typedef {Object} FeishuConfig
 * @property {string} appId - 应用 ID
 * @property {string} appSecret - 应用密钥
 */

/**
 * 消息卡片内容类型
 * @typedef {Object} MessageContent
 * @property {string} title - 消息标题
 * @property {string} content - 消息内容
 */

/**
 * 创建飞书客户端实例
 * @param {FeishuConfig} config - 飞书客户端配置
 * @returns {lark.Client} 飞书客户端实例
 */
export function createFeishuClient(config) {
    return new lark.Client(config);
}

/**
 * 发送飞书交互式卡片消息
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} chatId - 聊天 ID
 * @param {MessageContent} messageContent - 消息内容对象 {title, content}
 * @returns {Promise<Object>} 飞书 API 响应结果，格式：{ code, msg, data: { message_id } }
 */
async function sendInteractiveCard(client, chatId, { title, content }) {
    try {
        const res = await client.im.v1.message.create({
            params: {
                receive_id_type: "chat_id"
            },
            data: {
                receive_id: chatId,
                content: lark.messageCard.defaultCard({
                    title: title,
                    content: content
                }),
                msg_type: 'interactive'
            }
        });
        console.log(`[Feishu] 消息已发送：${title}`);
        // 返回标准的响应格式
        return {
            code: res.code || 0,
            msg: res.msg || 'success',
            data: {
                message_id: res.data?.message_id || ''
            }
        };
    } catch (error) {
        console.error(`[Feishu] 发送消息失败:`, error.message);
        throw error;
    }
}

/**
 * 发送飞书文本消息
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} chatId - 聊天 ID
 * @param {string} text - 文本内容
 * @returns {Promise<Object>} 飞书 API 响应结果，格式：{ code, msg, data: { message_id } }
 */
export async function sendTextMessage(client, chatId, text) {
    try {
        const res = await client.im.v1.message.create({
            params: {
                receive_id_type: "chat_id"
            },
            data: {
                receive_id: chatId,
                content: JSON.stringify({ text }),
                msg_type: 'text'
            }
        });
        console.log(`[Feishu] 文本消息已发送`);
        return {
            code: res.code || 0,
            msg: res.msg || 'success',
            data: {
                message_id: res.data?.message_id || ''
            }
        };
    } catch (error) {
        console.error(`[Feishu] 发送文本消息失败:`, error.message);
        throw error;
    }
}

/**
 * 发送飞书交互式卡片消息（带默认标题）
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} chatId - 聊天 ID
 * @param {string} content - 消息内容
 * @param {string} [title='消息通知'] - 可选的标题，默认为'消息通知'
 * @returns {Promise<Object>} 飞书 API 响应结果，格式：{ code, msg, data: { message_id } }
 */
export async function sendCardMessage(client, chatId, content, title = '消息通知') {
    return await sendInteractiveCard(client, chatId, { title, content });
}

/**
 * 发送思考状态消息
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} chatId - 聊天 ID
 * @returns {Promise<Object>} 飞书 API 响应结果，格式：{ code, msg, data: { message_id } }
 */
export async function sendThinkingMessage(client, chatId) {
    return await sendInteractiveCard(client, chatId, {
        title: 'Thinking...',
        content: '正在处理您的请求...'
    });
}

/**
 * 发送错误消息
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} chatId - 聊天 ID
 * @param {string} errorMessage - 错误信息
 * @param {string} [prefix='❌ 处理失败'] - 错误前缀
 * @returns {Promise<Object>} 飞书 API 响应结果，格式：{ code, msg, data: { message_id } }
 */
export async function sendErrorMessage(client, chatId, errorMessage, prefix = '❌ 处理失败') {
    return await sendInteractiveCard(client, chatId, {
        title: prefix,
        content: `错误：${errorMessage}`
    });
}

/**
 * 发送 AI 回复消息
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} chatId - 聊天 ID
 * @param {string} userMessage - 用户原始消息
 * @param {string} aiResponse - AI 回复内容
 * @returns {Promise<Object>} 飞书 API 响应结果，格式：{ code, msg, data: { message_id } }
 */
export async function sendAIResponse(client, chatId, userMessage, aiResponse) {
    const truncatedMessage = userMessage.length > 20 
        ? `${userMessage.substring(0, 20)}...` 
        : userMessage;
    
    return await sendInteractiveCard(client, chatId, {
        title: `回复：${truncatedMessage}`,
        content: aiResponse
    });
}

/**
 * 发送事件通知消息
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} chatId - 聊天 ID
 * @param {string} eventType - 事件类型
 * @param {string} eventDescription - 事件描述
 * @returns {Promise<Object>} 飞书 API 响应结果，格式：{ code, msg, data: { message_id } }
 */
export async function sendEventNotification(client, chatId, eventType, eventDescription) {
    return await sendInteractiveCard(client, chatId, {
        title: `📢 ${eventType}`,
        content: eventDescription
    });
}

/**
 * 发送空消息响应
 * 用于某些不需要返回内容的场景
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} chatId - 聊天 ID
 * @returns {Promise<Object>} 飞书 API 响应结果，格式：{ code, msg, data: { message_id } }
 */
export async function sendEmptyResponse(client, chatId) {
    return await sendInteractiveCard(client, chatId, {});
}

/**
 * 更新飞书消息
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} messageId - 要编辑的消息 ID
 * @param {string} msgType - 消息类型（'text' 或 'interactive'）
 * @param {string|Object} content - 消息内容
 *        - 当 msgType 为 'text' 时，传入字符串文本内容
 *        - 当 msgType 为 'interactive' 时，传入卡片内容对象 {title, content}
 * @returns {Promise<Object>} 飞书 API 响应结果
 */
export async function updateMessage(client, messageId, msgType, userMessage, content) {
    try {
//        const msgType = 'interactive';
        // 根据消息类型处理内容
        let messageContent;
        let res = {}
        if (msgType === 'text') {
            // 文本消息：将字符串内容转换为 JSON
            messageContent = JSON.stringify({ text: content });

            // 调用飞书 API 更新消息
            res = await client.im.v1.message.update({
                path: {
                    message_id: messageId
                },
                data: {
                    msg_type: msgType,
                    content: messageContent
                }
            });

        } else if (msgType === 'interactive') {
            const truncatedMessage = userMessage.length > 20
                ? `${userMessage.substring(0, 20)}...`
                : userMessage;

            // 交互式卡片：使用默认卡片格式
            const { title = truncatedMessage, content: cardContent } = content;
            messageContent = lark.messageCard.defaultCard({
                title: `回复：${truncatedMessage}`,
                content: content
            });

            res = client.im.v1.message.patch({
                path: {
                    message_id:messageId,
                },
                data: {
                    content:messageContent,
                },
            }
            ).then(res => {
                console.log(res);
            }).catch(e => {
                console.error(JSON.stringify(e.response.data, null, 4));
            });

        } else {
            throw new Error(`不支持的消息类型：${msgType}`);
        }
        
        console.log(`[Feishu] 消息编辑成功：${messageId}`);
        return res;
    } catch (error) {
        console.error(`[Feishu] 消息编辑失败:`, error.message);
        throw error;
    }
}

/**
 * 撤回飞书消息
 * @param {lark.Client} client - 飞书客户端实例
 * @param {string} messageId - 要撤回的消息 ID
 * @returns {Promise<Object>} 飞书 API 响应结果
 */

export async function recallMessage(client, messageId) {
  try {
    const response = await client.im.v1.message.delete({
      path: {
        message_id: messageId
      }
    });

    if (response.code === 0) {
      console.log('消息撤回成功');
    } else {
      console.log(`消息撤回失败: ${response.msg}`);
    }
  } catch (error) {
    console.error('调用接口失败:', error);
  }
}

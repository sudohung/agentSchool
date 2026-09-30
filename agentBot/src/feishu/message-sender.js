/**
 * 飞书消息发送模块
 * 统一封装文本/卡片消息的发送、更新、撤回
 * 与旧版差异：patch 更新正确 await、发送失败带重试、防御式参数校验
 */

import * as lark from '@larksuiteoapi/node-sdk';
import { MsgType, LogPrefix } from '../constants.js';

/** 发送瞬时错误重试次数 */
const SEND_RETRIES = 2;
/** 重试基础等待（毫秒），指数退避 */
const RETRY_BASE_DELAY = 500;

/**
 * 带重试的执行器（网络/5xx 类瞬时错误）
 * @param {Function} fn - 异步操作
 * @param {string} action - 操作描述（日志用）
 */
async function withRetry(fn, action) {
    let lastError;
    for (let attempt = 0; attempt <= SEND_RETRIES; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
            const status = error?.response?.status;
            const retryable = !status || status >= 500;
            if (!retryable || attempt === SEND_RETRIES) {
                break;
            }
            console.warn(`${LogPrefix.SENDER} ${action} 失败（第 ${attempt + 1} 次），准备重试: ${error.message}`);
            await new Promise((r) => setTimeout(r, RETRY_BASE_DELAY * 2 ** attempt));
        }
    }
    console.error(`${LogPrefix.SENDER} ${action} 最终失败: ${lastError.message}`);
    throw lastError;
}

/**
 * 截断用户消息用于卡片标题
 * @param {string} text - 原始文本
 * @param {number} [max=20]
 */
function truncate(text, max = 20) {
    if (!text) return '';
    return text.length > max ? `${text.substring(0, max)}...` : text;
}

/**
 * 发送交互式卡片消息
 * @param {import('./chat-service.js').ChatService} chatService
 * @param {string} chatId - 聊天 ID
 * @param {string} title - 卡片标题
 * @param {string} content - 卡片内容
 * @returns {Promise<{code:number, data:{message_id:string}}>}
 */
export async function sendCardMessage(chatService, chatId, title, content) {
    if (!chatId) throw new Error('发送卡片失败：chatId 为空');
    const client = chatService.getClient();
    return await withRetry(async () => {
        const res = await client.im.v1.message.create({
            params: { receive_id_type: 'chat_id' },
            data: {
                receive_id: chatId,
                content: lark.messageCard.defaultCard({ title, content }),
                msg_type: MsgType.INTERACTIVE,
            },
        });
        return {
            code: res.code || 0,
            data: { message_id: res.data?.message_id || '' },
        };
    }, `发送卡片到 ${chatId}`);
}

/**
 * 发送文本消息
 * @returns {Promise<{code:number, data:{message_id:string}}>}
 */
export async function sendTextMessage(chatService, chatId, text) {
    if (!chatId) throw new Error('发送文本失败：chatId 为空');
    const client = chatService.getClient();
    return await withRetry(async () => {
        const res = await client.im.v1.message.create({
            params: { receive_id_type: 'chat_id' },
            data: {
                receive_id: chatId,
                content: JSON.stringify({ text }),
                msg_type: MsgType.TEXT,
            },
        });
        return {
            code: res.code || 0,
            data: { message_id: res.data?.message_id || '' },
        };
    }, `发送文本到 ${chatId}`);
}

/** 发送"思考中"占位卡片 */
export async function sendThinkingMessage(chatService, chatId) {
    return await sendCardMessage(chatService, chatId, 'Thinking...', '正在处理您的请求...');
}

/** 发送错误卡片 */
export async function sendErrorMessage(chatService, chatId, errorMessage, title = '❌ 处理失败') {
    return await sendCardMessage(chatService, chatId, title, `错误：${errorMessage}`);
}

/**
 * 更新已发送消息
 * @param {string} messageId - 消息 ID
 * @param {'text'|'interactive'} msgType - 消息类型
 * @param {string} userMessage - 用户原始消息（卡片标题用）
 * @param {string|{title,content}} content - 新内容
 */
export async function updateMessage(chatService, messageId, msgType, userMessage, content) {
    if (!messageId) throw new Error('更新消息失败：messageId 为空');
    const client = chatService.getClient();

    return await withRetry(async () => {
        if (msgType === MsgType.TEXT) {
            return await client.im.v1.message.update({
                path: { message_id: messageId },
                data: {
                    msg_type: MsgType.TEXT,
                    content: JSON.stringify({ text: content }),
                },
            });
        }

        if (msgType === MsgType.INTERACTIVE) {
            const { title = truncate(userMessage), content: cardContent = '' } =
                typeof content === 'object' && content !== null ? content : { content };
            return await client.im.v1.message.patch({
                path: { message_id: messageId },
                data: {
                    content: lark.messageCard.defaultCard({
                        title: `回复：${truncate(userMessage)}`,
                        content: cardContent || title,
                    }),
                },
            });
        }

        throw new Error(`不支持的消息类型：${msgType}`);
    }, `更新消息 ${messageId}`);
}

/**
 * 撤回消息（尽力而为，不抛出）
 */
export async function recallMessage(chatService, messageId) {
    if (!messageId) return false;
    try {
        const res = await chatService.getClient().im.v1.message.delete({
            path: { message_id: messageId },
        });
        return res.code === 0;
    } catch (error) {
        console.error(`${LogPrefix.SENDER} 消息撤回失败: ${error.message}`);
        return false;
    }
}

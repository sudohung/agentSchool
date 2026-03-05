/**
 * 飞书消息处理模块
 * 负责处理飞书收到的消息并转发给 OpenCode AI
 */

import { FeishuConfig } from '../config.js';
import { extractAIResponse } from './message-parser.js';
import {
    sendThinkingMessage,
    sendErrorMessage,
    updateMessage
} from './index.js';

/**
 * 消息处理器配置
 * @typedef {Object} MessageHandlerConfig
 * @property {Object} channelClient - 飞书客户端
 * @property {Object} agentClient - OpenCode 客户端
 * @property {Map} sessionMap - 会话映射，用于双向通信
 * @property {Set} processingMessages - 防重处理标记
 */

/**
 * 处理飞书收到的消息（转发给 OpenCode AI）
 * @param {string} chatId - 聊天 ID
 * @param {string} userMessage - 用户消息
 * @param {Object} config - 配置对象
 * @param {Object} config.channelClient - 飞书客户端
 * @param {Object} config.agentClient - OpenCode 客户端
 * @param {Map} config.sessionMap - 会话映射
 * @param {Set} config.processingMessages - 防重处理标记
 * @returns {Promise<void>}
 */
export async function handleFeishuMessage(chatId, userMessage, { channelClient, agentClient, sessionMap, processingMessages }) {
    // 创建唯一标识防止重复处理
    const messageKey = `${chatId}:${userMessage}`;
    if (processingMessages.has(messageKey)) {
        console.log(`[Feishu] 消息已在处理中，跳过：${messageKey}`);
        return;
    }

    try {
        processingMessages.add(messageKey);
        console.log(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 处理消息：${userMessage}`);

        // 先发送思考状态
        const res = await sendThinkingMessage(channelClient, chatId);
        console.log(`[Feishu -> OpenCode] 处理 think 消息：${JSON.stringify(res)}`);


        // 创建或获取会话
        let sessionId = sessionMap.get(chatId);
        if (!sessionId) {
            const session = await agentClient.session.create({
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
            
            console.log(`${FeishuConfig.getLogPrefix()} 创建新会话：${sessionId}`);
            sessionMap.set(chatId, sessionId);
        }
        
        // 发送消息给 OpenCode AI
        const result = await agentClient.session.prompt({
            path: { id: sessionId },
            body: {
                parts: [{ type: "text", text: userMessage }],
            },
        });
        
        // 提取 AI 回复
        const { aiResponse, otherParts } = extractAIResponse(result, userMessage);

        // 回复到飞书
        await updateMessage(channelClient, res.data.message_id, userMessage, aiResponse);
        
    } catch (error) {
        console.error(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 处理失败:`, error.message);
        console.error(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 处理失败stack:`, error.stack);
        if (FeishuConfig.isDebugEnabled()) {
            console.error(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 错误详情:`, error);
        }
        await sendErrorMessage(channelClient, chatId, error.message);
    } finally {
        // 清理处理标记
        setTimeout(() => {
            processingMessages.delete(messageKey);
        }, FeishuConfig.messageConfig.processingTimeout);
    }
}

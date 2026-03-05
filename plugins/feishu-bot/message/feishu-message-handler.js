/**
 * 飞书消息处理模块
 * 负责处理飞书收到的消息并转发给 Agent AI
 * 
 * 使用 AgentManager 统一管理会话和消息去重，支持切换不同的 Agent 实现
 */

import { FeishuConfig } from '../config.js';
import { extractAIResponse } from './message-parser.js';
import {
    sendThinkingMessage,
    sendErrorMessage,
    updateMessage
} from './index.js';
import { AgentManager } from '../agent/agent-manager.js';

/**
 * 消息处理器配置
 * @typedef {Object} MessageHandlerConfig
 * @property {Object} channelClient - 飞书客户端
 * @property {AgentManager} agentManager - Agent 管理器（封装了 agentClient、sessionMap、processingMessages）
 */

/**
 * 处理飞书收到的消息（转发给 Agent AI）
 * @param {string} chatId - 聊天 ID
 * @param {string} userMessage - 用户消息
 * @param {Object} config - 配置对象
 * @param {Object} config.channelClient - 飞书客户端
 * @param {AgentManager} config.agentManager - Agent 管理器
 * @returns {Promise<void>}
 */
export async function handleFeishuMessage(chatId, userMessage, { channelClient, agentManager }) {
    // 检查消息是否正在处理中（去重）
    if (agentManager.isProcessing(chatId, userMessage)) {
        console.log(`[Feishu] 消息已在处理中，跳过：${chatId}:${userMessage}`);
        return;
    }

    try {
        // 标记消息开始处理
        agentManager.markProcessing(chatId, userMessage);
        console.log(`${FeishuConfig.getLogPrefix()}[-> Agent] 处理消息：${userMessage}`);

        // 先发送思考状态
        const res = await sendThinkingMessage(channelClient, chatId);
        console.log(`[Feishu -> Agent] 处理 think 消息：${JSON.stringify(res)}`);

        // 获取或创建会话（AgentManager 内部管理 sessionMap）
        const sessionId = await agentManager.getSession(chatId);
        console.log(`${FeishuConfig.getLogPrefix()} 使用会话：${sessionId}`);

        if (FeishuConfig.isDebugEnabled()) {
            console.log(`${FeishuConfig.getLogPrefix()} 使用会话：${sessionId}`);
        }
        
        // 发送消息给 Agent AI
        const result = await agentManager.sendMessage(sessionId, userMessage);
        
        // 提取 AI 回复
        const { aiResponse, otherParts } = extractAIResponse(result, userMessage);

        // 回复到飞书
        await updateMessage(channelClient, res.data.message_id, "interactive",userMessage, aiResponse);
        
    } catch (error) {
        console.error(`${FeishuConfig.getLogPrefix()}[-> Agent] 处理失败:`, error.message);
        console.error(`${FeishuConfig.getLogPrefix()}[-> Agent] 处理失败 stack:`, error.stack);
        if (FeishuConfig.isDebugEnabled()) {
            console.error(`${FeishuConfig.getLogPrefix()}[-> Agent] 错误详情:`, error);
        }
        await sendErrorMessage(channelClient, chatId, error.message);
    } finally {
        // 标记消息处理完成（延迟清理去重标记）
        agentManager.markCompleted(chatId, userMessage);
    }
}

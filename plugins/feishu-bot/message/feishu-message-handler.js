/**
 * 飞书消息处理模块
 * 负责处理飞书收到的消息并转发给 Agent AI
 * 
 * 使用 AgentManager 统一管理会话和消息去重，支持切换不同的 Agent 实现
 * 使用责任链模式处理命令
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
 * 命令处理器接口
 */
class CommandHandler {
    setNext(handler) {
        this.nextHandler = handler;
        return handler;
    }
    
    async handle(chatId, message, context) {
        if (this.nextHandler) {
            return await this.nextHandler.handle(chatId, message, context);
        }
        return null;
    }
}

/**
 * /new 命令处理器 - 重置会话
 */
class NewCommandHandler extends CommandHandler {
    async handle(chatId, message, context) {
        if (message.trim() === '/new') {
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /new 命令，重置会话`);
            const newSessionId = await context.agentManager.resetSession(chatId);
            return {
                type: 'command',
                action: 'new_session',
                sessionId: newSessionId,
                message: `已创建新会话: ${newSessionId}`
            };
        }
        return super.handle(chatId, message, context);
    }
}

/**
 * /instant:xxx 命令处理器 - 切换 Agent
 */
class InstantCommandHandler extends CommandHandler {
    async handle(chatId, message, context) {
        const instantMatch = message.trim().match(/^\/instant:(\S+)$/);
        if (instantMatch) {
            const agentKey = instantMatch[1];
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /instant 命令，切换 Agent: ${agentKey}`);
            const success = context.agentManager.setCurrentAgent(agentKey);
            const agentName = context.agentManager.getCurrentAgentName();
            return { 
                type: 'command', 
                action: 'switch_agent', 
                success,
                agentKey,
                agentName,
                message: success 
                    ? `已切换 Agent: ${agentName}`
                    : `切换失败，未找到 Agent: ${agentKey}`
            };
        }
        return super.handle(chatId, message, context);
    }
}

/**
 * /sessions 命令处理器 - 列出当前 Agent 的所有会话
 */
class SessionsCommandHandler extends CommandHandler {
    async handle(chatId, message, context) {
        if (message.trim() === '/sessions') {
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /sessions 命令，列出会话`);
            try {
                const sessions = await context.agentManager.listSessions();
                const agentName = context.agentManager.getCurrentAgentName();
                
                if (!sessions || sessions.length === 0) {
                    return { 
                        type: 'command', 
                        action: 'list_sessions', 
                        message: `当前 Agent (${agentName}) 没有会话`
                    };
                }
                
                const sessionList = sessions.slice(0, 10).map(s => {
                    const id = s.id || s.sessionId || 'unknown';
                    const title = s.title || '无标题';
                    const status = s.status || s.state || '';
                    return `• ${title} (${id}) ${status ? `- ${status}` : ''}`;
                }).join('\n');
                
                const more = sessions.length > 10 ? `\n... 还有 ${sessions.length - 10} 个会话` : '';
                
                return { 
                    type: 'command', 
                    action: 'list_sessions', 
                    message: `当前 Agent (${agentName}) 会话列表 (${sessions.length}):\n${sessionList}${more}`
                };
            } catch (error) {
                console.error(`${FeishuConfig.getLogPrefix()} 列出会话失败:`, error.message);
                return { 
                    type: 'command', 
                    action: 'list_sessions', 
                    message: `列出会话失败: ${error.message}`
                };
            }
        }
        return super.handle(chatId, message, context);
    }
}

/**
 * /session:xxxx 命令处理器 - 切换会话并显示最新消息
 */
class SessionCommandHandler extends CommandHandler {
    async handle(chatId, message, context) {
        const sessionMatch = message.trim().match(/^\/session:(\S+)$/);
        if (sessionMatch) {
            const targetSessionId = sessionMatch[1];
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /session 命令，切换会话: ${targetSessionId}`);
            
            try {
                // 切换会话
                context.agentManager.switchSession(chatId, targetSessionId);
                
                // 获取会话消息
                const messages = await context.agentManager.getSessionMessages(targetSessionId);
                const agentName = context.agentManager.getCurrentAgentName();
                
                if (!messages || messages.length === 0) {
                    return { 
                        type: 'command', 
                        action: 'switch_session', 
                        message: `已切换到会话: ${targetSessionId}\n(暂无消息)`
                    };
                }
                
                // 取最新的10条消息
                const recentMessages = messages.slice(-10);
                const messageList = recentMessages.map((m, idx) => {
                    const role = m.info?.role || m.role || 'unknown';
                    const content = this.extractMessageContent(m);
                    const preview = content.length > 80 ? content.substring(0, 80) + '...' : content;
                    return `${idx + 1}. [${role}]: ${preview}`;
                }).join('\n');
                
                return { 
                    type: 'command', 
                    action: 'switch_session', 
                    message: `已切换到会话: ${targetSessionId}\n当前 Agent: ${agentName}\n最新消息:\n${messageList}`
                };
            } catch (error) {
                console.error(`${FeishuConfig.getLogPrefix()} 切换会话失败:`, error.message);
                return { 
                    type: 'command', 
                    action: 'switch_session', 
                    message: `切换会话失败: ${error.message}`
                };
            }
        }
        return super.handle(chatId, message, context);
    }
    
    extractMessageContent(msg) {
        if (msg.parts && Array.isArray(msg.parts)) {
            return msg.parts
                .filter(p => p.type === 'text')
                .map(p => p.text || '')
                .join('');
        }
        if (msg.content) {
            return typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
        }
        return '';
    }
}

/**
 * @mention 过滤器 - 移除消息开头的 @user_id_1
 */
class MentionFilterHandler extends CommandHandler {
    async handle(chatId, message, context) {
        // 检查消息是否以 @user_id_1 开头
        if (message.trim().startsWith('@user_id_1')) {
            console.log(`${FeishuConfig.getLogPrefix()} 移除消息中的 @user_id_1 mention`);
            // 移除开头的 @user_id_1 及其后的空格
            const cleanedMessage = message.replace(/^@user_id_1\s*/, '').trim();
            console.log(`${FeishuConfig.getLogPrefix()} 清理后的消息：${cleanedMessage}`);
            
            // 将清理后的消息传递给下一个处理器
            return await this.nextHandler.handle(chatId, cleanedMessage, context);
        }
        
        // 如果不包含 @user_id_1，直接传递给下一个处理器
        return super.handle(chatId, message, context);
    }
}

/**
 * AI 消息处理器 - 处理普通消息，调用 AI 生成回复
 */
class AIMessageHandler extends CommandHandler {
    async handle(chatId, message, context) {
        const { channelClient, agentManager } = context;
        
        console.log(`${FeishuConfig.getLogPrefix()} 执行 AI 消息处理`);
        
        // 发送思考状态
//        const res = await sendThinkingMessage(channelClient, chatId);
//        console.log(`[Feishu -> Agent] 处理 think 消息：${JSON.stringify(res)}`);
        
        // 获取或创建会话
        const sessionId = await agentManager.getSession(chatId);
        console.log(`${FeishuConfig.getLogPrefix()} 使用会话：${sessionId}`);
        
        if (FeishuConfig.isDebugEnabled()) {
            console.log(`${FeishuConfig.getLogPrefix()} 使用会话：${sessionId}`);
        }
        
        // 发送消息给 Agent AI
        const result = await agentManager.sendMessage(sessionId, message);
        
        // 提取 AI 回复
        const { aiResponse, otherParts } = extractAIResponse(result, message);
        
//        // 回复到飞书
//        await updateMessage(channelClient, res.data.message_id, "interactive", message, aiResponse);
        
        return { 
            type: 'ai_response', 
            action: 'message_processed',
            sessionId,
            message: aiResponse
        };
    }
}

/**
 * 构建消息处理责任链
 */
function buildMessageChain() {
    const mentionFilterHandler = new MentionFilterHandler();
    const newHandler = new NewCommandHandler();
    const instantHandler = new InstantCommandHandler();
    const sessionsHandler = new SessionsCommandHandler();
    const sessionHandler = new SessionCommandHandler();
    const aiHandler = new AIMessageHandler();
    
    mentionFilterHandler.setNext(newHandler);
    newHandler.setNext(instantHandler);
    instantHandler.setNext(sessionsHandler);
    sessionsHandler.setNext(sessionHandler);

    // AIMessageHandler 必须是最后处理的 ->
    sessionHandler.setNext(aiHandler);
    return newHandler;
}

const messageChain = buildMessageChain();

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
 * @param {Object} content - 消息内容对象
 * @param {Object} config - 配置对象
 * @param {Object} config.channelClient - 飞书客户端
 * @param {AgentManager} config.agentManager - Agent 管理器
 * @returns {Promise<void>}
 */
export async function handleFeishuMessage(chatId, userMessage, content, { channelClient, agentManager }) {
    // 检查消息是否正在处理中（去重）
    if (agentManager.isProcessing(chatId, userMessage)) {
        console.log(`[Feishu] 消息已在处理中，跳过：${chatId}:${userMessage}`);
        return;
    }

    try {
        // 标记消息开始处理
        agentManager.markProcessing(chatId, userMessage);
        console.log(`${FeishuConfig.getLogPrefix()}[-> Agent] 处理消息：${userMessage}`);

        // 思考中
        const res = await sendThinkingMessage(channelClient, chatId);

        // 通过责任链处理命令
        const commandResult = await messageChain.handle(chatId, userMessage, { agentManager });
        
        // 如果是命令，直接返回结果
        if (commandResult) {
            console.log(`${FeishuConfig.getLogPrefix()}:${agentManager.getCurrentAgentName()} messageId=${res.data.message_id} ;msg=${userMessage};命令处理结果: ${JSON.stringify(commandResult)}`);

            await updateMessage(channelClient, res.data.message_id, "interactive", userMessage, commandResult.message);
            
            // 如果是 /new 命令，后续消息应该使用新会话
            // 如果是 /instant 命令，sendMessage 会自动使用新的 agent
            agentManager.markCompleted(chatId, userMessage);
            return;
        }
        console.error(`${FeishuConfig.getLogPrefix()} 命令处理失败:`, commandResult);

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

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
            console.log(`${FeishuConfig.getLogPrefix()} MentionFilterHandler message: ${message} `);
        // 检查消息是否包含有 @_user_1
        if (message.includes('@_user_1')) {
            console.log(`${FeishuConfig.getLogPrefix()} 移除消息中的 @_user_1 mention`);
            // 移除开头的 @user_id_1 及其后的空格
            const cleanedMessage = message.replace(/@_user_1\s*/g, '').trim();
            console.log(`${FeishuConfig.getLogPrefix()} 清理后的消息：${cleanedMessage}`);
            
            // 将清理后的消息传递给下一个处理器
            return super.handle(chatId, cleanedMessage, context);
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
        
        console.log(`${FeishuConfig.getLogPrefix()} 执行 AI 消息处理 message：${message}`);
        
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

    // mentionFilterHandler 必须在最前面，先移除 @_user_1 再匹配命令
    mentionFilterHandler.setNext(newHandler);
    newHandler.setNext(instantHandler);
    instantHandler.setNext(sessionsHandler);
    sessionsHandler.setNext(sessionHandler);

    // AIMessageHandler 必须是最后处理的 ->
    const aiHandler = new AIMessageHandler();
    sessionHandler.setNext(aiHandler);
    return mentionFilterHandler;
}

const messageChain = buildMessageChain();


/**
 * Context 过滤接口 - 拦截不同消息
 */
class ContextFilterHandler {
    setNext(handler) {
        this.nextHandler = handler;
        return handler;
    }

    async handle(messageContext, context) {
        if (this.nextHandler) {
            return await this.nextHandler.handle(messageContext, context);
        }
        return {
           type: 'default',
           text: '',
           raw: {},
           pass: true,
           reason: '过滤结束默认通过'
       };;
    }
}

/**
 * 文本消息内容处理器
 */
class TextFilterHandler extends ContextFilterHandler {
    async handle(messageContext, context) {
        //
        return super.handle(messageContext, context);
    }
}
/**
 * 群消息消息内容过滤
 */
class GroupFilterHandler extends ContextFilterHandler {
    async handle(messageContext, context) {
        if (messageContext && messageContext.chat_type === 'group') {
            // 群发消息时：没有@ 机器人，不处理(先用这个处理，后续改为机器人的openid)
            if (!messageContext.mentions
                || !Array.isArray(messageContext.mentions)
                || !messageContext.mentions.some(m => m.key === '@_user_1')) {
                console.log(`${FeishuConfig.getLogPrefix()} 处理群消息内容`);
                return {
                    type: 'group',
                    text: messageContext.content.text,
                    raw: messageContext.content,
                    pass: false,
                    reason: '群消息且不含@机器人'
                };
            }

        }
        return super.handle(messageContext, context);
    }
}


/**
 * 构建 Content 处理责任链
 */
function buildContextFilterChain() {
    const textFilterHandler = new TextFilterHandler();
    const groupFilterHandler = new GroupFilterHandler();
    textFilterHandler.setNext(groupFilterHandler);
    return textFilterHandler;
}

const contextFilterChain = buildContextFilterChain();


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
 * @param {string} messageContext - 消息上下文（包含原始消息对象等信息）eventData.json: groupChat.message
 * @param {Object} options - 配置对象
 * @param {Object} options.channelClient - 飞书客户端
 * @param {AgentManager} options.agentManager - Agent 管理器
 * @returns {Promise<void>}
 */
export async function handleFeishuMessage(chatId, userMessage, messageContext,{  channelClient, agentManager }) {
    // 检查消息是否正在处理中（去重）
    if (agentManager.isProcessing(chatId, userMessage)) {
        console.log(`[Feishu] 消息已在处理中，跳过：${chatId}:${userMessage}`);
        return;
    }

    try {
        // 标记消息开始处理
        agentManager.markProcessing(chatId, userMessage);
        console.log(`${FeishuConfig.getLogPrefix()}[-> Agent] 处理消息：${userMessage}`);

        console.log(`${FeishuConfig.getLogPrefix()}[-> Agent] =======> messageContext：${JSON.stringify(messageContext)}`);

        // 通过责任链处理 content 内容
        const contextFilterResult = await contextFilterChain.handle(messageContext, { agentManager, channelClient, chatId });
        // 记录内容处理结果
        if (!contextFilterResult || !contextFilterResult.pass) {
            console.log(`${FeishuConfig.getLogPrefix()} Content 处理结果：类型=${contextFilterResult.type}`);
            
            // 打印详细信息
            console.log(`${FeishuConfig.getLogPrefix()} unpass 原因：${contextFilterResult.reason}`);
            return;
        }

        //


        // 思考中
        const res = await sendThinkingMessage(channelClient, chatId);

        // 通过责任链处理命令
        const commandResult = await messageChain.handle(chatId, userMessage, { agentManager, channelClient });
        
        // 如果是命令，直接返回结果
        if (commandResult) {
            console.log(`${FeishuConfig.getLogPrefix()}:${agentManager.getCurrentAgentName()} messageId=${res.data.message_id} ;msg=${userMessage};命令处理结果：${JSON.stringify(commandResult)}`);

            await updateMessage(channelClient, res.data.message_id, "interactive", userMessage, commandResult.message);

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

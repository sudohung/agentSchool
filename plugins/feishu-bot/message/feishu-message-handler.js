/**
 * 飞书消息处理模块
 * 负责处理飞书收到的消息并转发给 Agent AI
 * 
 * 设计模式：
 * 1. 责任链模式（Chain of Responsibility）：处理消息流
 * 2. 策略模式（Strategy）：消息预处理规则
 * 3. 建造者模式（Builder）：构建责任链
 */

import { FeishuConfig } from '../config.js';
import { extractAIResponse } from './message-parser.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ESM: compute __dirname for this module so we can build reliable relative paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
import {
    sendThinkingMessage,
    sendErrorMessage,
    updateMessage
} from './index.js';

/**
 * ==================== 基础抽象类 ====================
 */

/**
 * 处理器基类
 */
class AbstractHandler {
    setNext(handler) {
        this.nextHandler = handler;
        return handler;
    }
    
    async handle(...args) {
        if (this.nextHandler) {
            return await this.nextHandler.handle(...args);
        }
        return null;
    }
}

/**
 * ==================== 消息预处理策略 ====================
 */

/**
 * 预处理策略接口
 */
class PreprocessStrategy {
    async process(messageContent, userMessage) {
        return userMessage;
    }
}

/**
 * Mention 替换策略
 */
class MentionReplaceStrategy extends PreprocessStrategy {
    async process(messageContent, userMessage) {
        if (userMessage && userMessage.includes('@_user_1')) {
            const cleaned = userMessage.replace(/@_user_1\s*/g, '').trim();
            console.log(`${FeishuConfig.getLogPrefix()} [预处理] 移除 @_user_1: ${userMessage} -> ${cleaned}`);
            return cleaned;
        }
        return userMessage;
    }
}

/**
 * 文本替换策略（可配置）
 */
class TextReplaceStrategy extends PreprocessStrategy {
    constructor(replacements = []) {
        super();
        this.replacements = replacements;
    }
    
    addRule(pattern, replacement) {
        this.replacements.push({ pattern, replacement });
        return this;
    }
    
    async process(messageContent, userMessage) {
        let result = userMessage;
        for (const { pattern, replacement } of this.replacements) {
            result = result.replace(pattern, replacement);
        }
        if (result !== userMessage) {
            console.log(`${FeishuConfig.getLogPrefix()} [预处理] 文本替换: ${userMessage} -> ${result}`);
        }
        return result;
    }
}

/**
 * ==================== 消息预处理处理器 ====================
 */

/**
 * 消息预处理处理器
 * 支持动态注册多个预处理策略
 */
class PreprocessHandler extends AbstractHandler {
    constructor() {
        super();
        this.strategies = [];
    }
    
    register(strategy) {
        this.strategies.push(strategy);
        return this;
    }
    
    async handle(chatId, userMessage, context) {
        let processedMessage = userMessage;
        const messageContent = context.messageContext?.content || {};
        
        // 依次执行所有预处理策略
        for (const strategy of this.strategies) {
            processedMessage = await strategy.process(messageContent, processedMessage);
        }
        
//        console.log(`${FeishuConfig.getLogPrefix()} [预处理完成] 原始: ${userMessage}, 处理后: ${processedMessage}`);
        
        // 传递处理后的消息
        return await super.handle(chatId, processedMessage, { ...context, processedMessage });
    }
}


/**
 * ==================== 命令处理器 ====================
 */

/**
 * /new 命令处理器 - 重置会话
 */
class NewCommandHandler extends AbstractHandler {
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
        return await super.handle(chatId, message, context);
    }
}

/**
 * /instant:xxx 命令处理器 - 切换 Agent
 */
class InstantCommandHandler extends AbstractHandler {
    async handle(chatId, message, context) {
        const instantMatch = message.trim().match(/^\/instant:(\S+)$/);
        if (instantMatch) {
            const agentKey = instantMatch[1];
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /instant 命令，切换 Agent: ${agentKey}`);
            const success = context.chatManager.setCurrentAgent(chatId, agentKey);
            const agentName = context.chatManager.getCurrentAgentName(chatId);
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
        return await super.handle(chatId, message, context);
    }
}

/**
 * /sessions 命令处理器 - 列出当前 Agent 的所有会话
 */
class SessionsCommandHandler extends AbstractHandler {
    async handle(chatId, message, context) {
        if (message.trim() === '/sessions') {
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /sessions 命令，列出会话`);
            try {
                const sessions = await context.chatManager.listSessions();
                const agentName = context.chatManager.getCurrentAgentName(chatId);
                
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
        return await super.handle(chatId, message, context);
    }
}

/**
 * /session:xxxx 命令处理器 - 切换会话并显示最新消息
 */
class SessionCommandHandler extends AbstractHandler {
    async handle(chatId, message, context) {
        const sessionMatch = message.trim().match(/^\/session:(\S+)$/);
        if (sessionMatch) {
            const targetSessionId = sessionMatch[1];
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /session 命令，切换会话: ${targetSessionId}`);
            
            try {
                context.chatManager.switchSession(chatId, targetSessionId);
                const messages = await context.chatManager.getSessionMessages(targetSessionId);
                const agentName = context.chatManager.getCurrentAgentName(chatId);
                
                if (!messages || messages.length === 0) {
                    return { 
                        type: 'command', 
                        action: 'switch_session',
                        message: `已切换到会话: ${targetSessionId}\n(暂无消息)`
                    };
                }
                
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
        return await super.handle(chatId, message, context);
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
 * /abort 命令处理器 - 中断当前会话
 */
class AbortCommandHandler extends AbstractHandler {
    async handle(chatId, message, context) {
        if (message.trim() === '/abort') {
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /abort 命令，中断当前会话`);
            
            try {

                const { chatManager, agentManager } = context;
                const sessionId = await agentManager.getSession(chatId);
                console.log(`${FeishuConfig.getLogPrefix()} 使用会话：${sessionId}`);

                if (FeishuConfig.isDebugEnabled()) {
                    console.log(`${FeishuConfig.getLogPrefix()} 使用会话：${sessionId}`);
                }

                // chatManage
                const agentKey = await chatManager.getCurrentAgentKey(chatId, "main")

                // 重置本地会话映射，创建新会话
                const obj = await agentManager.abortSession(agentKey, sessionId);
                
                return { 
                    type: 'command', 
                    action: 'abort_session',
                    sessionId: sessionId,
                    message: `已中断当前会话：${sessionId}`
                };
            } catch (error) {
                console.error(`${FeishuConfig.getLogPrefix()} 中断会话失败:`, error.message);
                return { 
                    type: 'command', 
                    action: 'abort_session',
                    message: `中断会话失败：${error.message}`
                };
            }
        }
        return await super.handle(chatId, message, context);
    }
}

/**
 * /permit:xxx 命令处理器 - 响应权限请求
 * 格式：/permit:permission_id 或 /permit:permission_id:allow
 */
class PermitCommandHandler extends AbstractHandler {
    async handle(chatId, message, context) {
        // 命令格式 /permit:once 允许所有权限请求（测试用） "once","always","reject"
        const permitMatch = message.trim().match(/^\/permit:(\S+)(?::(always|reject|once))?$/);

        if (permitMatch) {
            const action = permitMatch[1] || 'always';
            

            try {
                const { agentManager, chatManager } = context;
                
                // 从 chatManager 获取权限请求信息
                const permissionRequest = chatManager.getPermissionRequest(chatId);

                if (!permissionRequest) {
                    return {
                        type: 'command',
                        action: 'permit_permission',
                        message: `未找到待处理的权限请求，请先收到权限请求后再响应`
                    };
                }
                const permissionId = permissionRequest.permissionId;

                console.log(`${FeishuConfig.getLogPrefix()} 执行 /permit 命令，id : ${permissionId},响应权限请求 操作：${action}`);
                const sessionId = permissionRequest.sessionId;
                const agentKey = await chatManager.getCurrentAgentKey(chatId, "main");
                const agent = agentManager.getAgent(agentKey);
                
                if (!agent || !agent.client) {
                    return {
                        type: 'command',
                        action: 'permit_permission',
                        message: `权限响应失败：Agent 客户端未初始化`
                    };
                }
                
                const result = await agent.client.postSessionIdPermissionsPermissionId({
                    path: { id: sessionId, permissionID: permissionId },
                    body: { response: action }
                });

                console.log(`${FeishuConfig.getLogPrefix()} 权限响应结果：${ JSON.stringify(result)}` );
                
                // 清理已处理的权限请求
                chatManager.removePermissionRequest(chatId);
                
                const actionText = action;
                return {
                    type: 'command',
                    action: 'permit_permission',
                    permissionId,
                    action,
                    sessionId,
                    message: `已${actionText}权限请求：${permissionId}`
                };
            } catch (error) {
                console.error(`${FeishuConfig.getLogPrefix()} 权限响应失败:`, error);
                return {
                    type: 'command',
                    action: 'permit_permission',
                    message: `权限响应失败：${error.message}`
                };
            }
        }
        return await super.handle(chatId, message, context);
    }
}

/**
 * /reply:xxx 命令处理器 - 发送消息应答
 * 格式：/reply:message_content
 */
class ReplyCommandHandler extends AbstractHandler {
    async handle(chatId, message, context) {
        const replyMatch = message.trim().match(/^\/reply:(.+)$/);
        if (replyMatch) {
            const replyContent = replyMatch[1].trim();
            
            console.log(`${FeishuConfig.getLogPrefix()} 执行 /reply 命令，发送应答消息：${replyContent}`);
            
            try {
                const { agentManager, chatManager } = context;
                const sessionId = await agentManager.getSession(chatId);
                const agentKey = await chatManager.getCurrentAgentKey(chatId, "main");
                const agent = agentManager.getAgent(agentKey);
                
                if (!agent || !agent.client) {
                    return {
                        type: 'command',
                        action: 'reply_message',
                        message: `消息应答失败：Agent 客户端未初始化`
                    };
                }
                
                const result = await agent.client.session.prompt({
                    path: { id: sessionId },
                    body: {
                        parts: [{ type: "text", text: replyContent }],
                        noReply: false
                    }
                });
                
                const aiResponse = this.extractAIResponse(result);
                
                return {
                    type: 'command',
                    action: 'reply_message',
                    sessionId,
                    message: `应答消息已发送\n${aiResponse ? `AI 回复：${aiResponse}` : ''}`
                };
            } catch (error) {
                console.error(`${FeishuConfig.getLogPrefix()} 消息应答失败:`, error.message);
                return {
                    type: 'command',
                    action: 'reply_message',
                    message: `消息应答失败：${error.message}`
                };
            }
        }
        return await super.handle(chatId, message, context);
    }
    
    extractAIResponse(result) {
        if (!result) return '';
        
        const data = result.data || result;
        if (data?.info?.content) {
            return data.info.content;
        }
        
        if (data?.parts && Array.isArray(data.parts)) {
            const textParts = data.parts
                .filter(p => p.type === 'text')
                .map(p => p.text || '')
                .join('');
            return textParts;
        }
        
        return '';
    }
}

/**
 * AI 消息处理器 - 处理普通消息，调用 AI 生成回复
 */
class AIMessageHandler extends AbstractHandler {
    async handle(chatId, message, context) {
        const { chatManager, agentManager } = context;
        
        console.log(`${FeishuConfig.getLogPrefix()} 执行 AI 消息处理`);
        
        const sessionId = await agentManager.getSession(chatId);
        console.log(`${FeishuConfig.getLogPrefix()} 使用会话：${sessionId}`);

        if (FeishuConfig.isDebugEnabled()) {
            console.log(`${FeishuConfig.getLogPrefix()} 使用会话：${sessionId}`);
        }

        // chatManage
        const agentKey = await chatManager.getCurrentAgentKey(chatId, "main")
        const result = await agentManager.sendMessage(agentKey, sessionId, message);
        const { aiResponse, otherParts } = extractAIResponse(result, message);
        
        return { 
            type: 'ai_response', 
            action: 'message_processed',
            sessionId,
            message: aiResponse
        };
    }
}

/**
 * ==================== 责任链建造者 ====================
 */

/**
 * 消息处理链建造者
 */
class MessageChainBuilder {
    constructor() {
        this.handlers = [];
    }
    
    add(handler) {
        this.handlers.push(handler);
        return this;
    }
    
    build() {
        if (this.handlers.length === 0) {
            return null;
        }
        
        for (let i = 0; i < this.handlers.length - 1; i++) {
            this.handlers[i].setNext(this.handlers[i + 1]);
        }
        
        return this.handlers[0];
    }
}

/**
 * ==================== 上下文过滤器 ====================
 */

/**
 * Context 过滤器基类
 */
class AbstractFilterHandler {
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
        };
    }
}

/**
 * 群消息过滤器
 */
class GroupFilterHandler extends AbstractFilterHandler {
    async handle(messageContext, context) {
        if (messageContext && messageContext.chat_type === 'group') {
            if (!messageContext.mentions
                || !Array.isArray(messageContext.mentions)
                || !messageContext.mentions.some(m => m.key === '@_user_1')) {
                console.log(`${FeishuConfig.getLogPrefix()} 过滤群消息（未@机器人）`);
                return {
                    type: 'group',
                    text: messageContext.content?.text || '',
                    raw: messageContext.content,
                    pass: false,
                    reason: '群消息且不含@机器人'
                };
            }
        }
        return await super.handle(messageContext, context);
    }
}

/**
 * 黑名单 chatId 过滤器
 */
class BanChatFilterHandler extends AbstractFilterHandler {
    constructor() {
        super();
        this.cache = null;
        this.cacheTime = 0;
        this.cacheTtl = 60 * 1000; // 1分钟缓存
        // 使用相对于当前模块的路径，确保在不同启动目录下也能正确找到文件
        this.banFilePath = path.join(__dirname, '..', 'ban', 'ban.json');
    }

    getBlockedChatIds() {
        const now = Date.now();
        console.log(`${FeishuConfig.getLogPrefix()} 获取黑名单列表，缓存状态: ${this.cache ? '有效' : '无效'}`);
        console.log(`${FeishuConfig.getLogPrefix()} 获取黑名单列表，banFilePath: ${this.banFilePath}`);
        if (this.cache && (now - this.cacheTime) < this.cacheTtl) {
            return this.cache;
        }
        try {
            if (fs.existsSync(this.banFilePath)) {
                const data = JSON.parse(fs.readFileSync(this.banFilePath, 'utf-8'));
                this.cache = new Set(data.blockedChatId || []);
                this.cacheTime = now;
                console.log(`${FeishuConfig.getLogPrefix()} 重新加载黑名单列表，当前数量: ${this.cache.size}`);
            } else {
                this.cache = new Set();
            }
        } catch (error) {
            console.error(`${FeishuConfig.getLogPrefix()} 读取黑名单文件失败:`, error.message);
            this.cache = new Set();
        }
        return this.cache;
    }

    async handle(messageContext, context) {
        const chatId = messageContext?.chat_id;
        const blockedChatIds = this.getBlockedChatIds();

        if (chatId && blockedChatIds.has(chatId)) {
            console.log(`${FeishuConfig.getLogPrefix()} 过滤黑名单 chatId：${chatId}`);
            return {
                type: 'ban',
                text: '',
                raw: messageContext,
                pass: false,
                reason: `chatId ${chatId} 在黑名单中`
            };
        }
        return await super.handle(messageContext, context);
    }
}

/**
 * 构建上下文过滤链
 */
function buildContextFilterChain() {
    const builder = new MessageChainBuilder();
    builder.add(new GroupFilterHandler());
    builder.add(new BanChatFilterHandler());
    return builder.build();
}

/**
 * ==================== 构建消息处理链 ====================
 */

/**
 * 构建消息处理链
 * @param {PreprocessStrategy[]} preprocessStrategies - 预处理策略列表
 */
function buildMessageChain(preprocessStrategies = []) {
    // 创建预处理处理器
    const preprocessHandler = new PreprocessHandler();

    // 注册默认预处理策略
    preprocessHandler.register(new MentionReplaceStrategy());
    
    // 注册自定义预处理策略
    for (const strategy of preprocessStrategies) {
        preprocessHandler.register(strategy);
    }
    
    // 构建处理链
    const builder = new MessageChainBuilder();
    builder.add(preprocessHandler);
    builder.add(new NewCommandHandler());
    builder.add(new InstantCommandHandler());
    builder.add(new SessionsCommandHandler());
    builder.add(new SessionCommandHandler());
    builder.add(new AbortCommandHandler());
    builder.add(new PermitCommandHandler());
    builder.add(new ReplyCommandHandler());
    builder.add(new AIMessageHandler());
    
    return builder.build();
}

// 创建默认处理链实例
const messageChain = buildMessageChain();
const contextFilterChain = buildContextFilterChain();

/**
 * ==================== 导出的工具函数 ====================
 */

/**
 * 创建自定义消息处理链
 * @param {PreprocessStrategy[]} strategies - 自定义预处理策略
 */
export function createMessageChain(strategies = []) {
    return buildMessageChain(strategies);
}

/**
 * 创建文本替换预处理策略
 * @param {Array<{pattern: RegExp, replacement: string}>} rules - 替换规则
 */
export function createTextReplaceStrategy(rules = []) {
    const strategy = new TextReplaceStrategy();
    for (const rule of rules) {
        strategy.addRule(rule.pattern, rule.replacement);
    }
    return strategy;
}

/**
 * ==================== 主处理函数 ====================
 */

/**
 * 处理飞书收到的消息（转发给 Agent AI）
 */
export async function handleFeishuMessage(chatId, userMessage, messageContext, { chatManager, agentManager }) {
    if (agentManager.isProcessing(chatId, userMessage)) {
        console.log(`[Feishu] 消息已在处理中，跳过：${chatId}:${userMessage}`);
        return;
    }

    try {
        agentManager.markProcessing(chatId, userMessage);
        console.log(`${FeishuConfig.getLogPrefix()}[handleFeishuMessage-> Agent] 开始处理消息：${userMessage}`);
//        console.log(`${FeishuConfig.getLogPrefix()}[-> Agent] messageContext：${JSON.stringify(messageContext)}`);

        // 通过责任链过滤内容
        const contextFilterResult = await contextFilterChain.handle(messageContext, { agentManager, chatId });
        
        if (!contextFilterResult || !contextFilterResult.pass) {
            console.log(`${FeishuConfig.getLogPrefix()} 过滤结果：类型=${contextFilterResult.type}, 原因=${contextFilterResult.reason}`);
            return;
        }

        // 发送思考状态
        const res = await sendThinkingMessage(chatManager, chatId);

        // 通过责任链处理消息（包含预处理）
        const commandResult = await messageChain.handle(chatId, userMessage, { 
            agentManager, 
            chatManager,
            messageContext 
        });
        
        if (commandResult) {
            console.log(`${FeishuConfig.getLogPrefix()} ${chatManager.getCurrentAgentName(chatId)} messageId=${res.data.message_id} 结果：${JSON.stringify(commandResult)}`);
            await updateMessage(chatManager, res.data.message_id, "interactive", userMessage, commandResult.message);
            return;
        }
        
        console.error(`${FeishuConfig.getLogPrefix()} 命令处理失败:`, commandResult);

    } catch (error) {
        console.error(`${FeishuConfig.getLogPrefix()}[-> Agent] 处理失败:`, error.message);
        console.error(`${FeishuConfig.getLogPrefix()}[-> Agent] 处理失败 stack:`, error);
        if (FeishuConfig.isDebugEnabled()) {
            console.error(`${FeishuConfig.getLogPrefix()}[-> Agent] 错误详情:`, error);
        }
        await sendErrorMessage(chatManager, chatId, `回复: ${userMessage} -> ${error.message}`);
    } finally {
        agentManager.markCompleted(chatId, userMessage);
    }
}

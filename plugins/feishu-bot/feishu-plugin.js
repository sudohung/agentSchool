/**
 * 飞书消息通知插件
 * 监听 OpenCode 事件并发送消息到飞书
 */

import * as lark from '@larksuiteoapi/node-sdk';
import { 
    extractAIResponse 
} from './message-parser.js';
import {
    sendThinkingMessage,
    sendErrorMessage,
    sendAIResponse,
    sendEmptyResponse,
    updateMessage,
    recallMessage,
    sendEventNotification
} from './message/index.js';
import { FeishuConfig } from './config.js';

// 验证配置
if (!FeishuConfig.isValid()) {
    console.error('[FeishuBot] 缺少必要的环境变量配置：FEISHU_APP_ID 和 FEISHU_APP_SECRET');
    throw new Error('飞书机器人配置不完整');
}

// 创建 飞书 客户端（用于发送消息）
const feishuClient = new lark.Client({
    appId: FeishuConfig.appId,
    appSecret: FeishuConfig.appSecret
});

// 飞书 长连接客户端（用于接收消息）
let wsClient = null;
let isConnected = false;

// 消息去重集合，存储已处理的 messageId
const processedMessageIds = new Set();

// 消息去重时间戳集合，存储已处理消息的时间戳
const processedMessageTimestamps = new Map();

/******************** 主要方法 ****************************/

/**
 * 清理过期的消息记录
 * @param {number} currentTime - 当前时间戳
 */
function cleanupExpiredMessages(currentTime) {
    let cleanedCount = 0;

    // 使用配置中的消息ID TTL
    const MESSAGE_ID_TTL = FeishuConfig.messageConfig.messageIdTtl;
    for (const [messageId, timestamp] of processedMessageTimestamps.entries()) {
        if (currentTime - timestamp > MESSAGE_ID_TTL) {
            processedMessageIds.delete(messageId);
            processedMessageTimestamps.delete(messageId);
            cleanedCount++;
        }
    }
    
    if (cleanedCount > 0) {
        console.log(`${FeishuConfig.getLogPrefix()} 清理了 ${cleanedCount} 条过期消息记录`);
        console.log(`${FeishuConfig.getLogPrefix()} 当前缓存消息数：${processedMessageIds.size}`);
    }
}

function startWebSocketConnection(onMessageReceived) {
    if (wsClient && isConnected) {
        console.log(`${FeishuConfig.getLogPrefix()} WebSocket 已连接，跳过重复启动`);
        return;
    }

    try {
        wsClient = new lark.WSClient({
            appId: FeishuConfig.appId,
            appSecret: FeishuConfig.appSecret,
            loggerLevel: FeishuConfig.logConfig.level === 'debug' ? lark.LoggerLevel.debug : 
                       FeishuConfig.logConfig.level === 'error' ? lark.LoggerLevel.error : 
                       lark.LoggerLevel.info
        });

        wsClient.start({
            eventDispatcher: new lark.EventDispatcher({}).register({
                'im.message.receive_v1': async (data) => {
                    const {
                        message: { chat_id, content }
                    } = data;
                    
                    console.log(`${FeishuConfig.getLogPrefix()} 收到消息，聊天 ID: ${chat_id}, eventId: ${data.event_id}, create_time: ${data.create_time}`);

                    // 基于 messageId 进行去重处理
                    const messageId = data.event?.message?.message_id || data.message?.message_id;
                    const currentTime = Date.now();
                    
                    if (messageId) {

                        // 比较时间戳，使用配置中的消息过期时间
                        // 飞书的 create_time 是毫秒级时间戳（可能是字符串或数字）
                        const messageTime = typeof data.create_time === 'string' 
                            ? parseInt(data.create_time) 
                            : data.create_time;
                        if (currentTime - messageTime > FeishuConfig.messageConfig.messageExpiryTime) {
                            console.log(`${FeishuConfig.getLogPrefix()} 消息过旧，跳过: ${messageId}， 内容：${JSON.stringify(content)}`);
                            return;
                        }
                        // 检查是否已处理过
                        if (processedMessageIds.has(messageId)) {
                            console.log(`${FeishuConfig.getLogPrefix()} 消息已处理过，跳过: ${messageId}`);
                            return;
                        }
                        
                        // 记录处理过的消息
                        processedMessageIds.add(messageId);
                        processedMessageTimestamps.set(messageId, currentTime);
                        
                        console.log(`${FeishuConfig.getLogPrefix()} 记录新消息: ${messageId}`);
                    }
                    
                    // 清理过期的消息记录（每处理10条消息清理一次）
                    if (processedMessageIds.size % 10 === 0) {
                        cleanupExpiredMessages(currentTime);
                    }
                    console.log(`[Feishu] 收到消息，聊天 内容: ${data}`);

                    // 触发回调处理消息
                    if (onMessageReceived) {
                        await onMessageReceived(chat_id, JSON.parse(content).text);
                    }

                    return {}
                }
            })
        });

        isConnected = true;
        console.log(`${FeishuConfig.getLogPrefix()} WebSocket 长连接已启动`);
    } catch (error) {
        console.error(`${FeishuConfig.getLogPrefix()} WebSocket 启动失败:`, error.message);
        isConnected = false;
    }
}

/**
 * opencode 的 飞书插件主函数
 * @param {Object} context - 插件上下文
 * @param {Object} context.project - 项目信息
 * @param {Object} context.client - opencode客户端
 * @param {Object} context.$ - 依赖信息
 * @param {string} context.directory - 目录信息
 * @param {string} context.worktree - 工作区信息
 */
export const OpencodeFeishuPlugin = async ({ project, client, $, directory, worktree }) => {
    
    // 存储会话映射，用于双向通信
    const sessionMap = new Map();
    // 防重处理标记
    const processingMessages = new Set();
    
    // 插件初始化日志
    await client.app.log({
        body: {
            service: "feishu-plugin",
            level: "info",
            message: "飞书插件已初始化",
            extra: {
                project: project?.name || 'unknown',
                directory: directory
            }
        }
    });

    /**
     * 处理飞书收到的消息（转发给 OpenCode AI）
     */
    async function handleFeishuMessage(chatId, userMessage) {
        // 创建唯一标识防止重复处理
        const messageKey = `${chatId}:${userMessage}`;
        if (processingMessages.has(messageKey)) {
            console.log(`[Feishu] 消息已在处理中，跳过: ${messageKey}`);
            return;
        }

        try {

            processingMessages.add(messageKey);
            console.log(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 处理消息：${userMessage}`);

            // 先发送思考状态
            const res = await sendThinkingMessage(feishuClient, chatId);
            console.log(`[Feishu -> OpenCode] 处理think消息：${JSON.stringify(res)}`);


            // 创建或获取会话
            let sessionId = sessionMap.get(chatId);
            if (!sessionId) {
                const session = await client.session.create({
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
            const result = await client.session.prompt({
                path: { id: sessionId },
                body: {
                    parts: [{ type: "text", text: userMessage }],
                },
            });
            
            // 打印完整的 result 结构用于调试
//            console.log('[Opencode] === Prompt Result 完整结构 ===');
//            console.log('[Opencode] result:', JSON.stringify(result, null, 2));
//            console.log('[Opencode] result.data:', result.data);
//            console.log('[Opencode] result.info:', result.info);
//            console.log('[Opencode] ======================');
            
            // 提取 AI 回复
            const { aiResponse, otherParts } = extractAIResponse(result, userMessage);

            // 回复到飞书
//            recallMessage(feishuClient, res.data.message_id);
//            await sendAIResponse(feishuClient, chatId, userMessage, aiResponse);
            await updateMessage(feishuClient, res.data.message_id, userMessage, aiResponse);
            
        } catch (error) {
            console.error(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 处理失败:`, error.message);
            if (FeishuConfig.isDebugEnabled()) {
                console.error(`${FeishuConfig.getLogPrefix()}[-> OpenCode] 错误详情:`, error);
            }
            await sendErrorMessage(feishuClient, chatId, error.message);
        } finally {
            // 清理处理标记
            setTimeout(() => {
                processingMessages.delete(messageKey);
            }, FeishuConfig.messageConfig.processingTimeout); // 使用配置中的超时时间
        }
    }

    /**
     * 启动 飞书的WebSocket 连接，并订阅飞书事件
     */
    startWebSocketConnection(handleFeishuMessage);

    /**
     * 监听所有opencode事件
     */
    return {
        /**
         * 监听所有事件
         */
        event: async ({ event }) => {
            
            // 会话创建事件
            if (event.type === "session.created") {
                // 使用默认聊天ID或从事件中获取
                const targetChatId = FeishuConfig.defaultChatId || event.session?.chatId;
                if (targetChatId) {
                    await sendEventNotification(
                        feishuClient,
                        targetChatId,
                        "OpenCode 会话已创建",
                        `项目：${project?.name || '未知'}\n会话 ID: ${event.session.id}`
                    );
                }
            }
            
            // 会话完成事件
            if (event.type === "session.idle") {
                const targetChatId = FeishuConfig.defaultChatId || event.session?.chatId;
                if (targetChatId) {
                    await sendEventNotification(
                        feishuClient,
                        targetChatId,
                        "会话已完成",
                        `会话 ${event.session.id} 已完成处理`
                    );
                }
            }
            
            // 工具执行事件
            if (event.type === "tool.execute.after") {
                const toolName = event.tool.name;
                const targetChatId = FeishuConfig.defaultChatId || event.session?.chatId;
                if (targetChatId) {
                    await sendEventNotification(
                        feishuClient,
                        targetChatId,
                        `工具执行：${toolName}`,
                        `工具 ${toolName} 已执行完成`
                    );
                }
            }
            
            // 错误事件
            if (event.type === "session.error") {
                const targetChatId = FeishuConfig.defaultChatId || event.session?.chatId;
                if (targetChatId) {
                    await sendErrorMessage(
                        feishuClient,
                        targetChatId,
                        event.error.message,
                        "❌ 发生错误"
                    );
                }
            }
        },

        /**
         * 监听消息更新事件
         */
        "message.updated": async (input, output) => {
            // 可以在这里处理消息相关的逻辑
            // console.log('[Feishu] 消息已更新:', input.message.id);
        },

        /**
         * 监听文件编辑事件
         */
        "file.edited": async (input, output) => {
            // 可以在这里处理文件编辑后的通知
            // console.log('[Feishu] 文件已编辑:', input.filePath);
        }
    };
};

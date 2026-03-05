/**
 * 飞书消息通知插件
 * 监听 OpenCode 事件并发送消息到飞书
 */

import * as lark from '@larksuiteoapi/node-sdk';
import { 
    handleFeishuMessage,
    sendEventNotification,
    sendErrorMessage
} from './message/index.js';
import { FeishuConfig } from './config.js';
import { createFeishuWSClient } from './client/index.js';
import { createAgentManager, OpencodeAgent } from './agent/index.js';

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

// 创建飞书长连接客户端实例
const feishuWSClient = createFeishuWSClient({
    appId: FeishuConfig.appId,
    appSecret: FeishuConfig.appSecret,
    logLevel: FeishuConfig.logConfig.level,
    messageExpiryTime: FeishuConfig.messageConfig.messageExpiryTime,
    messageIdTtl: FeishuConfig.messageConfig.messageIdTtl
});

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

// 启动飞书长连接客户端
function startWebSocketConnection(onMessageReceived) {
    console.log(`正在启动 feishu 处理消息`);
    return feishuWSClient.start(onMessageReceived);
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
export const OpencodeFeishuPlugin = async (context) => {
    const { project, client, $, directory, worktree } = context;

    
    // 兼容：如果 agentClient 为空，尝试使用 client
    const effectiveClient = client;
    
    if (!effectiveClient) {
        console.error('[FeishuBot] 错误：未找到有效的 client 参数');
        console.error('[FeishuBot] context:', context);
        throw new Error('OpenCode client 未提供');
    }

    console.log('[FeishuBot] 插件已启动');
    
    // 创建 Agent 策略实例
    const agent = new OpencodeAgent(effectiveClient);
    console.log('[FeishuBot] 插件已启动1');

    // 创建 Agent 管理器（封装 sessionMap 和 processingMessages）
    const agentManager = createAgentManager({
        agent: agent,
        processingTimeout: FeishuConfig.messageConfig.processingTimeout,
        messageIdTtl: FeishuConfig.messageConfig.messageIdTtl
    });

    // 插件初始化日志
    await agentManager.log('info', '飞书插件已初始化', {
        project: project?.name || 'unknown',
        directory
    });
    console.log('[FeishuBot] 插件已启动2');

    /**
     * 启动 飞书的 WebSocket 连接，并订阅飞书事件
     */
    await startWebSocketConnection((chatId, userMessage) => {
        return handleFeishuMessage(chatId, userMessage, {
            channelClient: feishuClient,
            agentManager
        });
    });

    console.log('[FeishuBot] 插件已启动3');

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

/**
 * 飞书消息通知插件
 * 监听 OpenCode 事件并发送消息到飞书
 */

import * as lark from '@larksuiteoapi/node-sdk';

// 飞书客户端配置
const feishuConfig = {
    appId: 'cli_a9059178d1b8dcd1',
    appSecret: 'utn16AUDhHarUUWY2yaZScMX4OJNBY4K'
};

// 创建 HTTP 客户端（用于发送消息）
const feishuClient = new lark.Client(feishuConfig);

// WebSocket 长连接客户端（用于接收消息）
let wsClient = null;
let isConnected = false;
// 消息去重集合，存储已处理的 messageId
const processedMessageIds = new Set();
// 定期清理过期的 messageId（保留最近1小时）
const MESSAGE_ID_TTL = 60 * 60 * 1000; // 1小时
const processedMessageTimestamps = new Map();

/**
 * 清理过期的消息记录
 * @param {number} currentTime - 当前时间戳
 */
function cleanupExpiredMessages(currentTime) {
    let cleanedCount = 0;
    for (const [messageId, timestamp] of processedMessageTimestamps.entries()) {
        if (currentTime - timestamp > MESSAGE_ID_TTL) {
            processedMessageIds.delete(messageId);
            processedMessageTimestamps.delete(messageId);
            cleanedCount++;
        }
    }
    
    if (cleanedCount > 0) {
        console.log(`[Feishu] 清理了 ${cleanedCount} 条过期消息记录`);
        console.log(`[Feishu] 当前缓存消息数: ${processedMessageIds.size}`);
    }
}

/**
 * 解析 OpenCode 响应中的 parts
 * @param {Array} parts - OpenCode 响应的 parts 数组
 * @returns {Object} 解析结果 {textResponse, otherParts}
 */
function parseOpenCodeParts(parts) {
    const textParts = [];
    const otherParts = [];
    
    if (!Array.isArray(parts)) {
        return { textResponse: '', otherParts: [] };
    }
    
    for (const part of parts) {
        const parsedPart = parsePartByType(part);
        
        if (parsedPart.isText) {
            textParts.push(parsedPart.content);
        } else {
            otherParts.push(parsedPart);
        }
    }
    
    return {
        textResponse: textParts.join('\n'),
        otherParts: otherParts
    };
}

/**
 * 根据 part 类型进行解析
 * @param {Object} part - 单个 part 对象
 * @returns {Object} 解析后的 part 信息
 */
function parsePartByType(part) {
    const baseInfo = {
        type: part.type,
        id: part.id,
        sessionId: part.sessionID,
        messageId: part.messageID
    };
    
    switch (part.type) {
        case 'text':
            return {
                ...baseInfo,
                isText: true,
                content: part.text
            };
        
        case 'image':
            return {
                ...baseInfo,
                isText: false,
                content: '[图片内容待处理]',
                rawData: part
            };
        
        case 'code':
            return {
                ...baseInfo,
                isText: false,
                content: '[代码内容待处理]',
                rawData: part
            };
        
        case 'reasoning':
            return {
                ...baseInfo,
                isText: false,
                content: '[推理过程待处理]',
                rawData: part
            };
        
        case 'step-start':
        case 'step-finish':
            // 流程控制类型，不作为内容返回
            return {
                ...baseInfo,
                isText: false,
                content: '[流程控制]',
                rawData: part
            };
        
        default:
            return {
                ...baseInfo,
                isText: false,
                content: `[未知类型: ${part.type}]`,
                rawData: part
            };
    }
}

/**
 * 提取 AI 回复内容
 * @param {Object} result - OpenCode 响应结果
 * @param {string} userMessage - 用户原始消息
 * @returns {Object} {aiResponse, otherParts}
 */
function extractAIResponse(result, userMessage) {
    let aiResponse = '收到您的消息';
    let otherParts = [];
    
    // 优先从 parts 中提取
    if (result.data.parts && Array.isArray(result.data.parts)) {
        const parsed = parseOpenCodeParts(result.data.parts);
        aiResponse = parsed.textResponse || aiResponse;
        otherParts = parsed.otherParts;
        
        // 调试信息
        if (otherParts.length > 0) {
            logOtherPartStats(otherParts);
        }
    }
    // 兼容旧格式
    else if (result.data && result.data.info) {
        aiResponse = result.data.info.summary || userMessage;
    } else if (result.info) {
        aiResponse = result.info.summary || userMessage;
    }
    
    return { aiResponse, otherParts };
}

/**
 * 记录非文本 part 的统计信息
 * @param {Array} otherParts - 非文本 part 数组
 */
function logOtherPartStats(otherParts) {
    console.log(`[Feishu] 检测到 ${otherParts.length} 个非文本 part:`);
    const typeCounts = {};
    otherParts.forEach(p => {
        typeCounts[p.type] = (typeCounts[p.type] || 0) + 1;
    });
    console.log('[Feishu] 类型分布:', typeCounts);
}

/**
 * 发送飞书消息（使用 HTTP 短连接）
 * @param {string} chatId - 聊天 ID
 * @param {string} title - 消息标题
 * @param {string} content - 消息内容
 */
async function sendFeishuMessage(chatId, title, content) {
    try {
        await feishuClient.im.v1.message.create({
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
    } catch (error) {
        console.error(`[Feishu] 发送消息失败:`, error.message);
    }
}
function startWebSocketConnection(onMessageReceived) {
    if (wsClient && isConnected) {
        console.log('[Feishu] WebSocket 已连接，跳过重复启动');
        return;
    }

    try {
        wsClient = new lark.WSClient({
            ...feishuConfig,
            loggerLevel: lark.LoggerLevel.info
        });

        wsClient.start({
            eventDispatcher: new lark.EventDispatcher({}).register({
                'im.message.receive_v1': async (data) => {
                    const {
                        message: { chat_id, content }
                    } = data;
                    
                    console.log(`[Feishu] 收到消息，聊天 ID: ${chat_id}`);
                    
                    // 基于 messageId 进行去重处理
                    const messageId = data.event?.message?.message_id || data.message?.message_id;
                    const currentTime = Date.now();
                    
                    if (messageId) {
                        // 检查是否已处理过
                        if (processedMessageIds.has(messageId)) {
                            console.log(`[Feishu] 消息已处理过，跳过: ${messageId}`);
                            return;
                        }
                        
                        // 记录处理过的消息
                        processedMessageIds.add(messageId);
                        processedMessageTimestamps.set(messageId, currentTime);
                        
                        console.log(`[Feishu] 记录新消息: ${messageId}`);
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
                }
            })
        });

        isConnected = true;
        console.log('[Feishu] WebSocket 长连接已启动');
    } catch (error) {
        console.error('[Feishu] WebSocket 启动失败:', error.message);
        isConnected = false;
    }
}

/**
 * 飞书插件主函数
 */
export const FeishuPlugin = async ({ project, client, $, directory, worktree }) => {
    
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
            // 先回意见
            await sendFeishuMessage(
                chatId,
                `Thinking...`
            );

            processingMessages.add(messageKey);
            console.log(`[Feishu -> OpenCode] 处理消息：${userMessage}`);
            
            // 创建或获取会话
            let sessionId = sessionMap.get(chatId);
            if (!sessionId) {
                const session = await client.session.create({
                    body: { title: `feishu-${chatId}-${Date.now()}` }
                });
                
                // 打印完整的 session 结构用于调试
                console.log('[Feishu] === Session 完整结构 ===');
                console.log('[Feishu] session:', JSON.stringify(session, null, 2));
                console.log('[Feishu] session.id:', session.id);
                console.log('[Feishu] session.data:', session.data);
                console.log('[Feishu] session.path:', session.path);
                console.log('[Feishu] ======================');
                
                // 正确获取 session ID，检查多种可能的字段名
                sessionId = session.id || session.data?.id || session.path?.id;
                
                if (!sessionId) {
                    console.error('[Feishu] Session 创建成功但未获取到 ID:', session);
                    throw new Error('无法获取 Session ID');
                }
                
                console.log(`[Feishu] 创建新会话：${sessionId}`);
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
            console.log('[Opencode] === Prompt Result 完整结构 ===');
            console.log('[Opencode] result:', JSON.stringify(result, null, 2));
            console.log('[Opencode] result.data:', result.data);
            console.log('[Opencode] result.info:', result.info);
            console.log('[Opencode] ======================');
            
            // 提取 AI 回复
            const { aiResponse, otherParts } = extractAIResponse(result, userMessage);

            // 回复到飞书
            await sendFeishuMessage(
                chatId,
                `回复：${userMessage.substring(0, 20)}...`,
                aiResponse
            );
            
        } catch (error) {
            console.error('[Feishu -> OpenCode] 处理失败:', error.message);
            console.error('[Feishu -> OpenCode] 错误详情:', error);
            await sendFeishuMessage(
                chatId,
                '❌ 处理失败',
                `错误：${error.message}`
            );
        } finally {
            // 清理处理标记
            setTimeout(() => {
                processingMessages.delete(messageKey);
            }, 5000); // 5秒后清除标记
        }
    }

    // 启动 WebSocket 长连接（如果需要接收飞书消息）
    // 注意：如果只需要发送通知，可以注释掉下面这行
    startWebSocketConnection(handleFeishuMessage);

    return {
        /**
         * 监听所有事件
         */
        event: async ({ event }) => {
            
            // 会话创建事件
            if (event.type === "session.created") {
                await sendFeishuMessage(
                    "chat_id_here", // 替换为实际聊天 ID
                    "OpenCode 会话已创建",
                    `项目：${project?.name || '未知'}\n会话 ID: ${event.session.id}`
                );
            }
            
            // 会话完成事件
            if (event.type === "session.idle") {
                await sendFeishuMessage(
                    "chat_id_here",
                    "会话已完成",
                    `会话 ${event.session.id} 已完成处理`
                );
            }
            
            // 工具执行事件
            if (event.type === "tool.execute.after") {
                const toolName = event.tool.name;
                await sendFeishuMessage(
                    "chat_id_here",
                    `工具执行：${toolName}`,
                    `工具 ${toolName} 已执行完成`
                );
            }
            
            // 错误事件
            if (event.type === "session.error") {
                await sendFeishuMessage(
                    "chat_id_here",
                    "❌ 发生错误",
                    `错误信息：${event.error.message}`
                );
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

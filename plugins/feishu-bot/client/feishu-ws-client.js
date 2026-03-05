/**
 * 飞书 WebSocket 长连接客户端
 * 提供可复用的长连接创建和管理功能
 */

import * as lark from '@larksuiteoapi/node-sdk';

/**
 * 飞书长连接客户端管理类
 */
export class FeishuWSClient {
    /**
     * @type {lark.WSClient}
     */
    #wsClient = null;
    
    /**
     * @type {boolean}
     */
    #isConnected = false;
    
    /**
     * @type {Set<string>}
     */
    #processedMessageIds = new Set();
    
    /**
     * @type {Map<string, number>}
     */
    #processedMessageTimestamps = new Map();
    
    /**
     * @type {Object}
     */
    #config = null;
    
    /**
     * 创建飞书长连接客户端
     * @param {Object} config - 配置参数
     * @param {string} config.appId - 飞书应用 ID
     * @param {string} config.appSecret - 飞书应用密钥
     * @param {string} [config.logLevel='info'] - 日志级别 (debug, info, error)
     * @param {number} [config.messageExpiryTime=300000] - 消息过期时间（毫秒），默认 5 分钟
     * @param {number} [config.messageIdTtl=600000] - 消息 ID 缓存 TTL（毫秒），默认 10 分钟
     */
    constructor(config) {
        if (!config.appId || !config.appSecret) {
            throw new Error('飞书长连接客户端配置不完整：缺少 appId 或 appSecret');
        }
        
        this.#config = {
            appId: config.appId,
            appSecret: config.appSecret,
            logLevel: config.logLevel || 'info',
            messageExpiryTime: config.messageExpiryTime || 5 * 60 * 1000, // 5 分钟
            messageIdTtl: config.messageIdTtl || 10 * 60 * 1000 // 10 分钟
        };
    }
    
    /**
     * 获取日志前缀
     * @returns {string}
     */
    #getLogPrefix() {
        return '[FeishuWSClient]';
    }
    
    /**
     * 清理过期的消息记录
     * @param {number} currentTime - 当前时间戳
     */
    #cleanupExpiredMessages(currentTime) {
        let cleanedCount = 0;
        
        for (const [messageId, timestamp] of this.#processedMessageTimestamps.entries()) {
            if (currentTime - timestamp > this.#config.messageIdTtl) {
                this.#processedMessageIds.delete(messageId);
                this.#processedMessageTimestamps.delete(messageId);
                cleanedCount++;
            }
        }
        
        if (cleanedCount > 0) {
            console.log(`${this.#getLogPrefix()} 清理了 ${cleanedCount} 条过期消息记录`);
            console.log(`${this.#getLogPrefix()} 当前缓存消息数：${this.#processedMessageIds.size}`);
        }
    }
    
    /**
     * 检查消息是否已处理
     * @param {string} messageId - 消息 ID
     * @param {number} messageTime - 消息时间戳
     * @returns {boolean} true-已处理/需跳过，false-未处理
     */
    #shouldSkipMessage(messageId, messageTime) {
        const currentTime = Date.now();
        
        // 检查消息是否过旧
        if (currentTime - messageTime > this.#config.messageExpiryTime) {
            console.log(`${this.#getLogPrefix()} 消息过旧，跳过：${messageId}`);
            return true;
        }
        
        // 检查是否已处理过
        if (this.#processedMessageIds.has(messageId)) {
            console.log(`${this.#getLogPrefix()} 消息已处理过，跳过：${messageId}`);
            return true;
        }
        
        return false;
    }
    
    /**
     * 记录已处理的消息
     * @param {string} messageId - 消息 ID
     */
    #recordProcessedMessage(messageId) {
        const currentTime = Date.now();
        this.#processedMessageIds.add(messageId);
        this.#processedMessageTimestamps.set(messageId, currentTime);
        console.log(`${this.#getLogPrefix()} 记录新消息：${messageId}`);
    }
    
    /**
     * 启动 WebSocket 长连接
     * @param {Function} onMessageReceived - 消息接收回调函数 (chatId, messageText) => Promise<void>
     * @returns {boolean} 启动是否成功
     */
    async start(onMessageReceived) {
        // 检查是否已经连接
        if (this.#wsClient && this.#isConnected) {
            console.log(`${this.#getLogPrefix()} WebSocket 已连接，跳过重复启动`);
            return true;
        }
        
        try {
            // 创建 WebSocket 客户端
            this.#wsClient = new lark.WSClient({
                appId: this.#config.appId,
                appSecret: this.#config.appSecret,
                loggerLevel: this.#config.logLevel === 'debug' ? lark.LoggerLevel.debug : 
                           this.#config.logLevel === 'error' ? lark.LoggerLevel.error : 
                           lark.LoggerLevel.info
            });
            
            // 启动 WebSocket 连接并注册事件处理器
            this.#wsClient.start({
                eventDispatcher: new lark.EventDispatcher({}).register({
                    'im.message.receive_v1': async (data) => {
                        const {
                            message: { chat_id, content }
                        } = data;
                        
                        console.log(`${this.#getLogPrefix()} 收到消息，聊天 ID: ${chat_id}, eventId: ${data.event_id}, create_time: ${data.create_time}`);
                        
                        // 提取消息 ID（兼容不同结构）
                        const messageId = data.event?.message?.message_id || data.message?.message_id;
                        
                        if (messageId) {
                            // 解析消息时间戳
                            const messageTime = typeof data.create_time === 'string' 
                                ? parseInt(data.create_time) 
                                : data.create_time;
                            
                            // 检查是否应该跳过此消息
                            if (this.#shouldSkipMessage(messageId, messageTime)) {
                                return {};
                            }
                            
                            // 记录已处理的消息
                            this.#recordProcessedMessage(messageId);
                            
                            // 定期清理过期记录（每处理 10 条消息清理一次）
                            if (this.#processedMessageIds.size % 10 === 0) {
                                this.#cleanupExpiredMessages(Date.now());
                            }
                        }
                        
//                        console.log(`[Feishu] 收到消息，聊天内容：${JSON.stringify(data)}`);
                        
                        // 触发回调处理消息
                        if (onMessageReceived) {
                            await onMessageReceived(chat_id, JSON.parse(content).text);
                        }
                        
                        return {};
                    }
                })
            });
            
            this.#isConnected = true;
            console.log(`${this.#getLogPrefix()} WebSocket 长连接已启动`);
            return true;
            
        } catch (error) {
            console.error(`${this.#getLogPrefix()} WebSocket 启动失败:`, error.message);
            this.#isConnected = false;
            return false;
        }
    }
    
    /**
     * 停止 WebSocket 连接
     * @returns {Promise<boolean>} 停止是否成功
     */
    async stop() {
        if (!this.#wsClient) {
            console.log(`${this.#getLogPrefix()} WebSocket 客户端未创建`);
            return false;
        }
        
        try {
            // WSClient 没有显式的 stop 方法，通过清空引用来释放资源
            this.#wsClient = null;
            this.#isConnected = false;
            this.#processedMessageIds.clear();
            this.#processedMessageTimestamps.clear();
            
            console.log(`${this.#getLogPrefix()} WebSocket 长连接已停止`);
            return true;
        } catch (error) {
            console.error(`${this.#getLogPrefix()} WebSocket 停止失败:`, error.message);
            return false;
        }
    }
    
    /**
     * 获取连接状态
     * @returns {boolean} 连接状态
     */
    isConnected() {
        return this.#isConnected;
    }
    
    /**
     * 获取已处理的消息数量
     * @returns {number} 已处理消息数量
     */
    getProcessedMessageCount() {
        return this.#processedMessageIds.size;
    }
    
    /**
     * 重置消息去重缓存
     */
    resetMessageCache() {
        this.#processedMessageIds.clear();
        this.#processedMessageTimestamps.clear();
        console.log(`${this.#getLogPrefix()} 已重置消息去重缓存`);
    }
}

/**
 * 创建飞书长连接客户端的工厂函数
 * @param {Object} config - 配置参数
 * @returns {FeishuWSClient}
 */
export function createFeishuWSClient(config) {
    return new FeishuWSClient(config);
}

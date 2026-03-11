/**
 * Agent 管理器
 * 负责管理会话映射和消息去重
 */

import { FeishuConfig } from '../config.js';

/**
 * Agent 回调事件类型
 * @typedef {Object} AgentCallbackEvents
 * @property {Function} [onSessionCreated] - 会话创建回调 (sessionId, title) => void
 * @property {Function} [onMessageReceived] - 收到消息回调 (sessionId, message) => void
 * @property {Function} [onMessageSent] - 消息发送回调 (sessionId, message, response) => void
 * @property {Function} [onError] - 错误回调 (sessionId, error) => void
 * @property {Function} [onCustomEvent] - 自定义事件回调 (eventName, data) => void
 */

/**
 * Agent 管理器配置
 * @typedef {Object} AgentManagerConfig
 * @property {IAgentStrategy} agent - Agent 策略实例
 * @property {AgentCallbackEvents} [callbacks] - Agent 回调函数集合
 * @property {number} [processingTimeout=30000] - 消息处理超时时间（毫秒）
 * @property {number} [messageIdTtl=600000] - 消息 ID 缓存 TTL（毫秒）
 */

/**
 * Agent 管理器类
 */
export class AgentManager {
    /**
     * @type {IAgentStrategy}
     */
    #agent;

    /**
     * @type {Map<string, string>}
     */
    #agentMap;

    /**
     * @type {Map<string, string>}
     */
    #sessionMap;

    /**
     * @type {Set<string>}
     */
    #processingMessages;

    /**
     * @type {number}
     */
    #processingTimeout;

    /**
     * @type {Map<string, Promise>}
     */
    #sessionLocks;

    /**
     * @type {AgentCallbackEvents}
     */
    #callbacks;

    /**
     * 创建 Agent 管理器
     * @param {AgentManagerConfig} config - 配置对象
     */
    constructor({ agent, processingTimeout, messageIdTtl, agentMap = {}, callbacks = {} }) {
        if (!agent || !(agent instanceof Object)) {
            throw new Error('Agent 管理器配置无效：缺少有效的 agent 实例');
        }

        this.#agent = agent;
        this.#agentMap = agentMap;
        this.#sessionMap = new Map();
        this.#processingMessages = new Set();
        this.#processingTimeout = processingTimeout || FeishuConfig?.messageConfig?.processingTimeout || 30000;
        this.#sessionLocks = new Map();
        this.#callbacks = callbacks;
        
        // 初始化时将回调传递给 Agent
        this.#initAgentCallbacks();
    }
    
    // 初始化时将回调传递给 Agent
    #initAgentCallbacks() {
        if (typeof this.#agent.setCallbacks === 'function') {
            this.#agent.setCallbacks(this.#createCallbackWrapper());
        }
        // 遍历 agentMap
        for (const [key, agentInstance] of Object.entries(this.#agentMap)) {
            if (typeof agentInstance.setCallbacks === 'function') {
                agentInstance.setCallbacks(this.#createCallbackWrapper());
            }
        }
    }

    /**
     * 获取日志前缀
     * @returns {string}
     */
    #getLogPrefix() {
        return `[AgentManager-${this.#agent.getName()}]`;
    }

    /**
     * 创建回调包装器（提供给 Agent 使用）
     * @returns {Object} 包装后的回调对象
     */
    #createCallbackWrapper() {
        const self = this;
        return {
            onSessionCreated: (sessionId, title) => self.#triggerCallback('onSessionCreated', sessionId, title),
            onMessageReceived: (sessionId, message) => self.#triggerCallback('onMessageReceived', sessionId, message),
            onMessageSent: (sessionId, message, response) => self.#triggerCallback('onMessageSent', sessionId, message, response),
            onError: (sessionId, error) => self.#triggerCallback('onError', sessionId, error),
            onCustomEvent: (eventName, data) => self.#triggerCallback('onCustomEvent', eventName, data)
        };
    }

    /**
     * 触发回调
     * @param {string} eventName - 事件名称
     * @param  {...any} args - 回调参数
     */
    #triggerCallback(eventName, ...args) {
        const callback = this.#callbacks[eventName];
        if (typeof callback === 'function') {
            try {
                callback(...args);
            } catch (error) {
                console.error(`${this.#getLogPrefix()} 回调执行失败 [${eventName}]:`, error.message);
            }
        }
    }

    /**
     * 注册回调函数
     * @param {string} eventName - 事件名称
     * @param {Function} callback - 回调函数
     * @returns {AgentManager} this（支持链式调用）
     */
    registerCallback(eventName, callback) {
        if (typeof callback !== 'function') {
            throw new Error(`回调必须是函数类型，当前类型：${typeof callback}`);
        }
        this.#callbacks[eventName] = callback;
        return this;
    }

    /**
     * 注销回调函数
     * @param {string} eventName - 事件名称
     * @returns {AgentManager} this（支持链式调用）
     */
    unregisterCallback(eventName) {
        delete this.#callbacks[eventName];
        return this;
    }

    /**
     * 手动触发回调（供外部调用）
     * @param {string} eventName - 事件名称
     * @param  {...any} args - 回调参数
     */
    triggerCallback(eventName, ...args) {
        this.#triggerCallback(eventName, ...args);
    }

    /**
     * 创建唯一消息键
     * @param {string} chatId - 聊天 ID
     * @param {string} userMessage - 用户消息
     * @returns {string}
     */
    #createMessageKey(chatId, userMessage) {
        return `${chatId}:${userMessage}`;
    }

    /**
     * 检查消息是否正在处理中
     * @param {string} chatId - 聊天 ID
     * @param {string} userMessage - 用户消息
     * @returns {boolean} true-正在处理/需跳过，false-可以处理
     */
    isProcessing(chatId, userMessage) {
        const messageKey = this.#createMessageKey(chatId, userMessage);
        return this.#processingMessages.has(messageKey);
    }

    /**
     * 标记消息开始处理
     * @param {string} chatId - 聊天 ID
     * @param {string} userMessage - 用户消息
     */
    markProcessing(chatId, userMessage) {
        const messageKey = this.#createMessageKey(chatId, userMessage);
        this.#processingMessages.add(messageKey);
        console.log(`${this.#getLogPrefix()} 消息开始处理：${messageKey}`);
    }

    /**
     * 标记消息处理完成
     * @param {string} chatId - 聊天 ID
     * @param {string} userMessage - 用户消息
     */
    markCompleted(chatId, userMessage) {
        const messageKey = this.#createMessageKey(chatId, userMessage);
        
        // 延迟清理处理标记，防止重复消息
        setTimeout(() => {
            this.#processingMessages.delete(messageKey);
            console.log(`${this.#getLogPrefix()} 消息处理完成，清理标记：${messageKey}`);
        }, this.#processingTimeout);
    }

    /**
     * 获取或创建会话
     * @param {string} chatId - 聊天 ID
     * @returns {Promise<string>} 会话 ID
     */
    async getSession(chatId) {
        let sessionId = this.#sessionMap.get(chatId);

        if (!sessionId) {
            const title = `feishu-${chatId}-${Date.now()}`;
            sessionId = await this.#agent.createSession(title);
            
            if (FeishuConfig?.isDebugEnabled()) {
                console.log(`${this.#getLogPrefix()} 创建新会话：${sessionId}`);
            }

            this.#sessionMap.set(chatId, sessionId);
        }

        return sessionId;
    }


     /**
      * 重置会话：删除旧会话，清理本地映射和锁，立即创建新会话
      * @param {string} chatId - 聊天 ID
      * @returns {Promise<string>} 新会话 ID
      */
     async resetSession(chatId) {
         const oldSessionId = this.#sessionMap.get(chatId);
         
         if (oldSessionId) {
         
             try {
//                 await this.#agent.deleteSession(oldSessionId); // 先不用删除服务端的会话
                 console.log(`${this.#getLogPrefix()} 已删除服务端会话: ${oldSessionId}`);
             } catch (error) {
                 console.error(`${this.#getLogPrefix()} 删除服务端会话失败:`, error.message);
             }
             
             this.#sessionMap.delete(chatId);
             this.#sessionLocks.delete(oldSessionId);
             console.log(`${this.#getLogPrefix()} 已清理本地会话映射和锁: ${chatId}`);
         }
         
         const title = `feishu-${chatId}-${Date.now()}`;
         const newSessionId = await this.#agent.createSession(title);
         this.#sessionMap.set(chatId, newSessionId);
         
         console.log(`${this.#getLogPrefix()} 已创建新会话: ${newSessionId}`);
         return newSessionId;
     }

    /**
     * 切换当前 Agent
     * @param {string} agentKey - agentMap 中的 key
     * @returns {boolean} 是否切换成功
     */
    setCurrentAgent(agentKey) {
        let newAgent;
        
        // 兼容 Map 和 Object 两种格式
        if (typeof this.#agentMap.get === 'function') {
            newAgent = this.#agentMap.get(agentKey);
        } else {
            newAgent = this.#agentMap[agentKey];
        }
        
        if (newAgent) {
            this.#agent = newAgent;
            console.log(`${this.#getLogPrefix()} 已切换 Agent: ${agentKey}`);
            return true;
        }
        console.warn(`${this.#getLogPrefix()} 切换 Agent 失败，未找到: ${agentKey}`);
        return false;
    }
     /**
      * 获取当前 Agent
      * @returns {boolean}
       */
    existsAgent(agentKey) {
        let newAgent;

        // 兼容 Map 和 Object 两种格式
        if (typeof this.#agentMap.get === 'function') {
            newAgent = this.#agentMap.has(agentKey) ? this.#agentMap.get(agentKey) : null;
        } else {
            newAgent = this.#agentMap[agentKey];
        }
        return !!newAgent;
    }

    /**
     * 获取当前 Agent 名称
     * @returns {string}
     */
    getCurrentAgentName(agentKey) {
        return  agentKey? this.#agentMap.get(agentKey)?.getName() : this.#agent.getName();
    }

    /**
     * 获取指定 Agent 实例
     * @param {string} agentKey - Agent 键
     * @returns {IAgentStrategy|null} Agent 实例，如果未找到返回 null
     */
    getAgent(agentKey) {
        if (!agentKey) {
            return this.#agent;
        }
        
        if (typeof this.#agentMap.get === 'function') {
            return this.#agentMap.get(agentKey) || null;
        } else {
            return this.#agentMap[agentKey] || null;
        }
    }

    /**
     * 列出当前 Agent 的所有会话
     * @returns {Promise<Array>} 会话列表
     */
    async listSessions() {
        return await this.#agent.listSessions();
    }

    /**
     * 获取会话消息列表
     * @param {string} sessionId - 会话 ID
     * @returns {Promise<Array>} 消息列表
     */
    async getSessionMessages(sessionId) {
        return await this.#agent.getSessionMessages(sessionId);
    }

    /**
     * 切换当前会话
     * @param {string} chatId - 聊天 ID
     * @param {string} sessionId - 新的会话 ID
     * @returns {string} 切换后的会话 ID
     */
    switchSession(chatId, sessionId) {
        this.#sessionMap.set(chatId, sessionId);
        console.log(`${this.#getLogPrefix()} 切换会话: ${chatId} -> ${sessionId}`);
        return sessionId;
    }

    async abortSession(agentKey, sessionId) {
        const curAgent = this.#agentMap.get(agentKey) || this.#agent;
        return curAgent.abort(sessionId);
    }

    /**
     * 发送消息到 Agent（带锁机制，保证同一会话的消息顺序执行）
     * @param {string} sessionId - 会话 ID
     * @param {string} message - 用户消息
     * @returns {Promise<Object>} AI 响应结果
     */
    async sendMessage(agentKey, sessionId, message) {
        // 获取或创建当前会话的锁
//        let sessionLock = this.#sessionLocks.get(sessionId);

//        if (!sessionLock) {
//            // 没有锁，直接执行
//            sessionLock = Promise.resolve();
//        }
        console.log(`${this.#getLogPrefix()} ============== agentKey:${agentKey}, 获取锁：${sessionId}, message: ${message}`);

        // 创建新的 Promise 链，确保顺序执行
//        const currentTask = sessionLock.then(async () => {
            const curAgent = this.#agentMap.get(agentKey) || this.#agent;
            return await curAgent.sendMessage(sessionId, message);
//        });
        
        // 更新锁，捕获错误防止未处理的 Promise 拒绝
//        this.#sessionLocks.set(sessionId, currentTask.catch(() => {}));

        // 等待当前任务完成
        return await currentTask;
    }

    /**
     * 记录日志
     * @param {string} level - 日志级别
     * @param {string} message - 日志内容
     * @param {Object} extra - 额外信息
     */
    async log(level, message, extra = {}) {
        await this.#agent.log(level, message, extra);
    }

/**
     * 获取会话映射
     * @returns {Map<string, string>}
     */
    getSessionMap() {
        return this.#sessionMap;
    }

    /**
     * 通过 sessionId 获取 chatId
     * @param {string} sessionId - 会话 ID
     * @returns {string|null} chatId，如果未找到返回 null
     */
    getChatIdBySessionId(sessionId) {
        if (!sessionId) {
            return null;
        }
        
        for (const [chatId, sid] of this.#sessionMap.entries()) {
            if (sid === sessionId) {
                return chatId;
            }
        }
        
        return null;
    }

    /**
     * 通过 sessionId 获取 chatId（批量查找，支持多个 sessionId）
     * @param {string[]} sessionIds - 会话 ID 数组
     * @returns {Map<string, string>} sessionId -> chatId 的映射
     */
    getChatIdsBySessionIds(sessionIds) {
        const result = new Map();
        
        if (!sessionIds || sessionIds.length === 0) {
            return result;
        }
        
        const sessionIdSet = new Set(sessionIds);
        
        for (const [chatId, sessionId] of this.#sessionMap.entries()) {
            if (sessionIdSet.has(sessionId)) {
                result.set(sessionId, chatId);
            }
        }
        
        return result;
    }

    /**
     * 获取处理中的消息数量
     * @returns {number}
     */
    getProcessingCount() {
        return this.#processingMessages.size;
    }

    /**
     * 清空会话映射
     */
    clearSessionMap() {
        this.#sessionMap.clear();
        this.#sessionLocks.clear();
        console.log(`${this.#getLogPrefix()} 已清空会话映射和锁`);
    }

    /**
     * 清空处理标记
     */
    clearProcessingMessages() {
        this.#processingMessages.clear();
        console.log(`${this.#getLogPrefix()} 已清空处理标记`);
    }

    /**
     * 获取会话锁数量
     * @returns {number}
     */
    getSessionLockCount() {
        return this.#sessionLocks.size;
    }
}

/**
 * 创建 Agent 管理器工厂函数
 * @param {AgentManagerConfig} config - 配置对象
 * @returns {AgentManager}
 */
export function createAgentManager(config) {
    return new AgentManager(config);
}

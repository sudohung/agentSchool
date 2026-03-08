/**
 * Agent 策略接口定义
 * 定义统一的 Agent 接口，便于切换不同的 AI 客户端实现
 */

/**
 * Agent 回调接口
 * @typedef {Object} AgentCallbacks
 * @property {Function} onSessionCreated - 会话创建回调 (sessionId, title) => void
 * @property {Function} onMessageReceived - 收到消息回调 (sessionId, message) => void
 * @property {Function} onMessageSent - 消息发送回调 (sessionId, message, response) => void
 * @property {Function} onError - 错误回调 (sessionId, error) => void
 * @property {Function} onCustomEvent - 自定义事件回调 (eventName, data) => void
 */

/**
 * Agent 策略接口
 * @interface IAgentStrategy
 */
export class IAgentStrategy {
    /**
     * @type {AgentCallbacks|null}
     */
    #callbacks = null;

    /**
     * 设置回调函数（由 AgentManager 在创建时调用）
     * @param {AgentCallbacks} callbacks - 回调函数集合
     */
    setCallbacks(callbacks) {
        this.#callbacks = callbacks;
    }

    /**
     * 获取回调函数
     * @protected
     * @returns {AgentCallbacks|null}
     */
    getCallbacks() {
        return this.#callbacks;
    }

    /**
     * 获取 Agent 名称
     * @returns {string}
     */
    getName() {
        throw new Error('子类必须实现 getName 方法');
    }

    /**
     * 获取 Agent 名称
     * @returns {string}
     */
    initModel(providerId, modelId) {
        throw new Error('子类必须实现 initModel 方法');
    }

    /**
     * 创建新会话
     * @param {string} title - 会话标题
     * @returns {Promise<string>} 会话 ID
     */
    async createSession(title) {
        throw new Error('子类必须实现 createSession 方法');
    }

    /**
     * 删除会话
     * @param {string} sessionId - 会话 ID
     * @returns {Promise<boolean>} 删除结果
     */
    async deleteSession(sessionId) {
        throw new Error('子类必须实现 deleteSession 方法');
    }

    /**
     * 列出所有会话
     * @returns {Promise<Array>} 会话列表
     */
    async listSessions() {
        throw new Error('子类必须实现 listSessions 方法');
    }

    /**
     * 获取会话消息列表
     * @param {string} sessionId - 会话 ID
     * @returns {Promise<Array>} 消息列表
     */
    async getSessionMessages(sessionId) {
        throw new Error('子类必须实现 getSessionMessages 方法');
    }

    /**
     * 发送消息并获取响应
     * @param {string} sessionId - 会话 ID
     * @param {string} message - 用户消息
     * @returns {Promise<Object>} AI 响应结果
     */
    async sendMessage(sessionId, message) {
        throw new Error('子类必须实现 sendMessage 方法');
    }

    /**
     * 中断会话
     * @param {string} sessionId - 会话 ID
     * @returns {Promise<Object>} AI 响应结果
     */
    async abort(sessionId) {
        throw new Error('子类必须实现 abort 方法');
    }

    /**
     * 记录日志
     * @param {string} level - 日志级别
     * @param {string} message - 日志内容
     * @param {Object} extra - 额外信息
     */
    async log(level, message, extra = {}) {
        console.log(`[${this.getName()}] ${level}: ${message}`, extra);
    }
}

/**
 * 会话管理器
 * 职责：
 *  1. chatId -> sessionId 映射
 *  2. chatId -> agentKey 上下文（每个群可独立切换模型）
 *  3. 消息处理去重（防止并发重复处理同一消息）
 *  4. 同一会话的请求串行排队（修复旧版残缺的锁实现）
 */

import { BotConfig } from '../config/bot-config.js';
import { LogPrefix } from '../constants.js';

/**
 * 会话管理器类
 */
export class SessionManager {
    /** @type {import('./agent-registry.js').AgentRegistry} */
    #registry;
    /** @type {Map<string, string>} chatId -> sessionId */
    #sessionMap = new Map();
    /** @type {Map<string, string>} chatId -> agentKey */
    #agentContextMap = new Map();
    /** @type {Set<string>} 处理中的消息键 */
    #processingMessages = new Set();
    /** @type {number} 处理标记清理延迟 */
    #processingTimeout;
    /** @type {Map<string, Promise>} sessionId -> 串行任务链 */
    #sessionLocks = new Map();

    constructor(registry) {
        if (!registry) throw new Error('SessionManager 初始化失败：缺少 AgentRegistry');
        this.#registry = registry;
        this.#processingTimeout = BotConfig.messageConfig.processingTimeout;
    }

    #log(msg) {
        console.log(`${LogPrefix.AGENT_MGR} ${msg}`);
    }

    // ==================== 消息去重 ====================

    #messageKey(chatId, message) {
        return `${chatId}:${message}`;
    }

    isProcessing(chatId, message) {
        return this.#processingMessages.has(this.#messageKey(chatId, message));
    }

    markProcessing(chatId, message) {
        this.#processingMessages.add(this.#messageKey(chatId, message));
    }

    markCompleted(chatId, message) {
        const key = this.#messageKey(chatId, message);
        // 延迟清理，规避飞书重推导致的重复触发
        setTimeout(() => this.#processingMessages.delete(key), this.#processingTimeout);
    }

    // ==================== Agent 上下文 ====================

    /**
     * 获取 chat 当前生效的 Agent 实例
     * @param {string} chatId
     * @returns {{key:string, agent:OpencodeAgent}}
     */
    resolveAgent(chatId) {
        const key = this.#agentContextMap.get(chatId) || this.#registry.getDefaultKey();
        return { key, agent: this.#registry.getAgent(key) };
    }

    /**
     * 切换 chat 的 Agent
     * @returns {boolean} 是否成功
     */
    switchAgent(chatId, agentKey) {
        if (!this.#registry.hasAgent(agentKey)) {
            return false;
        }
        this.#agentContextMap.set(chatId, agentKey);
        this.#log(`chat=${chatId} 已切换 Agent: ${agentKey}`);
        return true;
    }

    // ==================== 会话生命周期 ====================

    /** @type {Map<string, Promise<string>>} chatId -> 创建会话中的 Promise（防竞态） */
    #creatingSessions = new Map();

    /**
     * 获取（或创建）chat 对应的会话
     * @returns {Promise<string>} sessionId
     */
    async getSession(chatId) {
        let sessionId = this.#sessionMap.get(chatId);
        if (sessionId) return sessionId;

        // 创建锁：并发请求只创建一次会话
        let creating = this.#creatingSessions.get(chatId);
        if (!creating) {
            creating = (async () => {
                const { agent } = this.resolveAgent(chatId);
                const id = await agent.createSession(`feishu-${chatId}-${Date.now()}`);
                this.#sessionMap.set(chatId, id);
                this.#log(`chat=${chatId} 创建新会话: ${id}`);
                return id;
            })().finally(() => this.#creatingSessions.delete(chatId));
            this.#creatingSessions.set(chatId, creating);
        }
        return creating;
    }

    /**
     * 重置会话：丢弃旧映射，创建新会话
     * @returns {Promise<string>} 新 sessionId
     */
    async resetSession(chatId) {
        const old = this.#sessionMap.get(chatId);
        this.#sessionMap.delete(chatId);
        this.#sessionLocks.delete(old);
        const { agent } = this.resolveAgent(chatId);
        const sessionId = await agent.createSession(`feishu-${chatId}-${Date.now()}`);
        this.#sessionMap.set(chatId, sessionId);
        this.#log(`chat=${chatId} 重置会话 ${old} -> ${sessionId}`);
        return sessionId;
    }

    /** 切换到已有会话 */
    switchSession(chatId, sessionId) {
        this.#sessionMap.set(chatId, sessionId);
        this.#log(`chat=${chatId} 切换会话 -> ${sessionId}`);
    }

    /**
     * sessionId -> chatId 反查
     * @returns {string|null}
     */
    getChatIdBySessionId(sessionId) {
        if (!sessionId) return null;
        for (const [chatId, sid] of this.#sessionMap.entries()) {
            if (sid === sessionId) return chatId;
        }
        return null;
    }

    // ==================== 消息发送（串行化） ====================

    /**
     * 向会话发送消息，同一会话内的请求串行执行
     * @param {string} chatId
     * @param {string} message
     * @returns {Promise<Object>} AI 响应
     */
    async sendMessage(chatId, message) {
        const sessionId = await this.getSession(chatId);
        const { key, agent } = this.resolveAgent(chatId);

        // 正确实现的串行锁：以 sessionId 为粒度排队，任务完成后释放
        const previous = this.#sessionLocks.get(sessionId) || Promise.resolve();
        const task = previous.then(() => agent.sendMessage(sessionId, message));
        const guarded = task.catch(() => {});
        this.#sessionLocks.set(sessionId, guarded);
        try {
            this.#log(`chat=${chatId} agent=${key} 发送消息到会话 ${sessionId}`);
            return await task;
        } finally {
            if (this.#sessionLocks.get(sessionId) === guarded) {
                this.#sessionLocks.delete(sessionId);
            }
        }
    }

    // ==================== 代理查询 ====================

    /**
     * 列出当前 Agent 的所有会话
     * 所有 Agent 共享同一 OpenCode client，会话列表全局一致，取默认 Agent 即可
     */
    async listSessions() {
        const { agent } = this.resolveAgent('');
        return agent.listSessions();
    }

    /** 获取会话消息（同上，client 共享） */
    async getSessionMessages(sessionId) {
        const { agent } = this.resolveAgent('');
        return agent.getSessionMessages(sessionId);
    }

    /** 中断 chat 当前会话 */
    async abortSession(chatId) {
        const sessionId = await this.getSession(chatId);
        const { agent } = this.resolveAgent(chatId);
        await agent.abort(sessionId);
        return sessionId;
    }
}

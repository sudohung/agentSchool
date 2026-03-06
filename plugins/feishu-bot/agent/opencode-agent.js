/**
 * OpenCode Agent 实现
 * 基于 @opencode-ai/sdk 的 Agent 策略实现
 */

import { IAgentStrategy } from './agent-strategy.js';

/**
 * OpenCode Agent 策略实现
 */
export class OpencodeAgent extends IAgentStrategy {

    /**
     * @param {Object} client - OpenCode 客户端实例
     */
    constructor(client) {
        super();
        if (!client) {
            throw new Error('OpencodeAgent 初始化失败：client 参数不能为空');
        }
        console.log('[OpencodeAgent] 初始化，client 类型:', typeof client, client ? '有值' : '空值');
        this.client = client;

        this.model = {providerID: "CodingPlan",modelID: "glm-5"}

    }

    initModel(providerID, modelID ) {
        // 这里可以添加模型初始化逻辑，例如预加载模型列表或设置默认模型
        this.model = {providerID: providerID,modelID: modelID }
        return this;
    }

    /**
     * 获取 Agent 名称
     * @returns {string}
     */
    getName() {
        return 'OpencodeAgent';
    }

    /**
     * 创建新会话
     * @param {string} title - 会话标题
     * @returns {Promise<string>} 会话 ID
     */
    async createSession(title) {
        const session = await this.client.session.create({
            body: { title }
        });

        // 兼容不同响应格式
        const sessionId = session.id || session.data?.id || session.path?.id;

        if (!sessionId) {
            console.error(`[${this.getName()}] Session 创建成功但未获取到 ID:`, session);
            throw new Error('无法获取 Session ID');
        }

        // 触发会话创建回调
        const callbacks = this.getCallbacks();
        if (callbacks?.onSessionCreated) {
            callbacks.onSessionCreated(sessionId, title);
        }

        return sessionId;
    }

    /**
     * 发送消息并获取响应
     * @param {string} sessionId - 会话 ID
     * @param {string} message - 用户消息
     * @returns {Promise<Object>} AI 响应结果
     */
    async sendMessage(sessionId, message) {
        try {
            // 触发消息发送前回调
            const callbacks = this.getCallbacks();
            if (callbacks?.onMessageReceived) {
                callbacks.onMessageReceived(sessionId, message);
            }

            const result = await this.client.session.prompt({
                path: { id: sessionId },
                body: {
                    model: this.model || {}, // 使用默认模型
                    parts: [{ type: "text", text: message }],
                },
            });

            // 触发消息发送后回调
            if (callbacks?.onMessageSent) {
                callbacks.onMessageSent(sessionId, message, result);
            }

            return result;
        } catch (error) {
            // 触发错误回调
            const callbacks = this.getCallbacks();
            if (callbacks?.onError) {
                callbacks.onError(sessionId, error);
            }
            throw error;
        }
    }

    /**
     * 记录日志
     * @param {string} level - 日志级别
     * @param {string} message - 日志内容
     * @param {Object} extra - 额外信息
     */
    async log(level, message, extra = {}) {
        await this.client.app.log({
            body: {
                service: "feishu-plugin",
                level,
                message,
                extra
            }
        });
    }
}

/**
 * 创建 OpenCode Agent 工厂函数
 * @param {Object} client - OpenCode 客户端
 * @returns {OpencodeAgent}
 */
export function createOpencodeAgent(client) {
    return new OpencodeAgent(client);
}

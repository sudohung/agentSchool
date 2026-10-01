/**
 * OpenCode Agent 策略实现
 * 封装 @opencode-ai/sdk 的会话与消息能力
 */

import { BotConfig } from '../config/bot-config.js';
import { LogPrefix } from '../constants.js';

/**
 * OpenCode Agent 类
 */
export class OpencodeAgent {
    /**
     * @param {Object} client - OpenCode SDK 客户端
     * @param {{provider:string, model:string}} model - 模型定义
     */
    constructor(client, model) {
        if (!client) throw new Error('OpencodeAgent 初始化失败：client 为空');
        if (!model?.provider || !model?.model) throw new Error('OpencodeAgent 初始化失败：模型定义不完整');
        this.client = client;
        this.model = { providerID: model.provider, modelID: model.model };
        this.callbacks = {};
    }

    setCallbacks(callbacks) {
        this.callbacks = callbacks || {};
    }

    #trigger(name, ...args) {
        try {
            this.callbacks[name]?.(...args);
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} 回调执行失败 [${name}]: ${error.message}`);
        }
    }

    /** @returns {string} agent 展示名 */
    getName() {
        return `${this.model.providerID}/${this.model.modelID}`;
    }

    /**
     * 创建新会话
     * @param {string} title
     * @returns {Promise<string>} 会话 ID
     */
    async createSession(title) {
        const session = await this.client.session.create({ body: { title } });
        const sessionId = session?.id || session?.data?.id;
        if (!sessionId) {
            throw new Error(`创建会话成功但未返回 ID: ${JSON.stringify(session)}`);
        }
        this.#trigger('onSessionCreated', sessionId, title);
        return sessionId;
    }

    /**
     * 发送消息（阻塞式 prompt）
     * @param {string} sessionId
     * @param {string} message
     */
    async sendMessage(sessionId, message) {
        if (!sessionId || !message) throw new Error('发送消息失败：sessionId/message 为空');
        this.#trigger('onMessageReceived', sessionId, message);
        try {
            const result = await this.client.session.prompt({
                path: { id: sessionId },
                body: {
                    model: this.model,
                    parts: [{ type: 'text', text: message }],
                },
            });
            this.#trigger('onMessageSent', sessionId, message, result);
            return result;
        } catch (error) {
            this.#trigger('onError', sessionId, error);
            throw error;
        }
    }

    /** 中断会话 */
    async abort(sessionId) {
        try {
            await this.client.session.abort({ path: { id: sessionId } });
        } catch (error) {
            this.#trigger('onError', sessionId, error);
            throw error;
        }
    }

    /** 列出所有会话 */
    async listSessions() {
        const res = await this.client.session.list();
        return res?.data || res || [];
    }

    /** 获取会话消息列表 */
    async getSessionMessages(sessionId) {
        const res = await this.client.session.messages({ path: { id: sessionId } });
        return res?.data || res || [];
    }

    /**
     * 回答工具提问（question.reply 闭环）
     * 注意：SDK 1.18.x 未生成 question 接口，此处直接调用服务端 HTTP API
     * @param {string} requestId - question 请求 ID（que_xxx）
     * @param {string[][]} answers - 答案列表，每个问题对应一个选中 label 数组
     * @param {string} [sessionId] - 所属会话 ID，用于 404 时按会话重定位真实 requestId
     * @returns {Promise<boolean>} 是否成功
     */
    async replyQuestion(requestId, answers, sessionId) {
        try {
            console.log(`${LogPrefix.AGENT_MGR} question.reply 请求: requestId=${requestId}, sessionId=${sessionId || '无'}, answers=${JSON.stringify(answers)}`);
            let res = await this.#postQuestionReply(requestId, answers);

            // 404 自愈：按钮/记忆中的 requestId 与服务端待答问题不匹配（过期、多实例错位等）
            // 按会话 ID 重新定位当前待答的 requestId 后重试一次
            if (res.status === 404 && sessionId) {
                const realId = await this.#findPendingQuestionId(sessionId);
                if (realId && realId !== requestId) {
                    console.warn(`${LogPrefix.AGENT_MGR} question.reply 404，requestId 不匹配，重定位: ${requestId} -> ${realId}`);
                    res = await this.#postQuestionReply(realId, answers);
                } else {
                    // 打印服务端当前待答列表，协助定位 ID 错位原因
                    await this.#logPendingQuestions();
                }
            }

            if (!res.ok) {
                console.error(`${LogPrefix.AGENT_MGR} question.reply HTTP ${res.status}`);
                return false;
            }
            return true;
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} question.reply 失败: ${error.message}`);
            return false;
        }
    }

    /**
     * 调用 question.reply HTTP 接口
     */
    async #postQuestionReply(requestId, answers) {
        const url = `${BotConfig.getOpencodeBaseUrl()}/question/${encodeURIComponent(requestId)}/reply`;
        return await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers }),
        });
    }

    /**
     * 按会话 ID 查询当前待答提问的真实 requestId
     * @returns {Promise<string|null>}
     */
    async #findPendingQuestionId(sessionId) {
        try {
            const res = await fetch(`${BotConfig.getOpencodeBaseUrl()}/question`);
            if (!res.ok) return null;
            const list = await res.json();
            const hit = (Array.isArray(list) ? list : []).find((q) => q?.sessionID === sessionId);
            return hit?.id || null;
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} 查询待答提问失败: ${error.message}`);
            return null;
        }
    }

    /**
     * 打印服务端当前待答提问列表（诊断 requestId 错位）
     */
    async #logPendingQuestions() {
        try {
            const res = await fetch(`${BotConfig.getOpencodeBaseUrl()}/question`);
            if (!res.ok) return;
            const list = await res.json();
            const brief = (Array.isArray(list) ? list : []).map((q) => ({
                id: q.id,
                sessionID: q.sessionID,
            }));
            console.warn(`${LogPrefix.AGENT_MGR} 服务端当前待答提问: ${JSON.stringify(brief) || '[]'}`);
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} 查询待答提问列表失败: ${error.message}`);
        }
    }

    /**
     * 拒绝工具提问（question.reject 闭环）
     * 用于交互超时兜底：拒绝后 OpenCode 会话不会永久挂起
     * @param {string} requestId - question 请求 ID（que_xxx）
     * @returns {Promise<boolean>} 是否成功
     */
    async rejectQuestion(requestId) {
        try {
            const url = `${BotConfig.getOpencodeBaseUrl()}/question/${encodeURIComponent(requestId)}/reject`;
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            if (!res.ok) {
                console.error(`${LogPrefix.AGENT_MGR} question.reject HTTP ${res.status}`);
                return false;
            }
            return true;
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} question.reject 失败: ${error.message}`);
            return false;
        }
    }

    /**
     * 响应权限请求
     * @param {string} sessionId
     * @param {string} permissionId
     * @param {'once'|'always'|'reject'} response
     */
    async respondPermission(sessionId, permissionId, response) {
        try {
            const body = { response };
            const path = { id: sessionId, permissionID: permissionId };
            // 优先使用新版 SDK 的 session.permissions.respond，降级到旧版顶层方法
            const respond = this.client.session?.permissions?.respond;
            if (typeof respond === 'function') {
                await respond.call(this.client.session.permissions, { path, body });
            } else if (typeof this.client.postSessionIdPermissionsPermissionId === 'function') {
                await this.client.postSessionIdPermissionsPermissionId({ path, body });
            } else {
                throw new Error('SDK 不支持权限响应接口');
            }
            return true;
        } catch (error) {
            console.error(`${LogPrefix.AGENT_MGR} 权限响应失败: ${error.message}`);
            return false;
        }
    }
}

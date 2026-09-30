/**
 * 交互管理器
 * 维护每个 chat 的"待回复交互"（工具提问 / 权限请求），
 * 实现用户回复 -> OpenCode 的闭环（旧版只发通知不回传）
 */

import { PendingInteraction, PermissionAction, LogPrefix } from '../constants.js';
import { sendTextMessage } from '../feishu/message-sender.js';

/** 待处理交互过期时间（毫秒） */
const INTERACTION_TTL = 10 * 60 * 1000;

/**
 * 交互管理器类
 */
export class InteractionManager {
    /** @type {Map<string, {type:string, requestId:string, sessionId:string, questions?:Array, createdAt:number}>} */
    #pending = new Map();
    /** @type {import('../agent/session-manager.js').SessionManager} */
    #sessionManager;
    /** @type {import('../feishu/chat-service.js').ChatService} */
    #chatService;

    constructor(sessionManager, chatService) {
        this.#sessionManager = sessionManager;
        this.#chatService = chatService;
    }

    /**
     * 注册工具提问
     * @param {string} chatId
     * @param {{id:string, sessionID:string, questions:Array}} properties
     */
    async registerQuestion(chatId, properties) {
        const requestId = properties.id;
        const sessionId = properties.sessionID;
        if (!chatId || !requestId || !sessionId) {
            console.warn(`${LogPrefix.EVENTS} 提问事件缺少关键字段，忽略`);
            return;
        }

        // 清理过期交互
        this.#cleanup();

        const questions = properties.questions || [];
        const lines = questions.map((q, i) => {
            const options = (q.options || []).map((o) => o.label).join(' / ');
            return `${i + 1}. ${q.question}（${q.header}）\n   选项：${options || '自由回答'}`;
        }).join('\n');

        this.#pending.set(chatId, {
            type: PendingInteraction.QUESTION,
            requestId,
            sessionId,
            questions,
            createdAt: Date.now(),
        });

        await sendTextMessage(
            this.#chatService,
            chatId,
            `🤔 工具提问（回复选项内容或直接回答）：\n${lines}`,
        );
    }

    /**
     * 注册权限请求
     * @param {string} chatId
     * @param {{id:string, sessionID:string, permission:string, patterns?:string[]}} properties
     */
    async registerPermission(chatId, properties) {
        const permissionId = properties.id;
        const sessionId = properties.sessionID;
        if (!chatId || !permissionId || !sessionId) {
            console.warn(`${LogPrefix.EVENTS} 权限事件缺少关键字段，忽略`);
            return;
        }

        this.#cleanup();

        this.#pending.set(chatId, {
            type: PendingInteraction.PERMISSION,
            requestId: permissionId,
            sessionId,
            permission: properties.permission,
            patterns: properties.patterns,
            createdAt: Date.now(),
        });

        await sendTextMessage(
            this.#chatService,
            chatId,
            `🔐 工具调用权限请求：${properties.permission}\n内容：${(properties.patterns || []).join(', ')}\n回复 /permit:once、/permit:always 或 /permit:reject`,
        );
    }

    /**
     * 用户消息回复路由：存在待处理交互时优先消费
     * 注意：以 / 开头的命令不在此消费，放行给命令路由（否则 /permit、/new 会被吞掉）
     * @param {string} chatId
     * @param {string} message - 用户消息（非命令）
     * @returns {Promise<boolean>} 是否已消费
     */
    async routeReply(chatId, message) {
        const pending = this.#pending.get(chatId);
        if (!pending || message.trim().startsWith('/')) return false;

        if (pending.type === PendingInteraction.QUESTION) {
            // 按问题数量构建答案：回复恰好是某问题的选项 label 时按选项作答，否则用原文
            const answers = (pending.questions || []).map((q) => {
                const labels = (q.options || []).map((o) => o.label);
                return labels.includes(message.trim()) ? [message.trim()] : [message];
            });
            const { agent } = this.#sessionManager.resolveAgent(chatId);
            const ok = await agent.replyQuestion(pending.requestId, answers);
            this.#pending.delete(chatId);
            await sendTextMessage(
                this.#chatService,
                chatId,
                ok ? `已回答提问：${message}` : '回答提交失败，请重试或使用 /abort 中断',
            );
            return true;
        }

        // 权限请求等待期：提示用户使用 /permit 命令
        await sendTextMessage(
            this.#chatService,
            chatId,
            '存在待处理的权限请求，请回复 /permit:once、/permit:always 或 /permit:reject',
        );
        return true;
    }

    /**
     * 响应权限请求（由 /permit 命令触发）
     * @param {string} chatId
     * @param {string} action - once/always/reject
     * @returns {Promise<boolean>}
     */
    async respondPermission(chatId, action) {
        const pending = this.#pending.get(chatId);
        if (!pending || pending.type !== PendingInteraction.PERMISSION) {
            return false;
        }
        if (![PermissionAction.ONCE, PermissionAction.ALWAYS, PermissionAction.REJECT].includes(action)) {
            await sendTextMessage(this.#chatService, chatId, '无效操作，请使用 once / always / reject');
            return true;
        }

        const { agent } = this.#sessionManager.resolveAgent(chatId);
        const ok = await agent.respondPermission(pending.sessionId, pending.requestId, action);
        this.#pending.delete(chatId);
        await sendTextMessage(
            this.#chatService,
            chatId,
            ok
                ? `已${action === PermissionAction.REJECT ? '拒绝' : '允许'}权限请求（${action}）`
                : '权限响应失败，请重试',
        );
        return true;
    }

    /**
     * 清理过期交互
     */
    #cleanup() {
        const now = Date.now();
        for (const [chatId, pending] of this.#pending.entries()) {
            if (now - pending.createdAt > INTERACTION_TTL) {
                this.#pending.delete(chatId);
                console.log(`${LogPrefix.EVENTS} 清理过期交互: chat=${chatId} type=${pending.type}`);
            }
        }
    }
}

/**
 * 交互管理器
 * 维护每个 chat 的"待回复交互"（工具提问 / 权限请求），
 * 实现用户回复 -> OpenCode 的闭环（旧版只发通知不回传）
 */

import { PendingInteraction, PermissionAction, CardActionType, LogPrefix } from '../constants.js';
import { sendTextMessage, sendInteractiveCard } from '../feishu/message-sender.js';
import { buildQuestionCard, buildReceiptCard } from '../feishu/card-builder.js';
import { sanitizeDeep, sanitizeText } from '../security/sanitizer.js';

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
     * 主路径：发送带选项按钮的卡片（点击按钮闭环）；发送失败降级为纯文本（打字回复闭环）
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
        await this.#cleanup();

        const questions = sanitizeDeep(properties.questions || [], '提问卡片');
        this.#pending.set(chatId, {
            type: PendingInteraction.QUESTION,
            requestId,
            sessionId,
            questions,
            createdAt: Date.now(),
        });

        try {
            await sendInteractiveCard(
                this.#chatService,
                chatId,
                buildQuestionCard(questions, requestId),
            );
        } catch (error) {
            console.warn(`${LogPrefix.EVENTS} 提问卡片发送失败，降级为文本: ${error.message}`);
            const lines = questions.map((q, i) => {
                const options = (q.options || []).map((o) => o.label).join(' / ');
                return `${i + 1}. ${q.question}（${q.header}）\n   选项：${options || '自由回答'}`;
            }).join('\n');
            await sendTextMessage(
                this.#chatService,
                chatId,
                `🤔 工具提问（回复选项内容或直接回答）：\n${lines}`,
            );
        }
    }

    /**
     * 处理卡片按钮点击（card.action.trigger 回调入口，由网关注册）
     * 返回回执卡片 JSON，飞书会原地替换原提问卡片；非本机器人动作返回 null 不处理
     * @param {Object} data - 卡片回调数据（operator/action/context）
     * @returns {Promise<Object|null>} 回执卡片 JSON
     */
    async handleCardAction(data) {
        // 兼容 schema：字段可能在顶层或 event 子对象中
        const payload = data?.event?.action ? data.event : data || {};
        const context = payload.context || {};
        const chatId = context.open_chat_id || payload.open_chat_id;
        const value = payload.action?.value;
        console.log(`${LogPrefix.EVENTS} 卡片按钮解析: chatId=${chatId}, value=${JSON.stringify(value)}`);

        // 非提问按钮（其他卡片/其他应用）不处理
        if (!chatId || !value || value.type !== CardActionType.QUESTION_REPLY) {
            console.log(`${LogPrefix.EVENTS} 非提问按钮动作，忽略: type=${value?.type}`);
            return null;
        }

        const pending = this.#pending.get(chatId);
        console.log(`${LogPrefix.EVENTS} 待答交互: ${pending ? `requestId=${pending.requestId}, sessionId=${pending.sessionId}, 按钮requestId=${value.requestId}` : '无'}`);
        const expired = !pending
            || pending.type !== PendingInteraction.QUESTION
            || pending.requestId !== value.requestId;
        if (expired) {
            return buildReceiptCard(
                '⚠️ 交互已失效',
                '该提问已过期或已处理，可直接输入新消息继续对话',
                'grey',
            );
        }

        const qIndex = Number(value.qIndex);
        const label = String(value.label || '');
        // 按问题顺序构建答案：点击的问题用所选选项，其余问题留空（单问题场景即完整作答）
        const answers = (pending.questions || []).map((q, idx) => (idx === qIndex ? [label] : []));
        const { agent } = this.#sessionManager.resolveAgent(chatId);
        const ok = await agent.replyQuestion(pending.requestId, answers, pending.sessionId);
        if (!ok) {
            // 保留 pending，用户可继续打字回复或再点按钮重试
            return buildReceiptCard(
                '❌ 提交失败',
                `「${label}」提交失败，请直接打字回复重试`,
                'red',
            );
        }
        this.#pending.delete(chatId);
        return buildReceiptCard('✅ 已回答', `选择：**${label}**`);
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

        await this.#cleanup();

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
            `🔐 工具调用权限请求：${properties.permission}\n内容：${sanitizeText((properties.patterns || []).join(', '), '权限请求')}\n回复 /permit:once、/permit:always 或 /permit:reject`,
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
            const ok = await agent.replyQuestion(pending.requestId, answers, pending.sessionId);
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
     * 超时的工具提问主动调 question.reject，避免 OpenCode 会话永久挂起等待
     */
    async #cleanup() {
        const now = Date.now();
        for (const [chatId, pending] of this.#pending.entries()) {
            if (now - pending.createdAt <= INTERACTION_TTL) continue;
            this.#pending.delete(chatId);
            console.log(`${LogPrefix.EVENTS} 清理过期交互: chat=${chatId} type=${pending.type}`);
            if (pending.type === PendingInteraction.QUESTION) {
                const { agent } = this.#sessionManager.resolveAgent(chatId);
                const ok = await agent.rejectQuestion(pending.requestId);
                if (!ok) {
                    console.warn(`${LogPrefix.EVENTS} 超时提问拒绝失败: request=${pending.requestId}`);
                }
            }
        }
    }
}

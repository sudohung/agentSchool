/**
 * OpenCode 事件监听器
 * 订阅 OpenCode 事件流，处理：
 *  - message.part.updated：流式更新飞书卡片（reasoning + text）
 *  - session.idle：最终确认，清理流式状态
 *  - question.asked / permission.asked：转发用户并等待回复（闭环）
 *  - session.status / session.error：重试与异常通知
 */

import { BotConfig } from '../config/bot-config.js';
import { OcEventType, PartType, LogPrefix } from '../constants.js';
import { authHeaders } from '../agent/opencode-agent.js';
import { sendCardMessage, updateMessage, recallMessage } from '../feishu/message-sender.js';
import { sanitizeText } from '../security/sanitizer.js';
import { sendWebhookMessage } from '../webhook/webhook-sender.js';
import { InteractionManager } from './interaction-manager.js';

/** 流式更新节流间隔（毫秒），避免频繁调用飞书 API */
const STREAM_THROTTLE = 1500;
/** 事件转发前的短暂等待（毫秒）：等流式占位消息先落地 */
const EVENT_DISPATCH_DELAY = 500;
/** 事件订阅重连基础等待（毫秒），指数退避 */
const RECONNECT_BASE_DELAY = 2000;
/** 重连退避上限（毫秒） */
const RECONNECT_MAX_DELAY = 60_000;

/**
 * 事件监听器类
 */
export class OpencodeListener {
    /** @type {import('../agent/session-manager.js').SessionManager} */
    #sessionManager;
    /** @type {import('../feishu/chat-service.js').ChatService} */
    #chatService;
    /** @type {InteractionManager} */
    #interaction;
    /** @type {Map<string, {messageId:string, content:string, updatedAt:number}>} chatId -> 流式状态 */
    #streamStates = new Map();
    /** @type {Object|null} API 通道事件路由（Agent API 会话的 question/permission 事件） */
    #apiRouter;

    constructor({ opencodeClient, getClient, getBaseUrl, sessionManager, chatService, apiRouter }) {
        // getClient：函数，返回最新 OpenCode 客户端（支持配置热更新后重连用新地址）
        this.#getClient = getClient || (() => opencodeClient);
        if (!opencodeClient && !getClient) {
            throw new Error('OpencodeListener 初始化失败：缺少 opencodeClient 或 getClient');
        }
        this.#getBaseUrl = getBaseUrl || (() => BotConfig.getOpencodeBaseUrl());
        this.#sessionManager = sessionManager;
        this.#chatService = chatService;
        this.#apiRouter = apiRouter || null;
        this.#interaction = new InteractionManager(sessionManager, chatService);
    }

    /** @type {Function} 返回最新 OpenCode SDK 客户端 */
    #getClient;
    /** @type {Function} 返回最新 OpenCode 服务地址（用于 v2 原生事件流） */
    #getBaseUrl;
    /** @type {'v1'|'v2'|''} 协议版本缓存 */
    #version = '';
    /** @type {string} 协议缓存对应的服务地址（地址变更时重新探测） */
    #versionBaseUrl = '';
    /** @type {AbortController|null} v2 事件流中止控制器（强制重连用） */
    #abortController = null;

    /** 提供给消息处理器的交互路由（question/permission 回复闭环 + 卡片按钮回调） */
    getInteraction() {
        return {
            routeReply: (chatId, message) => this.#interaction.routeReply(chatId, message),
            respondPermission: (chatId, action) => this.#interaction.respondPermission(chatId, action),
            handleCardAction: (data) => this.#interaction.handleCardAction(data),
        };
    }

    /**
     * 强制重建事件订阅（探活恢复/实例重启后调用）
     * v2 通过 abort 当前 SSE 请求立即重连；v1 依赖服务重启时连接自然断开
     */
    reconnect() {
        if (this.#abortController) {
            console.warn(`${LogPrefix.EVENTS} 收到重连指令，重建 OpenCode 事件流`);
            this.#abortController.abort();
            return;
        }
        console.log(`${LogPrefix.EVENTS} 收到重连指令（当前无活动 v2 事件流，等待主循环重连）`);
    }

    /**
     * 启动事件订阅主循环
     * 服务端不可用或流断开时自动重连（指数退避，封顶 60s）
     */
    async start() {
        let delay = RECONNECT_BASE_DELAY;
        for (;;) {
            try {
                const version = await this.#detectVersion();
                if (version === 'v2') {
                    // v2 服务端事件流为 GET /api/event（v1 SDK 的 /event 在 v2 上会立即断开）
                    await this.#subscribeV2(() => { delay = RECONNECT_BASE_DELAY; });
                } else {
                    const client = this.#getClient();
                    if (!client) throw new Error('OpenCode 客户端未初始化');
                    const events = await client.event.subscribe();
                    delay = RECONNECT_BASE_DELAY;
                    console.log(`${LogPrefix.EVENTS} 已订阅 OpenCode 事件流`);

                    for await (const event of events.stream) {
                        try {
                            await this.#dispatch(event);
                        } catch (error) {
                            console.error(`${LogPrefix.EVENTS} 事件处理异常 [${event?.type}]: ${error.message}`);
                        }
                    }
                    console.warn(`${LogPrefix.EVENTS} 事件流已断开，准备重连...`);
                }
            } catch (error) {
                console.error(`${LogPrefix.EVENTS} 事件订阅失败: ${error.message}`);
            }
            await new Promise((r) => setTimeout(r, delay));
            delay = Math.min(delay * 2, RECONNECT_MAX_DELAY);
        }
    }

    /**
     * 探测 OpenCode 协议版本（带缓存，服务地址变更时重新探测）
     * @returns {Promise<'v1'|'v2'>}
     */
    async #detectVersion() {
        const baseUrl = (this.#getBaseUrl?.() || '').replace(/\/+$/, '');
        if (!baseUrl) return 'v1';
        if (this.#version && this.#versionBaseUrl === baseUrl) return this.#version;
        this.#versionBaseUrl = baseUrl;
        try {
            const res = await fetch(`${baseUrl}/api/info`, { headers: authHeaders() });
            if (res.ok) {
                const info = await res.json().catch(() => null);
                if (String(info?.version || '').startsWith('2')) {
                    this.#version = 'v2';
                    return this.#version;
                }
            }
        } catch {
            // 探测失败按 v1 处理
        }
        this.#version = 'v1';
        return this.#version;
    }

    /**
     * 订阅 v2 原生 SSE 事件流（GET /api/event），并转换为内部统一事件后分发
     * @param {Function} onOpen 订阅成功回调（用于重置重连退避）
     */
    async #subscribeV2(onOpen) {
        const baseUrl = (this.#getBaseUrl?.() || '').replace(/\/+$/, '');
        if (!baseUrl) throw new Error('OpenCode 服务地址未配置');
        const controller = new AbortController();
        this.#abortController = controller;
        try {
            const res = await fetch(`${baseUrl}/api/event`, {
                headers: { Accept: 'text/event-stream', ...authHeaders() },
                signal: controller.signal,
            });
            if (!res.ok || !res.body) throw new Error(`v2 事件流 HTTP ${res.status}`);
            onOpen?.();
            console.log(`${LogPrefix.EVENTS} 已订阅 OpenCode v2 事件流`);

            const decoder = new TextDecoder();
            let buffer = '';
            for await (const chunk of res.body) {
                buffer += decoder.decode(chunk, { stream: true });
                let idx;
                while ((idx = buffer.indexOf('\n')) >= 0) {
                    const line = buffer.slice(0, idx).replace(/\r$/, '');
                    buffer = buffer.slice(idx + 1);
                    if (!line.startsWith('data:')) continue;
                    const payload = line.slice(5).trim();
                    if (!payload) continue;
                    let raw;
                    try {
                        raw = JSON.parse(payload);
                    } catch {
                        continue;
                    }
                    const event = this.#translateV2(raw);
                    if (!event) continue;
                    try {
                        await this.#dispatch(event);
                    } catch (error) {
                        console.error(`${LogPrefix.EVENTS} 事件处理异常 [${event?.type}]: ${error.message}`);
                    }
                }
            }
            console.warn(`${LogPrefix.EVENTS} 事件流已断开，准备重连...`);
        } finally {
            if (this.#abortController === controller) this.#abortController = null;
        }
    }

    /**
     * v2 事件结构 {type, data} -> 内部统一的 v1 风格事件 {type, properties}
     * @param {{type?:string, data?:Object}} raw
     * @returns {{type:string, properties:Object}|null}
     */
    #translateV2(raw) {
        const data = raw?.data || {};
        switch (raw?.type) {
            case 'session.text.delta':
                return {
                    type: OcEventType.MESSAGE_PART_UPDATED,
                    properties: { sessionID: data.sessionID, part: { sessionID: data.sessionID, type: PartType.TEXT, text: data.delta || '' } },
                };
            case 'session.reasoning.delta':
                return {
                    type: OcEventType.MESSAGE_PART_UPDATED,
                    properties: { sessionID: data.sessionID, part: { sessionID: data.sessionID, type: PartType.REASONING, text: data.delta || '' } },
                };
            case 'session.idle':
            case 'session.execution.succeeded':
            case 'session.execution.interrupted':
                return { type: OcEventType.SESSION_IDLE, properties: { sessionID: data.sessionID } };
            case 'session.retry.scheduled':
                return {
                    type: OcEventType.SESSION_STATUS,
                    properties: {
                        sessionID: data.sessionID,
                        status: { type: 'retry', attempt: data.attempt, message: this.#errorMessage(data.error), next: data.at },
                    },
                };
            case 'session.execution.failed':
                return { type: OcEventType.SESSION_ERROR, properties: { sessionID: data.sessionID, error: data.error } };
            case 'permission.asked':
                return {
                    type: OcEventType.PERMISSION_ASKED,
                    properties: { id: data.id, sessionID: data.sessionID, permission: data.action, patterns: data.resources || [] },
                };
            case 'form.created': {
                const form = data.form;
                if (!form?.id || !form?.sessionID) return null;
                const questions = (form.fields || [])
                    .filter((field) => !field.hidden)
                    .map((field) => ({
                        question: field.title || field.description || field.key,
                        header: field.title || '输入',
                        multiple: field.type === 'multiselect',
                        options: (field.options || []).map((option) => ({ label: option.label, value: option.value })),
                    }));
                return { type: OcEventType.QUESTION_ASKED, properties: { id: form.id, sessionID: form.sessionID, questions } };
            }
            case 'form.replied':
                return { type: OcEventType.QUESTION_REPLIED, properties: { requestID: data.id, sessionID: data.sessionID, answers: data.answer } };
            case 'form.cancelled':
                return { type: OcEventType.QUESTION_REJECTED, properties: { requestID: data.id, sessionID: data.sessionID } };
            default:
                return null;
        }
    }

    /**
     * 提取 v2 StructuredError 的可读信息
     */
    #errorMessage(err) {
        if (!err) return '未知';
        if (typeof err === 'string') return err;
        return err?.data?.message || err?.message || JSON.stringify(err).slice(0, 200);
    }

    /**
     * 事件分发
     */
    async #dispatch(event) {
        if (!event?.type || event.type === OcEventType.SERVER_HEARTBEAT) return;
        const internalSessionId = event.properties?.part?.sessionID || event.properties?.sessionID;
        const chatId = this.#sessionManager.getChatIdBySessionId(internalSessionId);

        // API 通道会话的事件路由到 Agent API 处理（question -> 任务等待输入，permission -> 自动拒绝）
        if (!chatId && this.#apiRouter?.hasSession?.(internalSessionId)) {
            await this.#dispatchApiEvent(event, internalSessionId);
            return;
        }

        switch (event.type) {
            case OcEventType.MESSAGE_PART_UPDATED:
                if (chatId) await this.#handlePartUpdated(chatId, event);
                break;
            case OcEventType.SESSION_IDLE:
                console.log(`${LogPrefix.EVENTS} session.idle: session=${event.properties?.sessionID} chat=${chatId || '未映射'}`);
                if (chatId) await this.#handleSessionIdle(chatId);
                break;
            case OcEventType.QUESTION_ASKED:
                console.log(`${LogPrefix.EVENTS} question.asked: session=${event.properties?.sessionID}, request=${event.properties?.id}, 问题数=${event.properties?.questions?.length}`);
                await this.#handleQuestionAsked(event, chatId);
                break;
            case OcEventType.QUESTION_REPLIED:
                console.log(`${LogPrefix.EVENTS} question.replied: session=${event.properties?.sessionID}, request=${event.properties?.requestID}, answers=${JSON.stringify(event.properties?.answers)}`);
                break;
            case OcEventType.QUESTION_REJECTED:
                console.log(`${LogPrefix.EVENTS} question.rejected: session=${event.properties?.sessionID}, request=${event.properties?.requestID}`);
                break;
            case OcEventType.PERMISSION_ASKED:
                await this.#handlePermissionAsked(event, chatId);
                break;
            case OcEventType.SESSION_STATUS:
                if (chatId) await this.#handleSessionStatus(event, chatId);
                break;
            case OcEventType.SESSION_ERROR:
                await this.#handleSessionError(event, chatId);
                break;
            default:
                break;
        }
    }

    /**
     * API 通道事件处理（Agent API 会话专用，不进飞书交互链路）
     */
    async #dispatchApiEvent(event, internalSessionId) {
        switch (event.type) {
            case OcEventType.QUESTION_ASKED:
                console.log(`${LogPrefix.EVENTS} API question.asked: session=${internalSessionId}, request=${event.properties?.id}`);
                this.#apiRouter.onQuestionAsked(event.properties);
                break;
            case OcEventType.PERMISSION_ASKED:
                console.log(`${LogPrefix.EVENTS} API permission.asked: session=${internalSessionId}, permission=${event.properties?.permission}`);
                await this.#apiRouter.onPermissionAsked(event.properties);
                break;
            default:
                break;
        }
    }

    /**
     * 流式更新：reasoning 实时写入卡片，text 作为最终回复
     */
    async #handlePartUpdated(chatId, event) {
        const part = event.properties?.part;
        if (!part) return;

        const state = this.#streamStates.get(chatId);
        if (!state) {
            // 流开始：创建占位消息
            const res = await sendCardMessage(this.#chatService, chatId, '🤔 思考中', '');
            this.#streamStates.set(chatId, {
                messageId: res.data?.message_id,
                content: '',
                updatedAt: 0,
            });
            return;
        }

        if (part.type === PartType.REASONING && part.text) {
            // 节流追加思考内容并更新卡片
            const now = Date.now();
            if (now - state.updatedAt < STREAM_THROTTLE) return;
            state.updatedAt = now;
            state.content = `${state.content}${part.text}`;
            // 注意：占位消息是卡片（interactive），只能走 patch 更新，用 text 更新会报 230054
            await updateMessage(
                this.#chatService,
                state.messageId,
                'interactive',
                '',
                { title: '🤔 思考中', content: sanitizeText(state.content, '流式思考') },
            ).catch(() => {});
        }
    }

    /**
     * 会话空闲：流结束，撤回流式卡片并清理状态
     * （最终回复由 message-handler 写回 Thinking 卡片，避免残留重复卡片）
     */
    async #handleSessionIdle(chatId) {
        const state = this.#streamStates.get(chatId);
        if (state?.messageId) {
            await recallMessage(this.#chatService, state.messageId).catch(() => {});
        }
        this.#streamStates.delete(chatId);
    }

    /**
     * 工具提问 -> 转发用户并等待回复
     */
    async #handleQuestionAsked(event, chatId) {
        const target = chatId || BotConfig.defaultChatId;
        await new Promise((r) => setTimeout(r, EVENT_DISPATCH_DELAY));
        await this.#interaction.registerQuestion(target, event.properties);
    }

    /**
     * 权限请求 -> 转发用户并等待 /permit 回复
     */
    async #handlePermissionAsked(event, chatId) {
        const target = chatId || BotConfig.defaultChatId;
        await new Promise((r) => setTimeout(r, EVENT_DISPATCH_DELAY));
        await this.#interaction.registerPermission(target, event.properties);
    }

    /**
     * 会话重试状态：首次重试时通知
     */
    async #handleSessionStatus(event, chatId) {
        const status = event.properties?.status;
        if (status?.type !== 'retry' || status.attempt !== 1) return;

        const content = [
            `会话 ID: ${event.properties?.sessionID}`,
            `错误信息: ${status.message || '未知'}`,
            `下次重试: ${status.next ? new Date(status.next).toLocaleString() : '未知'}`,
        ].join('\n');
        await sendCardMessage(this.#chatService, chatId, '⚠️ 会话重试中', sanitizeText(content, '重试通知'));
    }

    /**
     * 会话错误：聊天卡片 + webhook 双通知
     * 兼容多种错误结构：properties.error.message / properties.error.data.message / properties.errorMessage
     */
    async #handleSessionError(event, chatId) {
        // 执行失败时先清理流式占位卡片，避免残留
        if (chatId) await this.#handleSessionIdle(chatId).catch(() => {});
        const sessionID = event.properties?.sessionID || '未知';
        const err = event.properties?.error;
        const message = err?.data?.message || err?.message
            || event.properties?.errorMessage
            || JSON.stringify(err).slice(0, 200)
            || '未知错误';
        const content = `会话 ${sessionID} 发生异常\n错误信息：${message}`;

        if (chatId) {
            await sendCardMessage(this.#chatService, chatId, '❌ 会话异常', sanitizeText(content, '会话异常'));
        }
        await sendWebhookMessage('❌ 会话异常', content);
    }
}

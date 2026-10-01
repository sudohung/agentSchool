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
import { sendCardMessage, updateMessage, recallMessage } from '../feishu/message-sender.js';
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

    constructor({ opencodeClient, getClient, sessionManager, chatService }) {
        // getClient：函数，返回最新 OpenCode 客户端（支持配置热更新后重连用新地址）
        this.#getClient = getClient || (() => opencodeClient);
        if (!opencodeClient && !getClient) {
            throw new Error('OpencodeListener 初始化失败：缺少 opencodeClient 或 getClient');
        }
        this.#sessionManager = sessionManager;
        this.#chatService = chatService;
        this.#interaction = new InteractionManager(sessionManager, chatService);
    }

    /** @type {Function} 返回最新 OpenCode SDK 客户端 */
    #getClient;

    /** 提供给消息处理器的交互路由（question/permission 回复闭环 + 卡片按钮回调） */
    getInteraction() {
        return {
            routeReply: (chatId, message) => this.#interaction.routeReply(chatId, message),
            respondPermission: (chatId, action) => this.#interaction.respondPermission(chatId, action),
            handleCardAction: (data) => this.#interaction.handleCardAction(data),
        };
    }

    /**
     * 启动事件订阅主循环
     * 服务端不可用或流断开时自动重连（指数退避，封顶 60s）
     */
    async start() {
        let delay = RECONNECT_BASE_DELAY;
        for (;;) {
            try {
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
            } catch (error) {
                console.error(`${LogPrefix.EVENTS} 事件订阅失败: ${error.message}`);
            }
            await new Promise((r) => setTimeout(r, delay));
            delay = Math.min(delay * 2, RECONNECT_MAX_DELAY);
        }
    }

    /**
     * 事件分发
     */
    async #dispatch(event) {
        if (!event?.type || event.type === OcEventType.SERVER_HEARTBEAT) return;
        const chatId = this.#sessionManager.getChatIdBySessionId(
            event.properties?.part?.sessionID || event.properties?.sessionID,
        );

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
                { title: '🤔 思考中', content: state.content },
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
        await sendCardMessage(this.#chatService, chatId, '⚠️ 会话重试中', content);
    }

    /**
     * 会话错误：聊天卡片 + webhook 双通知
     * 兼容多种错误结构：properties.error.message / properties.error.data.message / properties.errorMessage
     */
    async #handleSessionError(event, chatId) {
        const sessionID = event.properties?.sessionID || '未知';
        const err = event.properties?.error;
        const message = err?.data?.message || err?.message
            || event.properties?.errorMessage
            || JSON.stringify(err).slice(0, 200)
            || '未知错误';
        const content = `会话 ${sessionID} 发生异常\n错误信息：${message}`;

        if (chatId) {
            await sendCardMessage(this.#chatService, chatId, '❌ 会话异常', content);
        }
        await sendWebhookMessage('❌ 会话异常', content);
    }
}

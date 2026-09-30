/**
 * 飞书消息主处理器
 * 编排流程：去重 -> 过滤链 -> "思考中"卡片 -> 交互回复路由 -> 命令路由 -> AI 处理
 */

import { LogPrefix, CommandAction } from '../constants.js';
import {
    sendThinkingMessage,
    sendErrorMessage,
    updateMessage,
    sendTextMessage,
} from '../feishu/message-sender.js';
import { runFilterChain, preprocessMessage } from './filters.js';
import { CommandRouter, extractTextResponse } from './commands.js';

/**
 * 消息处理器类
 */
export class MessageHandler {
    /**
     * @param {Object} deps
     * @param {import('../agent/session-manager.js').SessionManager} deps.sessionManager
     * @param {import('../agent/agent-registry.js').AgentRegistry} deps.registry
     * @param {import('../feishu/chat-service.js').ChatService} deps.chatService
     * @param {Object} deps.interaction - 交互上下文（由事件层注册，处理 question/permission 回复）
     */
    #deps;
    #commandRouter;

    constructor(deps) {
        this.#deps = deps;
        this.#commandRouter = new CommandRouter(deps.sessionManager, deps.registry);
    }

    #log(msg) {
        console.log(`${LogPrefix.HANDLER} ${msg}`);
    }

    /**
     * 处理一条飞书消息（网关回调入口）
     * @param {string} chatId
     * @param {string} userMessage
     * @param {Object} messageContext
     */
    async handle(chatId, userMessage, messageContext) {
        const { sessionManager, chatService, interaction } = this.#deps;

        // 步骤1：并发去重
        if (sessionManager.isProcessing(chatId, userMessage)) {
            this.#log(`消息处理中，跳过: ${chatId}`);
            return;
        }

        try {
            // 步骤2：过滤链（群@、黑名单）
            const filterResult = runFilterChain(chatId, messageContext);
            if (!filterResult.pass) {
                this.#log(`消息被过滤: ${filterResult.type} - ${filterResult.reason}`);
                return;
            }

            const message = preprocessMessage(userMessage);
            sessionManager.markProcessing(chatId, userMessage);
            this.#log(`开始处理: ${message}`);

            // 步骤3：交互优先级路由 —— 存在待回答提问/权限时，回复直接作为答案
            if (interaction && interaction.routeReply) {
                const handled = await interaction.routeReply(chatId, message);
                if (handled) return;
            }

            // 步骤4：命令路由
            const commandResult = await this.#commandRouter.route(chatId, message);
            if (commandResult) {
                // 权限命令需要 interaction 协作完成
                if (commandResult.action === CommandAction.PERMIT) {
                    const done = await interaction.respondPermission?.(chatId, commandResult.permitAction);
                    commandResult.message = done
                        ? `已响应权限请求: ${commandResult.permitAction}`
                        : '未找到待处理的权限请求';
                }
                const thinking = await sendThinkingMessage(chatService, chatId);
                await updateMessage(
                    chatService,
                    thinking.data.message_id,
                    'interactive',
                    userMessage,
                    { title: '执行结果', content: commandResult.message },
                );
                return;
            }

            // 步骤5：普通消息 -> AI Agent 处理
            await this.#handleAiMessage(chatId, message, userMessage);
        } catch (error) {
            console.error(`${LogPrefix.HANDLER} 处理失败: ${error.message}`, error.stack);
            await sendErrorMessage(chatService, chatId, `回复: ${userMessage} -> ${error.message}`).catch(() => {});
        } finally {
            sessionManager.markCompleted(chatId, userMessage);
        }
    }

    /**
     * AI 消息处理：发送 prompt 并将最终回复写回"思考中"卡片
     */
    async #handleAiMessage(chatId, message, userMessage) {
        const { sessionManager, chatService } = this.#deps;
        const thinking = await sendThinkingMessage(chatService, chatId);
        const thinkingId = thinking?.data?.message_id;

        const result = await sessionManager.sendMessage(chatId, message);
        const aiResponse = extractTextResponse(result) || '（无文本回复）';

        if (thinkingId) {
            await updateMessage(chatService, thinkingId, 'interactive', userMessage, {
                title: '回复',
                content: aiResponse,
            });
        } else {
            await sendTextMessage(chatService, chatId, aiResponse);
        }
    }
}

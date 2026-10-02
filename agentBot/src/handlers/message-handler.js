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
import { sanitizeText } from '../security/sanitizer.js';
import { runFilterChain, preprocessMessage } from './filters.js';
import { CommandRouter, extractTextResponse } from './commands.js';

/** 引用链向上追溯的最大层数（防止嵌套引用导致上下文爆炸） */
const MAX_QUOTE_DEPTH = 3;
/** 单条引用内容的最大字符数 */
const MAX_QUOTE_LENGTH = 2000;

/** 截断单条引用内容 */
function truncateLine(text, max) {
    return text.length > max ? `${text.slice(0, max)}\n...（引用内容过长已截断）` : text;
}

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
                    { title: '执行结果', content: sanitizeText(commandResult.message, '命令结果') },
                );
                return;
            }

            // 步骤5：解析 @ 名单（显式 @ 透传，排除机器人自身）
            const atList = await this.#extractAtList(messageContext);

            // 步骤6：普通消息 -> AI Agent 处理（引用回复时携带引用上下文，回复时按需 @）
            await this.#handleAiMessage(chatId, message, userMessage, messageContext, atList);
        } catch (error) {
            // undici 的 fetch failed 会把真实原因藏在 cause（HeadersTimeoutError/连接错误等）
            const cause = error?.cause?.message || error?.cause?.code || error?.cause;
            console.error(`${LogPrefix.HANDLER} 处理失败: ${error.message}${cause ? ` | cause: ${cause}` : ''}`, error.stack);
            // 错误详情只进服务端日志，飞书侧仅回简要提示，避免路径/堆栈泄漏
            await sendErrorMessage(chatService, chatId, '处理失败，请稍后重试或联系管理员查看服务日志').catch(() => {});
        } finally {
            sessionManager.markCompleted(chatId, userMessage);
        }
    }

    /**
     * AI 消息处理：发送 prompt 并将最终回复写回"思考中"卡片
     * 引用回复场景：将引用的消息内容作为上下文一并交给 opencode
     * @ 回复场景：atList 非空时，回复内容开头 @ 对应成员
     */
    async #handleAiMessage(chatId, message, userMessage, messageContext = {}, atList = []) {
        const { sessionManager, chatService } = this.#deps;
        const thinking = await sendThinkingMessage(chatService, chatId);
        const thinkingId = thinking?.data?.message_id;

        // 构建引用上下文（失败不阻塞主流程，仅用原文发送）
        let prompt = await this.#buildPromptWithQuotes(message, messageContext?.parent_id);
        // 用户显式 @ 了其他人时，告知 opencode 该意图（便于其理解任务上下文）
        if (atList.length > 0) {
            prompt = `${prompt}\n\n[提示] 用户在消息中@了: ${atList.map((a) => a.name || a.openId).join('、')}`;
        }

        const result = await sessionManager.sendMessage(chatId, prompt);
        const aiResponse = extractTextResponse(result) || '（无文本回复）';

        const atPrefix = this.#renderAtPrefix(atList, 'card');
        if (thinkingId) {
            await updateMessage(chatService, thinkingId, 'interactive', userMessage, {
                title: '回复',
                content: atPrefix + sanitizeText(aiResponse, 'AI回复'),
            });
        } else {
            await sendTextMessage(chatService, chatId, this.#renderAtPrefix(atList, 'text') + sanitizeText(aiResponse, 'AI回复'));
        }
    }

    /**
     * 从消息事件的 mentions 中提取 @ 名单（排除机器人自身）
     * @param {Object} messageContext - 消息事件上下文
     * @returns {Promise<Array<{openId:string, name:string}>>}
     */
    async #extractAtList(messageContext) {
        const mentions = messageContext?.mentions || [];
        if (mentions.length === 0) return [];

        const { chatService } = this.#deps;
        const botOpenId = await chatService.getBotOpenId();

        const list = [];
        for (const mention of mentions) {
            const openId = mention?.id?.open_id;
            // 格式校验：非法 id 直接跳过，避免渲染进卡片导致 230099
            if (!openId || !/^ou_[A-Za-z0-9]+$/.test(openId)) continue;
            // 排除用户 @ 机器人自身的场景（机器人无需 @ 自己）
            if (botOpenId && openId === botOpenId) continue;
            list.push({ openId, name: mention.name || '' });
        }
        if (list.length > 0) {
            this.#log(`回复将 @: ${list.map((a) => `${a.name}(${a.openId.slice(0, 10)}...)`).join('、')}`);
        }
        return list;
    }

    /**
     * 渲染 @ 前缀（文本消息与卡片消息的 at 语法不同，且引号规则不同）
     * 卡片 markdown：必须不带引号 <at id=ou_xxx></at>，带引号会被当作纯文本
     * 文本消息：标准语法 <at user_id="ou_xxx"></at>
     * @param {Array<{openId:string, name:string}>} atList
     * @param {'card'|'text'} style
     * @returns {string}
     */
    #renderAtPrefix(atList, style) {
        if (!atList?.length) return '';
        const tags = atList.map(({ openId }) => style === 'card'
            ? `<at id=${openId}></at>`
            : `<at user_id="${openId}"></at>`);
        return `${tags.join(' ')} `;
    }

    /**
     * 引用回复场景构建 prompt：引用链（向上最多 3 层）+ 当前问题
     * @param {string} message - 用户当前问题
     * @param {string} [parentId] - 被引用/回复的消息 ID
     * @returns {Promise<string>}
     */
    async #buildPromptWithQuotes(message, parentId) {
        if (!parentId) return message;

        // 向上递归取引用链，按时间从早到晚排列
        const quotes = [];
        let currentId = parentId;
        for (let depth = 0; currentId && depth < MAX_QUOTE_DEPTH; depth++) {
            const msg = await this.#deps.chatService.getMessageById(currentId);
            console.log(`${LogPrefix.HANDLER} 引用反查: id=${currentId}, 结果=${msg ? `type=${msg.msgType}, textLen=${msg.text.length}` : 'null'}`);
            if (!msg) break;
            quotes.unshift(msg.text);
            currentId = msg.parentId;
        }

        const validQuotes = quotes.filter(Boolean);
        if (validQuotes.length === 0) {
            console.warn(`${LogPrefix.HANDLER} 引用内容提取为空，降级为纯文本消息发送`);
            return message;
        }

        // 引用内容超长保护
        const quoteBlock = validQuotes
            .map((text) => truncateLine(text, MAX_QUOTE_LENGTH))
            .join('\n---\n');

        return [
            '[引用消息开始]',
            quoteBlock,
            '[引用消息结束]',
            '',
            '[当前问题]',
            message,
        ].join('\n');
    }
}

/**
 * 命令处理器（策略注册表模式）
 * 命令格式统一为 /<cmd>[:<arg>]，未匹配的 / 命令返回帮助
 */

import { CommandAction, PermissionAction } from '../constants.js';

/**
 * 命令处理器类
 * @param {import('../agent/session-manager.js').SessionManager} sessionManager
 * @param {import('../agent/agent-registry.js').AgentRegistry} registry
 */
export class CommandRouter {
    #sessionManager;
    #registry;

    constructor(sessionManager, registry) {
        this.#sessionManager = sessionManager;
        this.#registry = registry;
    }

    // ==================== 各命令实现 ====================

    /** /help */
    #cmdHelp() {
        return {
            action: CommandAction.HELP,
            message: [
                '可用命令：',
                '/new - 重置会话',
                '/agents - 列出可用 Agent',
                '/model:<key> - 切换 Agent 模型',
                '/sessions - 列出会话',
                '/session:<id> - 切换会话',
                '/abort - 中断当前会话',
                '/permit:<once|always|reject> - 响应权限请求',
                '/reply:<内容> - 发送应答消息',
                '/help - 显示帮助',
            ].join('\n'),
        };
    }

    /** /new 重置会话 */
    async #cmdNew(chatId) {
        const sessionId = await this.#sessionManager.resetSession(chatId);
        return { action: CommandAction.NEW_SESSION, message: `已创建新会话: ${sessionId}` };
    }

    /** /agents 列出 Agent */
    #cmdListAgents(chatId) {
        const current = this.#sessionManager.resolveAgent(chatId).key;
        const lines = this.#registry.listAgents()
            .map(({ key, name }) => `${key === current ? '→' : '•'} ${key} (${name})`)
            .join('\n');
        return { action: CommandAction.LIST_AGENTS, message: `可用 Agent（当前 →）：\n${lines}` };
    }

    /** /model:<key> 切换 Agent */
    #cmdSwitchAgent(chatId, agentKey) {
        const ok = this.#sessionManager.switchAgent(chatId, agentKey);
        if (!ok) {
            return {
                action: CommandAction.SWITCH_AGENT,
                message: `切换失败，未找到 Agent: ${agentKey}（/agents 查看列表）`,
            };
        }
        const { agent } = this.#sessionManager.resolveAgent(chatId);
        return { action: CommandAction.SWITCH_AGENT, message: `已切换 Agent: ${agent.getName()}` };
    }

    /** /sessions 列出会话 */
    async #cmdListSessions() {
        try {
            const sessions = await this.#sessionManager.listSessions();
            if (!sessions?.length) {
                return { action: CommandAction.LIST_SESSIONS, message: '当前 Agent 没有会话' };
            }
            const list = sessions.slice(0, 10).map((s) => {
                const id = s.id || s.sessionId || 'unknown';
                const title = s.title || '无标题';
                return `• ${title} (${id})`;
            }).join('\n');
            const more = sessions.length > 10 ? `\n... 还有 ${sessions.length - 10} 个` : '';
            return {
                action: CommandAction.LIST_SESSIONS,
                message: `会话列表 (${sessions.length}):\n${list}${more}`,
            };
        } catch (error) {
            return { action: CommandAction.LIST_SESSIONS, message: `列出会话失败: ${error.message}` };
        }
    }

    /** /session:<id> 切换会话 */
    async #cmdSwitchSession(chatId, sessionId) {
        try {
            this.#sessionManager.switchSession(chatId, sessionId);
            const messages = await this.#sessionManager.getSessionMessages(sessionId);
            if (!messages?.length) {
                return { action: CommandAction.SWITCH_SESSION, message: `已切换到会话: ${sessionId}\n(暂无消息)` };
            }
            const recent = messages.slice(-10).map((m, i) => {
                const role = m.info?.role || m.role || 'unknown';
                const text = (m.parts || [])
                    .filter((p) => p.type === 'text')
                    .map((p) => p.text || '')
                    .join('');
                return `${i + 1}. [${role}]: ${text.length > 80 ? `${text.slice(0, 80)}...` : text}`;
            }).join('\n');
            return {
                action: CommandAction.SWITCH_SESSION,
                message: `已切换到会话: ${sessionId}\n最新消息:\n${recent}`,
            };
        } catch (error) {
            return { action: CommandAction.SWITCH_SESSION, message: `切换会话失败: ${error.message}` };
        }
    }

    /** /abort 中断会话 */
    async #cmdAbort(chatId) {
        try {
            const sessionId = await this.#sessionManager.abortSession(chatId);
            return { action: CommandAction.ABORT, message: `已中断会话: ${sessionId}` };
        } catch (error) {
            return { action: CommandAction.ABORT, message: `中断会话失败: ${error.message}` };
        }
    }

    /** /reply:<内容> 直接将内容作为 prompt 发送到当前会话 */
    async #cmdReply(chatId, content) {
        try {
            const result = await this.#sessionManager.sendMessage(chatId, content);
            return {
                action: CommandAction.REPLY,
                message: `应答消息已发送\n${extractTextResponse(result)}`,
            };
        } catch (error) {
            return { action: CommandAction.REPLY, message: `应答失败: ${error.message}` };
        }
    }

    // ==================== 路由 ====================

    /**
     * 解析并执行命令
     * @param {string} chatId
     * @param {string} message - 预处理后的用户消息
     * @returns {Promise<Object|null>} 命令结果；null 表示非命令（走 AI 处理）
     */
    async route(chatId, message) {
        const trimmed = message.trim();
        if (!trimmed.startsWith('/')) return null;

        const [cmdRaw, ...argParts] = trimmed.slice(1).split(':');
        const cmd = cmdRaw.toLowerCase();
        const arg = argParts.join(':').trim();

        switch (cmd) {
            case 'help':
                return this.#cmdHelp();
            case 'new':
                return this.#cmdNew(chatId);
            case 'agents':
                return this.#cmdListAgents(chatId);
            case 'model':
            case 'instant':
                return arg
                    ? this.#cmdSwitchAgent(chatId, arg)
                    : { action: CommandAction.SWITCH_AGENT, message: '用法: /model:<key>，/agents 查看列表' };
            case 'sessions':
                return await this.#cmdListSessions();
            case 'session':
                return arg
                    ? await this.#cmdSwitchSession(chatId, arg)
                    : { action: CommandAction.SWITCH_SESSION, message: '用法: /session:<id>，/sessions 查看列表' };
            case 'abort':
                return await this.#cmdAbort(chatId);
            case 'reply':
                return arg
                    ? await this.#cmdReply(chatId, arg)
                    : { action: CommandAction.REPLY, message: '用法: /reply:<内容>' };
            case 'permit': {
                // 权限响应依赖 pending 权限请求，由 message-handler 注入处理
                return { action: CommandAction.PERMIT, permitAction: arg || PermissionAction.ALWAYS };
            }
            default:
                return {
                    action: CommandAction.INVALID,
                    message: `无效命令: /${cmd}，/help 查看可用命令`,
                };
        }
    }
}

/**
 * 从 OpenCode 响应中提取文本
 * @param {Object} result
 * @returns {string}
 */
export function extractTextResponse(result) {
    if (!result) return '';
    const data = result.data || result;
    if (Array.isArray(data?.parts)) {
        return data.parts
            .filter((p) => p.type === 'text')
            .map((p) => p.text || '')
            .join('\n');
    }
    if (data?.info?.content) return data.info.content;
    return '';
}

/**
 * 全局枚举常量定义
 * 统一管理魔法值，避免散落在各模块中
 */

/** 飞书消息类型 */
export const MsgType = {
    TEXT: 'text',
    INTERACTIVE: 'interactive',
};

/** 命令动作标识 */
export const CommandAction = {
    HELP: 'help',
    NEW_SESSION: 'new_session',
    SWITCH_AGENT: 'switch_agent',
    LIST_AGENTS: 'list_agents',
    LIST_SESSIONS: 'list_sessions',
    SWITCH_SESSION: 'switch_session',
    ABORT: 'abort_session',
    PERMIT: 'permit_permission',
    REPLY: 'reply_message',
    INVALID: 'invalid_command',
};

/** 权限响应动作 */
export const PermissionAction = {
    ONCE: 'once',
    ALWAYS: 'always',
    REJECT: 'reject',
};

/** OpenCode 事件类型 */
export const OcEventType = {
    MESSAGE_PART_UPDATED: 'message.part.updated',
    SESSION_IDLE: 'session.idle',
    SESSION_ERROR: 'session.error',
    SESSION_STATUS: 'session.status',
    QUESTION_ASKED: 'question.asked',
    PERMISSION_ASKED: 'permission.asked',
    SERVER_HEARTBEAT: 'server.heartbeat',
};

/** OpenCode part 类型 */
export const PartType = {
    TEXT: 'text',
    REASONING: 'reasoning',
    STEP_START: 'step-start',
    STEP_FINISH: 'step-finish',
};

/** 交互上下文类型（用户回复路由） */
export const PendingInteraction = {
    QUESTION: 'question',
    PERMISSION: 'permission',
};

/** 消息前缀 */
export const LogPrefix = {
    GATEWAY: '[Gateway]',
    SENDER: '[Sender]',
    AGENT_MGR: '[SessionManager]',
    HANDLER: '[MessageHandler]',
    EVENTS: '[OcEvents]',
    WEBHOOK: '[Webhook]',
    ADMIN: '[Admin]',
};

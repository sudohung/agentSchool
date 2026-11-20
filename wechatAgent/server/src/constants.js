/**
 * 全局常量与枚举
 * 约定：所有枚举值集中在此，禁止业务代码里散落字符串字面量
 */

/** OpenCode 协议版本 */
export const EngineVersion = Object.freeze({
    V1: 'v1',
    V2: 'v2',
    AUTO: 'auto',
});

/** 下发给小程序的流式帧类型（NDJSON，一行一帧） */
export const FrameType = Object.freeze({
    START: 'start',
    DELTA: 'delta',
    REASONING: 'reasoning',
    TOOL: 'tool',
    QUESTION: 'question',
    PERMISSION: 'permission',
    DONE: 'done',
    ERROR: 'error',
    PING: 'ping',
});

/** 聊天消息角色 */
export const MessageRole = Object.freeze({
    USER: 'user',
    ASSISTANT: 'assistant',
});

/** 消息状态 */
export const MessageStatus = Object.freeze({
    STREAMING: 'streaming',
    DONE: 'done',
    ERROR: 'error',
    ABORTED: 'aborted',
});

/** 登录模式 */
export const AuthMode = Object.freeze({
    WECHAT: 'wechat',
    DEV: 'dev',
});

/** 统一错误码（前端按 code 做提示） */
export const ErrorCode = Object.freeze({
    BAD_REQUEST: 'BAD_REQUEST',
    UNAUTHORIZED: 'UNAUTHORIZED',
    FORBIDDEN: 'FORBIDDEN',
    NOT_FOUND: 'NOT_FOUND',
    CONFLICT: 'CONFLICT',
    ENGINE_ERROR: 'ENGINE_ERROR',
    TIMEOUT: 'TIMEOUT',
    INTERNAL: 'INTERNAL',
});

/** 一轮对话的终态 */
export const TurnStatus = Object.freeze({
    DONE: 'done',
    ABORTED: 'aborted',
    ERROR: 'error',
    TIMEOUT: 'timeout',
});

/** 日志前缀 */
export const LogPrefix = Object.freeze({
    BOOT: '[Boot]',
    HTTP: '[Http]',
    AUTH: '[Auth]',
    ENGINE: '[Engine]',
    BUS: '[Bus]',
    CHAT: '[Chat]',
    STORE: '[Store]',
});
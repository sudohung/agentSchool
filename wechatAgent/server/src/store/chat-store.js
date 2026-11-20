/**
 * 用户与会话/消息持久化
 * 结构：{ users, sessions, messages }
 *   users:    openid -> { id, openid, nickname, avatar, mode, createdAt, lastSeenAt }
 *   sessions: 业务会话 id -> { id, userId, title, engine, model, opencodeSessionId, createdAt, updatedAt }
 *   messages: 业务会话 id -> [{ id, role, content, reasoning, status, createdAt }]
 */

import { randomUUID } from 'crypto';
import { JsonStore, dataFile } from './json-store.js';
import { MessageRole, MessageStatus } from '../constants.js';

const EMPTY = { users: {}, sessions: {}, messages: {} };

export class ChatStore {
    /** @type {JsonStore} */
    #store;

    /** @param {string} dataDir */
    constructor(dataDir) {
        this.#store = new JsonStore(dataFile(dataDir, 'chat-store.json'), EMPTY);
        this.#store.get().users ||= {};
        this.#store.get().sessions ||= {};
        this.#store.get().messages ||= {};
    }

    // ==================== 用户 ====================

    /**
     * 按 openid 查找或创建用户
     * @param {string} openid
     * @param {{mode:string, nickname?:string, avatar?:string}} profile
     */
    upsertUser(openid, profile) {
        const data = this.#store.get();
        const now = Date.now();
        let user = data.users[openid];
        if (!user) {
            user = {
                id: `usr_${randomUUID()}`,
                openid,
                nickname: profile.nickname || '微信用户',
                avatar: profile.avatar || '',
                mode: profile.mode,
                createdAt: now,
                lastSeenAt: now,
            };
            data.users[openid] = user;
        } else {
            user.lastSeenAt = now;
            if (profile.nickname) user.nickname = profile.nickname;
            if (profile.avatar) user.avatar = profile.avatar;
            user.mode = profile.mode;
        }
        this.#store.save();
        return user;
    }

    /**
     * 按用户 id 取用户
     * @param {string} userId
     */
    getUser(userId) {
        return Object.values(this.#store.get().users).find((item) => item.id === userId) || null;
    }

    // ==================== 会话 ====================

    /**
     * 列出某用户的会话（按更新时间倒序）
     * @param {string} userId
     */
    listSessions(userId) {
        return Object.values(this.#store.get().sessions)
            .filter((item) => item.userId === userId)
            .sort((a, b) => b.updatedAt - a.updatedAt);
    }

    /**
     * 取会话
     * @param {string} sessionId
     */
    getSession(sessionId) {
        return this.#store.get().sessions[sessionId] || null;
    }

    /**
     * 创建会话
     * @param {{userId:string, title:string, engine:string, model:string}} input
     */
    createSession(input) {
        const now = Date.now();
        const session = {
            id: `sc_${randomUUID()}`,
            userId: input.userId,
            title: input.title || '新的对话',
            engine: input.engine,
            model: input.model,
            opencodeSessionId: '',
            createdAt: now,
            updatedAt: now,
        };
        this.#store.get().sessions[session.id] = session;
        this.#store.get().messages[session.id] = [];
        this.#store.save();
        return session;
    }

    /**
     * 更新会话字段
     * @param {string} sessionId
     * @param {Object} patch
     */
    updateSession(sessionId, patch) {
        const data = this.#store.get();
        const session = data.sessions[sessionId];
        if (!session) return null;
        Object.assign(session, patch, { updatedAt: Date.now() });
        this.#store.save();
        return session;
    }

    /**
     * 删除会话及其消息
     * @param {string} sessionId
     */
    deleteSession(sessionId) {
        const data = this.#store.get();
        if (!data.sessions[sessionId]) return false;
        delete data.sessions[sessionId];
        delete data.messages[sessionId];
        this.#store.save();
        return true;
    }

    // ==================== 消息 ====================

    /**
     * 会话消息列表
     * @param {string} sessionId
     */
    listMessages(sessionId) {
        return this.#store.get().messages[sessionId] || [];
    }

    /**
     * 追加消息
     * @param {string} sessionId
     * @param {{role:string, content:string, reasoning?:string, status?:string, id?:string}} input
     */
    appendMessage(sessionId, input) {
        const data = this.#store.get();
        data.messages[sessionId] ||= [];
        const message = {
            id: input.id || `msg_${randomUUID()}`,
            role: input.role,
            content: input.content || '',
            reasoning: input.reasoning || '',
            status: input.status || MessageStatus.DONE,
            createdAt: Date.now(),
        };
        data.messages[sessionId].push(message);
        if (data.sessions[sessionId]) data.sessions[sessionId].updatedAt = message.createdAt;
        this.#store.save();
        return message;
    }

    /**
     * 增量更新消息（流式过程中高频调用，内存更新 + 延迟落盘）
     * @param {string} sessionId
     * @param {string} messageId
     * @param {{content?:string, reasoning?:string, status?:string}} patch
     * @param {boolean} [persist]
     */
    patchMessage(sessionId, messageId, patch, persist = false) {
        const list = this.#store.get().messages[sessionId];
        const message = list?.find((item) => item.id === messageId);
        if (!message) return null;
        Object.assign(message, patch);
        if (persist) this.#store.save();
        return message;
    }

    // ==================== 维护 ====================

    /** 立即落盘（进程退出前调用） */
    flush() {
        if (this.#store.dirty) this.#store.save();
    }
}

/**
 * 判断消息是否为用户消息
 * @param {string} role
 */
export function isUserMessage(role) {
    return role === MessageRole.USER;
}
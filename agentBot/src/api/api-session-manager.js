/**
 * API 会话管理器
 * 职责：
 *  1. 会话凭证（callerSessionId = 职能key_uuid）生成与绑定映射管理
 *  2. 凭证 -> { 职能, 实例, 内部会话 } 的解析（对外仅暴露凭证）
 *  3. 绑定持久化（重启后凭证仍有效）与空闲超时清理
 *  4. 同一内部会话的请求串行排队（复用飞书通道的串行锁模式）
 */

import { randomUUID } from 'crypto';
import { readFileSync, writeFileSync, renameSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { LogPrefix } from '../constants.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

/** 绑定映射持久化路径 */
const SESSION_STORE_PATH = join(__dirname, '../../config/api-sessions.json');

/**
 * API 会话管理器类
 */
export class ApiSessionManager {
    /** @type {import('../agent/role-registry.js').RoleRegistry} */
    #roleRegistry;
    /** @type {import('../agent/instance-pool.js').InstancePool} */
    #instancePool;
    /** @type {Map<string, Object>} callerSessionId -> 绑定 */
    #bindings = new Map();
    /** @type {Map<string, Promise>} 内部会话ID -> 串行任务链 */
    #sessionLocks = new Map();
    /** @type {NodeJS.Timeout|null} 空闲清理定时器 */
    #sweeper = null;

    /**
     * @param {import('../agent/role-registry.js').RoleRegistry} roleRegistry
     * @param {import('../agent/instance-pool.js').InstancePool} instancePool
     */
    constructor(roleRegistry, instancePool) {
        if (!roleRegistry || !instancePool) {
            throw new Error('ApiSessionManager 初始化失败：缺少 RoleRegistry/InstancePool');
        }
        this.#roleRegistry = roleRegistry;
        this.#instancePool = instancePool;
        this.#loadPersisted();
    }

    /**
     * 启动空闲清理（定时扫描，超时绑定直接移除）
     */
    startSweeper() {
        if (this.#sweeper) return;
        // 每 10 分钟扫描一次过期会话
        this.#sweeper = setInterval(() => this.#sweepIdle(), 10 * 60 * 1000);
        this.#sweeper.unref?.();
    }

    /**
     * 按职能申请会话：生成凭证并创建内部 OpenCode 会话
     * @param {string} roleKey
     * @returns {Promise<{callerSessionId:string, role:string, name:string}>}
     */
    async applySession(roleKey) {
        const role = this.#roleRegistry.getRole(roleKey);
        if (!role) {
            throw new Error(`职能不存在: ${roleKey}，请先调用 list_roles 获取可用职能`);
        }

        // 创建内部 OpenCode 会话
        const agent = this.#instancePool.getAgentForRole(role);
        const sessionId = await agent.createSession(`api-${role.key}-${Date.now()}`);

        // 生成对外凭证（职能 key 前缀便于调用方辨认用途）
        const callerSessionId = `${role.key}_${randomUUID()}`;
        this.#bindings.set(callerSessionId, {
            roleKey: role.key,
            sessionId,
            createdAt: Date.now(),
            lastActiveAt: Date.now(),
            // 待答提问（question.asked 事件写入，下一次 chat 自动作为答案回传）
            pendingQuestion: null,
        });
        this.#persist();
        console.log(`${LogPrefix.API_SESSION} 申请会话: credential=${callerSessionId}, 内部会话=${sessionId}`);
        return { callerSessionId, role: role.key, name: role.name };
    }

    /**
     * 获取绑定（命中则刷新活跃时间）
     * @param {string} callerSessionId
     * @returns {Object|null}
     */
    getBinding(callerSessionId) {
        const binding = this.#bindings.get(callerSessionId);
        if (binding) binding.lastActiveAt = Date.now();
        return binding || null;
    }

    /**
     * 校验凭证有效性，无效时抛出带指引的错误
     * @param {string} callerSessionId
     * @returns {Object} 绑定
     */
    requireBinding(callerSessionId) {
        const binding = this.getBinding(callerSessionId);
        if (!binding) {
            throw new Error(`会话凭证无效或已过期: ${callerSessionId}，请重新调用 apply_session 申请`);
        }
        return binding;
    }

    /**
     * 获取凭证对应的职能 Agent 实例
     */
    getAgent(callerSessionId) {
        const binding = this.requireBinding(callerSessionId);
        const role = this.#roleRegistry.getRole(binding.roleKey);
        return { binding, role, agent: this.#instancePool.getAgentForRole(role) };
    }

    /**
     * 按绑定获取职能 Agent 实例（事件路由用，凭证不可见场景）
     */
    getAgentByBinding(binding) {
        const role = this.#roleRegistry.getRole(binding.roleKey);
        return { binding, role, agent: this.#instancePool.getAgentForRole(role) };
    }

    /**
     * 内部会话 ID 反查绑定（事件路由用）
     * @param {string} internalSessionId
     * @returns {Object|null}
     */
    findByInternalSessionId(internalSessionId) {
        if (!internalSessionId) return null;
        for (const binding of this.#bindings.values()) {
            if (binding.sessionId === internalSessionId) return binding;
        }
        return null;
    }

    /** 判断内部会话 ID 是否属于 API 通道 */
    hasInternalSession(internalSessionId) {
        return !!this.findByInternalSessionId(internalSessionId);
    }

    /**
     * 主动释放会话
     * @returns {boolean} 是否存在并已删除
     */
    closeSession(callerSessionId) {
        const deleted = this.#bindings.delete(callerSessionId);
        if (deleted) this.#persist();
        return deleted;
    }

    // ==================== 串行排队 ====================

    /**
     * 在指定内部会话上串行执行任务
     * @param {string} sessionId - 内部会话 ID
     * @param {() => Promise<T>} fn
     * @returns {Promise<T>}
     */
    async withSessionLock(sessionId, fn) {
        const previous = this.#sessionLocks.get(sessionId) || Promise.resolve();
        const task = previous.then(fn);
        // 吞掉失败防止链条断裂（错误由调用方处理）
        const guarded = task.catch(() => {});
        this.#sessionLocks.set(sessionId, guarded);
        try {
            return await task;
        } finally {
            if (this.#sessionLocks.get(sessionId) === guarded) {
                this.#sessionLocks.delete(sessionId);
            }
        }
    }

    // ==================== 持久化与清理 ====================

    /**
     * 持久化绑定映射（原子写入；不持久化运行态字段）
     */
    #persist() {
        try {
            const data = {};
            for (const [credential, binding] of this.#bindings.entries()) {
                data[credential] = {
                    roleKey: binding.roleKey,
                    sessionId: binding.sessionId,
                    createdAt: binding.createdAt,
                    lastActiveAt: binding.lastActiveAt,
                };
            }
            const tmp = `${SESSION_STORE_PATH}.tmp`;
            writeFileSync(tmp, JSON.stringify(data, null, 2));
            renameSync(tmp, SESSION_STORE_PATH);
        } catch (error) {
            console.error(`${LogPrefix.API_SESSION} 绑定持久化失败（不影响运行）: ${error.message}`);
        }
    }

    /**
     * 启动时恢复持久化的绑定
     * 职能已下线的绑定跳过；内部会话由 OpenCode 服务端持久，无需恢复动作
     */
    #loadPersisted() {
        try {
            if (!existsSync(SESSION_STORE_PATH)) return;
            const data = JSON.parse(readFileSync(SESSION_STORE_PATH, 'utf-8'));
            let restored = 0;
            for (const [credential, saved] of Object.entries(data || {})) {
                if (!this.#roleRegistry.hasRole(saved.roleKey)) {
                    console.warn(`${LogPrefix.API_SESSION} 跳过已下线职能的绑定: ${credential}`);
                    continue;
                }
                this.#bindings.set(credential, {
                    roleKey: saved.roleKey,
                    sessionId: saved.sessionId,
                    createdAt: saved.createdAt || Date.now(),
                    lastActiveAt: saved.lastActiveAt || Date.now(),
                    pendingQuestion: null,
                });
                restored++;
            }
            if (restored > 0) {
                console.log(`${LogPrefix.API_SESSION} 已恢复 ${restored} 个持久化会话绑定`);
            }
        } catch (error) {
            console.error(`${LogPrefix.API_SESSION} 绑定恢复失败（忽略，按全新状态运行）: ${error.message}`);
        }
    }

    /**
     * 清理空闲超时的绑定
     */
    #sweepIdle() {
        const timeoutMs = this.#roleRegistry.getSessionConfig().idleTimeoutMinutes * 60 * 1000;
        const now = Date.now();
        const expired = [];
        for (const [credential, binding] of this.#bindings.entries()) {
            if (now - binding.lastActiveAt > timeoutMs) expired.push(credential);
        }
        if (expired.length === 0) return;
        for (const credential of expired) {
            this.#bindings.delete(credential);
        }
        this.#persist();
        console.log(`${LogPrefix.API_SESSION} 清理空闲超时会话 ${expired.length} 个`);
    }
}

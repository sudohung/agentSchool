/**
 * OpenCode 实例探活与恢复监视器
 * 职责：
 *  1. 周期性探测 OpenCode 服务（v1 用 /global/health，v2 用 /api/info）
 *  2. 连续失败达到阈值判定不可用（down），恢复后触发 recovered
 *  3. 通过 hostname+pid 识别 v2 实例重启（容器/进程重启后会话失效）
 */

import { authHeaders } from './opencode-agent.js';
import { LogPrefix } from '../constants.js';

/** 默认探活间隔（毫秒），可用 AGENTBOT_HEALTH_INTERVAL_MS 覆盖 */
const DEFAULT_INTERVAL_MS = Number(process.env.AGENTBOT_HEALTH_INTERVAL_MS || 30_000);
/** 默认连续失败阈值，可用 AGENTBOT_HEALTH_FAILURES 覆盖 */
const DEFAULT_FAILURE_THRESHOLD = Number(process.env.AGENTBOT_HEALTH_FAILURES || 2);
/** 单次探活超时（毫秒） */
const PROBE_TIMEOUT_MS = 5_000;

/**
 * 探活监视器类
 */
export class HealthMonitor {
    #getBaseUrl;
    #intervalMs;
    #failureThreshold;
    #onChange;
    #timer = null;
    #running = false;
    /** @type {boolean|null} 健康状态（null=尚未探测） */
    #healthy = null;
    /** @type {number} 连续失败次数 */
    #failures = 0;
    /** @type {string} 实例身份（v2 hostname+pid，用于识别重启） */
    #identity = '';

    /**
     * @param {{getBaseUrl:Function, intervalMs?:number, failureThreshold?:number, onChange?:Function}} options
     */
    constructor({ getBaseUrl, intervalMs, failureThreshold, onChange }) {
        if (typeof getBaseUrl !== 'function') throw new Error('HealthMonitor 初始化失败：缺少 getBaseUrl');
        this.#getBaseUrl = getBaseUrl;
        this.#intervalMs = intervalMs || DEFAULT_INTERVAL_MS;
        this.#failureThreshold = failureThreshold || DEFAULT_FAILURE_THRESHOLD;
        this.#onChange = onChange || null;
    }

    /** 当前是否健康（null 表示尚未探测） */
    get healthy() {
        return this.#healthy;
    }

    /** 启动周期探活 */
    start() {
        if (this.#running) return;
        this.#running = true;
        this.#tick();
        this.#timer = setInterval(() => this.#tick(), this.#intervalMs);
        this.#timer.unref?.();
        console.log(`${LogPrefix.EVENTS} OpenCode 探活已启动（间隔 ${this.#intervalMs}ms，失败阈值 ${this.#failureThreshold}）`);
    }

    /** 停止探活 */
    stop() {
        this.#running = false;
        if (this.#timer) {
            clearInterval(this.#timer);
            this.#timer = null;
        }
    }

    /**
     * 探测一次实例状态
     * @returns {Promise<{ok:boolean, protocol?:'v1'|'v2', version?:string, identity?:string}>}
     */
    async #probe() {
        const baseUrl = (this.#getBaseUrl() || '').replace(/\/+$/, '');
        if (!baseUrl) return { ok: false };
        const headers = authHeaders();

        // v2：/api/info 返回 JSON（含 version/pid/hostname）
        try {
            const res = await fetch(`${baseUrl}/api/info`, { headers, signal: AbortSignal.timeout(PROBE_TIMEOUT_MS) });
            const contentType = res.headers.get('content-type') || '';
            if (res.ok && contentType.includes('json')) {
                const info = await res.json().catch(() => null);
                if (String(info?.version || '').startsWith('2')) {
                    return {
                        ok: true,
                        protocol: 'v2',
                        version: info.version,
                        identity: `${info.hostname || ''}#${info.pid ?? ''}`,
                    };
                }
            }
        } catch {
            // 继续尝试 v1 探活
        }

        // v1：/global/health 返回 JSON
        try {
            const res = await fetch(`${baseUrl}/global/health`, { headers, signal: AbortSignal.timeout(PROBE_TIMEOUT_MS) });
            const contentType = res.headers.get('content-type') || '';
            if (res.ok && contentType.includes('json')) {
                const health = await res.json().catch(() => null);
                if (health?.healthy) {
                    return { ok: true, protocol: 'v1', version: health.version };
                }
            }
        } catch {
            // 实例不可达
        }
        return { ok: false };
    }

    /** 一次探活周期 */
    async #tick() {
        if (!this.#running) return;
        const result = await this.#probe();
        const previous = this.#healthy;

        if (result.ok) {
            this.#failures = 0;
            const restarted = Boolean(this.#identity && result.identity && result.identity !== this.#identity);
            if (result.identity) this.#identity = result.identity;
            this.#healthy = true;

            if (previous !== true) {
                this.#emit({
                    type: previous === false ? 'recovered' : 'up',
                    protocol: result.protocol,
                    version: result.version,
                    restarted: false,
                });
            } else if (restarted) {
                this.#emit({ type: 'restarted', protocol: result.protocol, version: result.version, restarted: true });
            }
            return;
        }

        this.#failures += 1;
        if (this.#healthy !== false && this.#failures >= this.#failureThreshold) {
            this.#healthy = false;
            this.#emit({ type: 'down', failures: this.#failures });
        }
    }

    /** 派发状态变更事件（隔离回调异常） */
    #emit(event) {
        try {
            this.#onChange?.(event);
        } catch (error) {
            console.error(`${LogPrefix.EVENTS} 探活回调异常: ${error.message}`);
        }
    }
}
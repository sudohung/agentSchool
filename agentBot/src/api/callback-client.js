/**
 * opencode 回调执行器
 * 职责：
 *  1. 反向校验回调目标：实例可达（ping）+ 会话归属（sessionExists），防配错/谎报
 *  2. 结果推送：POST /session/{sessionId}/message（参照 opencode-scheduler 的做法）
 *     - 提交超时/中断视为服务端已入队（不算失败，opencode 会排队处理）
 *     - 确定性失败按指数退避重试
 */

import { LogPrefix } from '../constants.js';

/** 单次请求超时（毫秒） */
const REQUEST_TIMEOUT_MS = 15000;
/** 推送重试次数（首次 + 重试） */
const PUSH_MAX_ATTEMPTS = 3;
/** 重试基础退避（毫秒），按次数翻倍：2s / 4s */
const RETRY_BACKOFF_BASE_MS = 2000;

/** 规范化 baseUrl（去尾部斜杠） */
function normalizeBaseUrl(baseUrl) {
    return String(baseUrl ?? '').trim().replace(/\/+$/, '');
}

/**
 * 通用 HTTP 请求（AbortController 超时控制，返回解析后的 JSON）
 */
async function request(pathname, options = {}, timeoutMs = REQUEST_TIMEOUT_MS, baseUrl) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(new Error(`request timeout: ${pathname}`)), timeoutMs);
    try {
        const res = await fetch(normalizeBaseUrl(baseUrl) + pathname, { ...options, signal: ctrl.signal });
        const text = await res.text();
        let body = null;
        try { body = text ? JSON.parse(text) : null; } catch { body = text; }
        if (!res.ok) {
            const err = new Error(`opencode API ${res.status}: ${typeof body === 'string' ? body.slice(0, 300) : JSON.stringify(body)?.slice(0, 300)}`);
            err.status = res.status;
            throw err;
        }
        return body;
    } finally {
        clearTimeout(timer);
    }
}

/**
 * 回调执行器类
 */
export class CallbackClient {
    /**
     * 反向校验回调目标（参照 scheduler registerInstance 的验证逻辑）
     * @param {string} baseUrl - 调用方 opencode 实例地址
     * @param {string} sessionId - 调用方当前会话 id
     * @throws 校验失败时抛出带指引的错误
     */
    async verifyTarget(baseUrl, sessionId) {
        const url = normalizeBaseUrl(baseUrl);
        if (!/^https?:\/\/.+/.test(url)) {
            throw new Error(`callback.baseUrl 格式无效: ${baseUrl}（应为 http(s)://ip:port）`);
        }
        if (!sessionId) {
            throw new Error('callback.sessionId 不能为空（调用方需提供自身当前会话 id）');
        }

        // 可达性检查
        try {
            await request('/session?limit=1', {}, 5000, url);
        } catch (error) {
            throw new Error(`回调目标实例不可达: ${url}（${error.message}）`);
        }

        // 会话归属检查（404 = 会话不存在于该实例）
        try {
            await request(`/session/${sessionId}`, {}, 10000, url);
        } catch (error) {
            if (error.status === 404) {
                throw new Error(`回调目标会话 ${sessionId} 不存在于实例 ${url}，请检查 sessionId 是否为该实例的会话`);
            }
            throw new Error(`回调目标会话校验失败: ${error.message}`);
        }
    }

    /**
     * 推送结果消息到调用方会话（含重试）
     * @param {string} baseUrl
     * @param {string} sessionId
     * @param {string} text - 推送文本
     * @returns {Promise<boolean>} 是否成功（含"已入队"判定）
     */
    async pushWithRetry(baseUrl, sessionId, text) {
        for (let attempt = 1; attempt <= PUSH_MAX_ATTEMPTS; attempt++) {
            const ok = await this.#pushOnce(baseUrl, sessionId, text);
            if (ok) return true;
            if (attempt < PUSH_MAX_ATTEMPTS) {
                const delay = RETRY_BACKOFF_BASE_MS * attempt;
                console.warn(`${LogPrefix.CALLBACK} 推送失败，${delay / 1000}s 后重试（${attempt}/${PUSH_MAX_ATTEMPTS - 1}）: session=${sessionId}`);
                await new Promise((resolve) => setTimeout(resolve, delay));
            }
        }
        return false;
    }

    /**
     * 单次推送
     * 提交超时/连接中断时 prompt 通常已在服务端入队（opencode 会排队），视为成功
     */
    async #pushOnce(baseUrl, sessionId, text) {
        try {
            await request(`/session/${sessionId}/message`, {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ parts: [{ type: 'text', text }] }),
            }, REQUEST_TIMEOUT_MS, baseUrl);
            return true;
        } catch (error) {
            if (/request timeout|terminated|aborted/i.test(error.message)) {
                console.warn(`${LogPrefix.CALLBACK} 推送提交超时（视为已入队）: session=${sessionId}`);
                return true;
            }
            console.warn(`${LogPrefix.CALLBACK} 推送失败: session=${sessionId}, ${error.message}`);
            return false;
        }
    }
}

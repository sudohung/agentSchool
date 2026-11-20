/**
 * OpenCode 客户端：同时兼容 v1（无鉴权 /session 系列）与 v2（Basic 鉴权 /api/session 系列）
 *
 * 版本差异（已实测）：
 *  - v1：POST /session/{id}/prompt_async 立即 204，流式内容走 GET /event 的 message.part.delta
 *  - v2：POST /api/session/{id}/prompt 立即返回，流式内容走 GET /api/event 的 session.text.delta
 */

import { EngineVersion, ErrorCode, LogPrefix } from '../constants.js';
import { httpError } from '../http/respond.js';

/** v2 Basic 认证用户名固定为 opencode */
const V2_USERNAME = 'opencode';

/** 单次 HTTP 调用超时（不含长连接事件流） */
const REQUEST_TIMEOUT_MS = 30000;

export class OpencodeClient {
    /** @type {import('../config.js').loadConfig extends Function ? any : any} */
    #engine;
    /** @type {'v1'|'v2'|null} */
    #version = null;
    /** @type {Promise<'v1'|'v2'>|null} 并发探测只发一次 */
    #detecting = null;

    /** @param {{key:string,label:string,baseUrl:string,version:string,password:string,directory:string}} engine */
    constructor(engine) {
        this.#engine = engine;
    }

    get key() {
        return this.#engine.key;
    }

    get label() {
        return this.#engine.label;
    }

    get baseUrl() {
        return this.#engine.baseUrl;
    }

    get directory() {
        return this.#engine.directory;
    }

    /** v2 认证头（v1 不需要） */
    get authHeader() {
        if (!this.#engine.password) return {};
        const raw = Buffer.from(`${V2_USERNAME}:${this.#engine.password}`).toString('base64');
        return { Authorization: `Basic ${raw}` };
    }

    /**
     * 探测协议版本（缓存）
     * 判定依据：/api/info 返回 version 以 2 开头即 v2；无密码时直接按 v1
     * @returns {Promise<'v1'|'v2'>}
     */
    async ensureVersion() {
        if (this.#version) return this.#version;
        if (this.#detecting) return this.#detecting;

        if (this.#engine.version === EngineVersion.V1 || this.#engine.version === EngineVersion.V2) {
            this.#version = this.#engine.version;
            return this.#version;
        }

        this.#detecting = (async () => {
            try {
                const res = await fetch(`${this.baseUrl}/api/info`, {
                    headers: this.authHeader,
                    signal: AbortSignal.timeout(5000),
                });
                if (res.ok) {
                    const info = await res.json().catch(() => null);
                    if (String(info?.version || '').startsWith('2')) return EngineVersion.V2;
                }
            } catch {
                // 探测失败按 v1 处理，后续调用会暴露真实错误
            }
            return EngineVersion.V1;
        })();

        try {
            this.#version = await this.#detecting;
        } finally {
            this.#detecting = null;
        }
        return this.#version;
    }

    /** 清空版本缓存（引擎重启/协议变化时用） */
    resetVersion() {
        this.#version = null;
    }

    /**
     * 统一发请求并解析 JSON
     * @param {string} method
     * @param {string} path
     * @param {any} [body]
     * @param {{raw?:boolean}} [options]
     */
    async request(method, path, body, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const headers = { Accept: 'application/json', ...this.authHeader };
        if (body !== undefined) headers['Content-Type'] = 'application/json';

        let res;
        try {
            res = await fetch(url, {
                method,
                headers,
                body: body === undefined ? undefined : JSON.stringify(body),
                signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
            });
        } catch (error) {
            throw httpError(502, ErrorCode.ENGINE_ERROR, `OpenCode 请求失败 ${method} ${path}: ${error.message}`);
        }

        if (options.raw) return res;

        const text = await res.text();
        if (!res.ok) {
            throw httpError(
                res.status === 404 ? 404 : 502,
                ErrorCode.ENGINE_ERROR,
                `OpenCode 返回 ${res.status} ${method} ${path}: ${text.slice(0, 300)}`,
            );
        }
        if (!text) return null;
        try {
            return JSON.parse(text);
        } catch {
            return text;
        }
    }

    /**
     * 健康探测
     */
    async health() {
        try {
            const res = await fetch(`${this.baseUrl}/global/health`, {
                headers: this.authHeader,
                signal: AbortSignal.timeout(4000),
            });
            return res.ok;
        } catch {
            return false;
        }
    }

    // ==================== 会话 ====================

    /**
     * 创建会话
     * @param {{title?:string, model?:{providerID:string, modelID:string}}} [input]
     * @returns {Promise<string>} opencode 会话 ID
     */
    async createSession(input = {}) {
        const version = await this.ensureVersion();
        if (version === EngineVersion.V2) {
            const body = { title: input.title };
            if (input.model?.providerID && input.model?.modelID) {
                body.model = { providerID: input.model.providerID, id: input.model.modelID };
            }
            if (this.directory) body.location = { directory: this.directory };
            const res = await this.request('POST', '/api/session', body);
            const id = res?.data?.id;
            if (!id) throw httpError(502, ErrorCode.ENGINE_ERROR, `创建 v2 会话未返回 ID: ${JSON.stringify(res).slice(0, 200)}`);
            return id;
        }

        const body = { title: input.title };
        if (input.model?.providerID && input.model?.modelID) {
            body.model = { id: input.model.modelID, providerID: input.model.providerID };
        }
        const query = this.directory ? `?directory=${encodeURIComponent(this.directory)}` : '';
        const res = await this.request('POST', `/session${query}`, body);
        const id = res?.id || res?.data?.id;
        if (!id) throw httpError(502, ErrorCode.ENGINE_ERROR, `创建 v1 会话未返回 ID: ${JSON.stringify(res).slice(0, 200)}`);
        return id;
    }

    /**
     * 异步发送一轮提问（不等结果，结果通过事件流获取）
     * @param {string} sessionId
     * @param {string} text
     * @param {{messageID?:string, system?:string}} [options]
     */
    async promptAsync(sessionId, text, options = {}) {
        const version = await this.ensureVersion();
        if (version === EngineVersion.V2) {
            if (!text) throw httpError(400, ErrorCode.BAD_REQUEST, '提问内容不能为空');
            await this.request('POST', `/api/session/${encodeURIComponent(sessionId)}/prompt`, { text });
            return;
        }

        const body = { parts: [{ type: 'text', text }] };
        if (options.messageID) body.messageID = options.messageID;
        if (options.system) body.system = options.system;
        const query = this.directory ? `?directory=${encodeURIComponent(this.directory)}` : '';
        await this.request('POST', `/session/${encodeURIComponent(sessionId)}/prompt_async${query}`, body);
    }

    /**
     * 中断当前生成
     * @param {string} sessionId
     */
    async abort(sessionId) {
        const version = await this.ensureVersion();
        const path = version === EngineVersion.V2
            ? `/api/session/${encodeURIComponent(sessionId)}/interrupt`
            : `/session/${encodeURIComponent(sessionId)}/abort`;
        try {
            await this.request('POST', path, {});
            return true;
        } catch (error) {
            console.warn(`${LogPrefix.ENGINE} 中断会话失败 ${sessionId}: ${error.message}`);
            return false;
        }
    }

    /**
     * 拉取会话消息（用于断线补偿/历史同步）
     * @param {string} sessionId
     * @param {{limit?:number}} [options]
     */
    async listMessages(sessionId, options = {}) {
        const version = await this.ensureVersion();
        const limit = options.limit || 50;
        if (version === EngineVersion.V2) {
            const res = await this.request(
                'GET',
                `/api/session/${encodeURIComponent(sessionId)}/message?order=asc&limit=${limit}`,
            );
            const items = res?.data || res || [];
            return items.map((item) => ({
                role: item?.role === 'user' ? 'user' : 'assistant',
                text: extractV2Text(item),
            }));
        }
        const res = await this.request('GET', `/session/${encodeURIComponent(sessionId)}/message?limit=${limit}`);
        const items = Array.isArray(res) ? res : res?.data || [];
        return items.map((item) => ({
            role: item?.info?.role === 'user' ? 'user' : 'assistant',
            text: (item?.parts || [])
                .filter((part) => part.type === 'text' && !part.synthetic)
                .map((part) => part.text)
                .join(''),
        }));
    }

    // ==================== 交互闭环 ====================

    /**
     * 回复表单提问
     * @param {string} sessionId
     * @param {string} formId
     * @param {Array<string>} labels 按字段顺序选中的标签
     */
    async replyForm(sessionId, formId, labels) {
        const version = await this.ensureVersion();
        if (version === EngineVersion.V2) {
            const detail = await this.request(
                'GET',
                `/api/session/${encodeURIComponent(sessionId)}/form/${encodeURIComponent(formId)}`,
            );
            const fields = (detail?.data?.fields || []).filter((field) => !field.hidden);
            if (!fields.length) throw httpError(404, ErrorCode.NOT_FOUND, '表单不存在或已失效');

            const answer = {};
            (labels || []).forEach((label, index) => {
                const field = fields[index] || fields[0];
                if (!field?.key || label === undefined || label === null || label === '') return;
                const option = (field.options || []).find((item) => item.label === label || item.value === label);
                answer[field.key] = field.type === 'multiselect' ? [option?.value || String(label)] : (option?.value || label);
            });
            if (Object.keys(answer).length === 0) throw httpError(400, ErrorCode.BAD_REQUEST, '回答内容为空');
            await this.request(
                'POST',
                `/api/session/${encodeURIComponent(sessionId)}/form/${encodeURIComponent(formId)}/reply`,
                { answer },
            );
            return true;
        }

        await this.request('POST', `/question/${encodeURIComponent(formId)}/reply`, {
            answers: (labels || []).map((label) => [label]),
        });
        return true;
    }

    /**
     * 回复权限申请
     * @param {string} sessionId
     * @param {string} requestId
     * @param {'once'|'always'|'reject'} decision
     */
    async replyPermission(sessionId, requestId, decision) {
        const version = await this.ensureVersion();
        if (version === EngineVersion.V2) {
            await this.request(
                'POST',
                `/api/session/${encodeURIComponent(sessionId)}/permission/${encodeURIComponent(requestId)}/reply`,
                { decision },
            );
            return true;
        }
        await this.request('POST', `/permission/${encodeURIComponent(requestId)}/reply`, { reply: decision });
        return true;
    }

    // ==================== 事件流地址 ====================

    /**
     * 事件流地址与请求头
     * @returns {Promise<{url:string, headers:Object}>}
     */
    async eventEndpoint() {
        const version = await this.ensureVersion();
        return {
            url: `${this.baseUrl}${version === EngineVersion.V2 ? '/api/event' : '/event'}`,
            headers: { Accept: 'text/event-stream', ...this.authHeader },
        };
    }
}

/**
 * 提取 v2 消息文本（兼容 message 列表的多种载荷结构）
 * @param {any} item
 */
function extractV2Text(item) {
    if (typeof item?.payload?.text === 'string') return item.payload.text;
    if (typeof item?.text === 'string') return item.text;
    const parts = item?.parts || item?.content || [];
    return parts
        .filter((part) => part?.type === 'text')
        .map((part) => part.text || '')
        .join('');
}
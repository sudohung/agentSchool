/**
 * OpenCode 事件总线
 *
 * 每个引擎只维持一条 SSE 长连接，按 opencode 会话 ID 分发给订阅者。
 * 事件结构差异由 EventNormalizer 抹平（v1 properties / v2 data）。
 */

import { EventEmitter } from 'events';
import { EventNormalizer } from './event-normalizer.js';
import { LogPrefix } from '../constants.js';

/** 重连退避 */
const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 15000;

/** 心跳超时：超过该时长没有任何字节（含注释心跳）视为连接僵死 */
const IDLE_TIMEOUT_MS = 60000;

export class OpencodeEventBus extends EventEmitter {
    /** @type {import('./client.js').OpencodeClient} */
    #client;
    /** @type {AbortController|null} */
    #controller = null;
    /** @type {boolean} */
    #stopped = false;
    /** @type {number} */
    #delay = RECONNECT_BASE_MS;
    /** @type {number} 当前连接代数，用于丢弃旧连接的收尾逻辑 */
    #generation = 0;
    /** @type {EventNormalizer} */
    #normalizer = new EventNormalizer();

    /** @param {import('./client.js').OpencodeClient} client */
    constructor(client) {
        super();
        this.setMaxListeners(0);
        this.#client = client;
    }

    get engineKey() {
        return this.#client.key;
    }

    /** 启动事件订阅循环 */
    start() {
        this.#stopped = false;
        this.#loop();
    }

    /** 停止事件订阅 */
    stop() {
        this.#stopped = true;
        this.#controller?.abort();
        this.#controller = null;
    }

    /** 强制重连（引擎重启/地址变更后调用） */
    reconnect() {
        this.#client.resetVersion();
        this.#controller?.abort();
    }

    /**
     * 订阅某会话的事件
     * @param {string} sessionId
     * @param {(event:Object)=>void} handler
     * @returns {()=>void} 取消订阅
     */
    subscribeSession(sessionId, handler) {
        const wrapped = (event) => {
            if (event.sessionId !== sessionId) return;
            handler(event);
        };
        this.on('session', wrapped);
        return () => this.off('session', wrapped);
    }

    /** 主循环：连接 -> 读流 -> 断线重连 */
    async #loop() {
        while (!this.#stopped) {
            const generation = ++this.#generation;
            try {
                await this.#consume(generation);
            } catch (error) {
                if (!this.#stopped) {
                    console.warn(`${LogPrefix.BUS} 事件流中断(${this.#client.key}): ${error.message}`);
                }
            }
            if (this.#stopped) break;

            await sleep(this.#delay);
            this.#delay = Math.min(this.#delay * 2, RECONNECT_MAX_MS);
        }
    }

    /**
     * 建立并消费一次 SSE 连接
     * @param {number} generation
     */
    async #consume(generation) {
        const { url, headers } = await this.#client.eventEndpoint();
        const controller = new AbortController();
        this.#controller = controller;

        let idleTimer = setTimeout(() => controller.abort(), IDLE_TIMEOUT_MS);
        const resetIdle = () => {
            clearTimeout(idleTimer);
            idleTimer = setTimeout(() => controller.abort(), IDLE_TIMEOUT_MS);
        };

        try {
            const res = await fetch(url, { headers, signal: controller.signal });
            if (!res.ok || !res.body) {
                throw new Error(`订阅失败 HTTP ${res.status}`);
            }
            console.log(`${LogPrefix.BUS} 事件流已连接(${this.#client.key}) ${url}`);
            this.#delay = RECONNECT_BASE_MS;
            this.#normalizer.reset();
            this.emit('connected', this.#client.key);

            const decoder = new TextDecoder();
            let buffer = '';
            let eventName = '';
            let dataLines = [];

            for await (const chunk of res.body) {
                if (this.#stopped || generation !== this.#generation) break;
                resetIdle();

                buffer += decoder.decode(chunk, { stream: true });
                let newlineIndex;
                while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
                    const line = buffer.slice(0, newlineIndex).replace(/\r$/, '');
                    buffer = buffer.slice(newlineIndex + 1);

                    if (line === '') {
                        // 空行 = 一帧结束
                        if (dataLines.length) {
                            this.#handleFrame(eventName, dataLines.join('\n'));
                        }
                        eventName = '';
                        dataLines = [];
                        continue;
                    }
                    if (line.startsWith(':')) continue; // 注释心跳
                    if (line.startsWith('event:')) {
                        eventName = line.slice(6).trim();
                    } else if (line.startsWith('data:')) {
                        dataLines.push(line.slice(5).trimStart());
                    }
                }
            }
        } finally {
            clearTimeout(idleTimer);
            if (this.#controller === controller) this.#controller = null;
        }
    }

    /**
     * 解析一帧并广播
     * @param {string} eventName
     * @param {string} raw
     */
    #handleFrame(eventName, raw) {
        if (!raw || raw === '{}') return;
        let payload;
        try {
            payload = JSON.parse(raw);
        } catch {
            return;
        }
        for (const event of this.#normalizer.normalize(payload, eventName)) {
            this.emit('session', event);
            this.emit(event.kind, event);
        }
    }
}

/**
 * @param {number} ms
 */
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
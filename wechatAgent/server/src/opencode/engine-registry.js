/**
 * 引擎注册表：按引擎 key 管理客户端与事件总线
 */

import { OpencodeClient } from './client.js';
import { OpencodeEventBus } from './event-bus.js';
import { httpError } from '../http/respond.js';
import { ErrorCode, LogPrefix } from '../constants.js';

/**
 * 一个引擎客户端 + 一条事件总线的组合
 */
class EngineRuntime {
    /** @type {OpencodeClient} */
    client;
    /** @type {OpencodeEventBus} */
    bus;

    /** @param {Object} engineConfig */
    constructor(engineConfig) {
        this.client = new OpencodeClient(engineConfig);
        this.bus = new OpencodeEventBus(this.client);
    }

    start() {
        this.bus.start();
    }

    stop() {
        this.bus.stop();
    }
}

export class EngineRegistry {
    /** @type {Map<string, EngineRuntime>} */
    #runtimes = new Map();
    /** @type {string} */
    #defaultKey;

    /** @param {Object} config */
    constructor(config) {
        this.#defaultKey = config.defaultEngine;
        for (const [key, engineConfig] of Object.entries(config.engines)) {
            this.#runtimes.set(key, new EngineRuntime(engineConfig));
        }
    }

    /** 启动所有事件订阅 */
    start() {
        for (const runtime of this.#runtimes.values()) runtime.start();
    }

    /** 停止所有事件订阅 */
    stop() {
        for (const runtime of this.#runtimes.values()) runtime.stop();
    }

    /** 默认引擎 key */
    get defaultKey() {
        return this.#defaultKey;
    }

    /**
     * 按 key 取运行时（key 为空则用默认引擎）
     * @param {string} [key]
     * @returns {EngineRuntime}
     */
    get(key) {
        const resolved = key || this.#defaultKey;
        const runtime = this.#runtimes.get(resolved);
        if (!runtime) {
            throw httpError(400, ErrorCode.BAD_REQUEST, `未知引擎: ${resolved}`);
        }
        return runtime;
    }

    /** 引擎清单（下发给前端做选择器） */
    list() {
        return [...this.#runtimes.entries()].map(([key, runtime]) => ({
            key,
            label: runtime.client.label,
            version: runtime.client.baseUrl ? 'auto' : 'auto',
            directory: runtime.client.directory,
        }));
    }

    /**
     * 引擎健康状态
     * @returns {Promise<Array<{key:string,label:string,ok:boolean,url:string}>>}
     */
    async health() {
        const entries = [...this.#runtimes.entries()];
        return Promise.all(entries.map(async ([key, runtime]) => ({
            key,
            label: runtime.client.label,
            ok: await runtime.client.health(),
            url: runtime.client.baseUrl,
        })));
    }

    /** 热重载：清版本缓存并重连事件流 */
    reconnectAll() {
        for (const runtime of this.#runtimes.values()) runtime.bus.reconnect();
        console.log(`${LogPrefix.ENGINE} 已触发全部引擎重连`);
    }
}
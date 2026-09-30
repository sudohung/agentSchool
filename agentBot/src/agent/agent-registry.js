/**
 * Agent 注册表
 * 从 config/bot.json 读取定义，基于单一 OpenCode 客户端懒创建 Agent 实例
 * 支持配置管理页触发热重载（reload）
 */

import { createOpencodeClient } from '@opencode-ai/sdk';
import { BotConfig } from '../config/bot-config.js';
import { OpencodeAgent } from './opencode-agent.js';

/**
 * Agent 注册表类
 */
export class AgentRegistry {
    /** @type {Map<string, OpencodeAgent>} */
    #agents = new Map();
    /** @type {string} */
    #defaultKey;
    /** @type {string} */
    #baseUrl;
    /** @type {Object} OpenCode SDK 客户端（事件订阅等共用） */
    #client;

    constructor() {
        this.#build();
    }

    /**
     * 构建客户端与 Agent 表
     */
    #build() {
        const cfg = BotConfig.loadBotConfig();
        if (!Array.isArray(cfg.agents) || cfg.agents.length === 0) {
            throw new Error('Agent 注册表为空：请检查 config/bot.json');
        }

        // 单一 OpenCode 客户端，所有 Agent 共享
        this.#client = createOpencodeClient({ baseUrl: cfg.opencodeBaseUrl });
        this.#baseUrl = cfg.opencodeBaseUrl;

        this.#agents = new Map();
        for (const def of cfg.agents) {
            if (!def.key || !def.provider || !def.model) {
                console.warn(`[AgentRegistry] 跳过不完整的 Agent 定义: ${JSON.stringify(def)}`);
                continue;
            }
            this.#agents.set(def.key, new OpencodeAgent(this.#client, def));
        }

        this.#defaultKey = this.#agents.has(cfg.defaultKey)
            ? cfg.defaultKey
            : [...this.#agents.keys()][0];

        console.log(`[AgentRegistry] 已加载 ${this.#agents.size} 个 Agent（${cfg.opencodeBaseUrl}），默认: ${this.#defaultKey}`);
    }

    /**
     * 热重载配置（配置管理页保存后调用）
     * @returns {{baseUrl:string, count:number, defaultKey:string}}
     */
    reload() {
        this.#build();
        return { baseUrl: this.#baseUrl, count: this.#agents.size, defaultKey: this.#defaultKey };
    }

    /** 获取共享的 OpenCode 客户端 */
    getClient() {
        return this.#client;
    }

    /** 获取当前服务地址 */
    getBaseUrl() {
        return this.#baseUrl;
    }

    /**
     * 获取 Agent 实例
     * @param {string} [key] - 为空返回默认 Agent
     * @returns {OpencodeAgent|null}
     */
    getAgent(key) {
        if (!key) return this.#agents.get(this.#defaultKey) || null;
        return this.#agents.get(key) || null;
    }

    /** 判断 Agent 是否存在 */
    hasAgent(key) {
        return this.#agents.has(key);
    }

    /** 获取默认 Agent key */
    getDefaultKey() {
        return this.#defaultKey;
    }

    /**
     * 列出所有 Agent 定义
     * @returns {Array<{key:string, name:string}>}
     */
    listAgents() {
        return [...this.#agents.entries()].map(([key, agent]) => ({ key, name: agent.getName() }));
    }

    /** 为所有 Agent 设置回调 */
    setCallbacksForAll(callbacks) {
        for (const agent of this.#agents.values()) {
            agent.setCallbacks(callbacks);
        }
    }
}

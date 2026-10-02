/**
 * OpenCode 实例池
 * 职责：
 *  1. 按实例 key 解析服务地址（未指定实例回退全局配置）
 *  2. 按「实例地址 + 模型」懒创建并缓存 OpencodeAgent（client 池，避免重复建连）
 *  3. 职能 -> Agent 的解析入口（模型未配置时兜底全局默认模型）
 */

import { createOpencodeClient } from '@opencode-ai/sdk';
import { BotConfig } from '../config/bot-config.js';
import { OpencodeAgent } from './opencode-agent.js';
import { LogPrefix } from '../constants.js';

/**
 * 实例池类
 */
export class InstancePool {
    /** @type {import('./role-registry.js').RoleRegistry} */
    #roleRegistry;
    /** @type {Map<string, OpencodeAgent>} 缓存键 -> Agent 实例 */
    #agents = new Map();

    constructor(roleRegistry) {
        if (!roleRegistry) throw new Error('InstancePool 初始化失败：缺少 RoleRegistry');
        this.#roleRegistry = roleRegistry;
    }

    /**
     * 解析实例服务地址
     * @param {string} instanceKey - 空/未注册实例回退全局地址
     * @returns {string}
     */
    resolveBaseUrl(instanceKey) {
        return this.#roleRegistry.resolveInstanceUrl(instanceKey);
    }

    /**
     * 解析职能的模型定义
     * role.model 支持 "provider/model" 格式；为空时兜底 bot.json 的默认 Agent 模型
     * @param {Object} role
     * @returns {{provider:string, model:string}}
     */
    #resolveModel(role) {
        const modelSpec = (role.model || '').trim();
        if (modelSpec && modelSpec.includes('/')) {
            const [provider, model] = modelSpec.split('/', 2);
            return { provider: provider.trim(), model: model.trim() };
        }
        if (modelSpec) {
            // 未带 provider 前缀时使用全局默认 provider
            return { provider: BotConfig.opencodeProvider, model: modelSpec };
        }

        // 兜底：bot.json 默认 Agent 的模型定义
        const cfg = BotConfig.loadBotConfig();
        const def = (cfg.agents || []).find((a) => a.key === cfg.defaultKey) || (cfg.agents || [])[0];
        if (!def?.provider || !def?.model) {
            throw new Error('职能未配置模型且无法从 bot.json 解析默认模型');
        }
        return { provider: def.provider, model: def.model };
    }

    /**
     * 获取职能对应的 Agent 实例（懒创建 + 缓存）
     * @param {Object} role - 职能定义
     * @returns {OpencodeAgent}
     */
    getAgentForRole(role) {
        if (!role?.key) throw new Error('获取 Agent 失败：职能定义不完整');

        const model = this.#resolveModel(role);
        const baseUrl = this.resolveBaseUrl(role.instance);
        // 项目目录：会话归档到 opencode UI 的对应项目下（空 = 服务端默认目录）
        const directory = this.#roleRegistry.resolveInstanceDirectory(role.instance);
        const cacheKey = `${baseUrl}|${directory}|${model.provider}|${model.model}`;

        let agent = this.#agents.get(cacheKey);
        if (agent) return agent;

        const client = createOpencodeClient({ baseUrl, directory: directory || undefined });
        agent = new OpencodeAgent(client, model, baseUrl);
        this.#agents.set(cacheKey, agent);
        console.log(`${LogPrefix.POOL} 创建 Agent: role=${role.key} model=${model.provider}/${model.model} instance=${baseUrl} directory=${directory || '(默认)'}`);
        return agent;
    }

    /** 清空缓存（配置热重载后调用，下次使用时按新配置重建） */
    invalidate() {
        this.#agents.clear();
        console.log(`${LogPrefix.POOL} Agent 缓存已清空，将在下次使用时按新配置重建`);
    }
}

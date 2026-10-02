/**
 * 职能注册表
 * 从 config/roles.json 读取职能定义与 OpenCode 实例注册表
 * 职能：对外（MCP 调用方）暴露的 Bot 能力单元，每个职能可独立配置提示词/实例/模型
 * 支持配置管理页触发热重载（reload）
 */

import { readFileSync, writeFileSync, renameSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { LogPrefix } from '../constants.js';
import { BotConfig } from '../config/bot-config.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

/** roles.json 路径 */
const ROLES_JSON_PATH = join(__dirname, '../../config/roles.json');

/** 会话队列配置默认值（syncWaitCapMs/longPollWindowMs 均须低于 MCP 客户端工具默认 30s 超时，避免 -32001） */
const SESSION_DEFAULTS = {
    idleTimeoutMinutes: 1440,
    maxConcurrent: 4,
    queueTimeoutMinutes: 10,
    syncWaitCapMs: 20000,
    longPollWindowMs: 25000,
};

/**
 * 职能注册表类
 */
export class RoleRegistry {
    /** @type {Map<string, Object>} roleKey -> 职能定义 */
    #roles = new Map();
    /** @type {Map<string, string>} instanceKey -> baseUrl */
    #instances = new Map();
    /** @type {Object} 会话队列配置 */
    #sessionConfig = { ...SESSION_DEFAULTS };

    constructor() {
        this.#load();
    }

    /**
     * 加载并校验配置
     */
    #load() {
        const cfg = this.#readRolesJson();
        this.#instances = new Map(Object.entries(cfg.instances || {}));

        this.#roles = new Map();
        for (const role of cfg.roles || []) {
            if (!role?.key || !role?.name) {
                console.warn(`${LogPrefix.ROLE} 跳过不完整的职能定义: ${JSON.stringify(role)}`);
                continue;
            }
            // 引用的实例必须已注册（空串表示用全局实例）
            const inst = role.instance || '';
            if (inst && !this.#instances.has(inst)) {
                console.warn(`${LogPrefix.ROLE} 职能 ${role.key} 引用未注册实例 "${inst}"，回退全局实例`);
                role.instance = '';
            }
            this.#roles.set(role.key, role);
        }

        this.#sessionConfig = { ...SESSION_DEFAULTS, ...(cfg.session || {}) };
        console.log(`${LogPrefix.ROLE} 已加载 ${this.#roles.size} 个职能，${this.#instances.size} 个自定义实例`);
    }

    /**
     * 读取 roles.json（不存在或损坏返回空结构，不让主流程崩溃）
     */
    #readRolesJson() {
        try {
            if (existsSync(ROLES_JSON_PATH)) {
                return JSON.parse(readFileSync(ROLES_JSON_PATH, 'utf-8'));
            }
        } catch (error) {
            console.error(`${LogPrefix.ROLE} roles.json 读取失败: ${error.message}`);
        }
        return { instances: {}, roles: [], session: {} };
    }

    /**
     * 热重载配置（配置管理页保存后调用）
     * @returns {{roleCount:number, instanceCount:number}}
     */
    reload() {
        this.#load();
        return { roleCount: this.#roles.size, instanceCount: this.#instances.size };
    }

    /**
     * 获取职能定义
     * @param {string} key
     * @returns {Object|null}
     */
    getRole(key) {
        return this.#roles.get(key) || null;
    }

    /**
     * 判断职能是否存在
     */
    hasRole(key) {
        return this.#roles.has(key);
    }

    /**
     * 列出可用职能（对外暴露的字段）
     * @returns {Array<{key:string, name:string, desc:string}>}
     */
    listRoles() {
        return [...this.#roles.values()].map((r) => ({
            key: r.key,
            name: r.name,
            desc: r.desc || '',
        }));
    }

    /**
     * 解析实例地址（职能未指定实例时用全局配置）
     * @param {string} instanceKey
     * @returns {string} baseUrl
     */
    resolveInstanceUrl(instanceKey) {
        if (!instanceKey || !this.#instances.has(instanceKey)) return BotConfig.getOpencodeBaseUrl();
        return this.#parseInstance(this.#instances.get(instanceKey)).baseUrl;
    }

    /**
     * 解析实例的项目目录（会话归档到 opencode UI 对应项目下；空 = 服务端默认目录）
     * @param {string} instanceKey
     * @returns {string} directory
     */
    resolveInstanceDirectory(instanceKey) {
        if (!instanceKey || !this.#instances.has(instanceKey)) return BotConfig.getOpencodeDirectory();
        return this.#parseInstance(this.#instances.get(instanceKey)).directory;
    }

    /**
     * 兼容两种实例配置格式："http://..." 字符串 或 { baseUrl, directory } 对象
     * @param {string|Object} raw
     * @returns {{baseUrl:string, directory:string}}
     */
    #parseInstance(raw) {
        if (typeof raw === 'string') return { baseUrl: raw, directory: '' };
        return { baseUrl: raw?.baseUrl || '', directory: raw?.directory || '' };
    }

    /** 获取会话队列配置 */
    getSessionConfig() {
        return { ...this.#sessionConfig };
    }

    /**
     * 获取完整配置（管理页读取用）
     * @returns {{instances:Object, roles:Array, session:Object}}
     */
    getConfig() {
        const cfg = this.#readRolesJson();
        return {
            instances: cfg.instances || {},
            roles: cfg.roles || [],
            session: this.#sessionConfig,
        };
    }

    /**
     * 校验并保存完整配置（原子写入 roles.json 后热重载）
     * @param {{instances:Object, roles:Array, session?:Object}} cfg
     * @returns {{roleCount:number, instanceCount:number}}
     */
    saveConfig(cfg) {
        // 校验实例表：key 非空、地址合法（支持字符串或 {baseUrl, directory} 对象）
        const instances = cfg?.instances || {};
        for (const [key, raw] of Object.entries(instances)) {
            const inst = typeof raw === 'string' ? { baseUrl: raw } : raw;
            if (!key.trim()) throw new Error('实例 key 不能为空');
            if (!/^https?:\/\//.test(inst?.baseUrl || '')) {
                throw new Error(`实例 ${key} 的地址必须以 http:// 或 https:// 开头`);
            }
        }

        // 校验职能：key/name 必填且唯一，引用实例必须已注册
        if (!Array.isArray(cfg?.roles) || cfg.roles.length === 0) {
            throw new Error('至少需要配置一个职能');
        }
        const keys = new Set();
        for (const role of cfg.roles) {
            if (!role?.key?.trim() || !role?.name?.trim()) {
                throw new Error('职能定义不完整：key/name 均必填');
            }
            if (keys.has(role.key)) throw new Error(`职能 key 重复: ${role.key}`);
            keys.add(role.key);
            // 乱码防御：文本字段含 U+FFFD 替换符说明源数据已被错误编码污染（如非 UTF-8 编辑器保存）
            const textFields = [role.name, role.desc, role.prompt];
            if (textFields.some((t) => typeof t === 'string' && t.includes('\uFFFD'))) {
                throw new Error(`职能 ${role.key} 的文本内容存在乱码（含替换符），请刷新页面后重新填写中文内容`);
            }
            const inst = role.instance || '';
            if (inst && !instances[inst]) {
                throw new Error(`职能 ${role.key} 引用了未注册的实例: ${inst}`);
            }
            if (role.model && role.model.includes('/') === false) {
                throw new Error(`职能 ${role.key} 的模型需为 "provider/model" 格式或留空`);
            }
            if (role.skills && !Array.isArray(role.skills)) {
                throw new Error(`职能 ${role.key} 的 skills 必须为数组`);
            }
        }

        // 原子写入
        const tmp = `${ROLES_JSON_PATH}.tmp`;
        writeFileSync(tmp, JSON.stringify({
            instances,
            roles: cfg.roles,
            session: { ...SESSION_DEFAULTS, ...(cfg.session || {}) },
        }, null, 2));
        renameSync(tmp, ROLES_JSON_PATH);

        return this.reload();
    }
}

/**
 * 运行配置加载
 * 优先级：环境变量 > config.json > config.example.json
 */

import { readFileSync, existsSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';
import { EngineVersion } from './constants.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

/** server 根目录（src 的上一级） */
export const SERVER_ROOT = resolve(__dirname, '..');

/** 配置文件候选路径 */
const CONFIG_PATHS = [
    process.env.AGENT_CONFIG || join(SERVER_ROOT, 'config.json'),
    join(SERVER_ROOT, 'config.example.json'),
];

/**
 * 读取首个存在的配置文件
 * @returns {{config: Object, path: string}}
 */
function readConfigFile() {
    for (const path of CONFIG_PATHS) {
        if (!existsSync(path)) continue;
        try {
            return { config: JSON.parse(readFileSync(path, 'utf-8')), path };
        } catch (error) {
            throw new Error(`配置文件解析失败 ${path}: ${error.message}`);
        }
    }
    throw new Error('未找到配置文件：请复制 config.example.json 为 config.json');
}

/**
 * 把引擎配置规范化为内部结构
 * @param {string} key
 * @param {Object} raw
 */
function normalizeEngine(key, raw) {
    const baseUrl = String(raw?.baseUrl || '').replace(/\/+$/, '');
    if (!/^https?:\/\//.test(baseUrl)) {
        throw new Error(`引擎 ${key} 的 baseUrl 必须以 http:// 或 https:// 开头`);
    }
    const version = [EngineVersion.V1, EngineVersion.V2].includes(raw?.version)
        ? raw.version
        : EngineVersion.AUTO;
    return {
        key,
        label: raw?.label || key,
        baseUrl,
        version,
        password: raw?.password || '',
        directory: raw?.directory || '',
    };
}

/**
 * 加载完整配置
 * @returns {Object}
 */
export function loadConfig() {
    const { config: fileConfig, path } = readConfigFile();

    const engines = {};
    for (const [key, raw] of Object.entries(fileConfig.engines || {})) {
        engines[key] = normalizeEngine(key, raw);
    }
    if (Object.keys(engines).length === 0) {
        throw new Error('配置缺少 engines：至少需要一个 OpenCode 引擎');
    }

    const defaultEngine = fileConfig.defaultEngine && engines[fileConfig.defaultEngine]
        ? fileConfig.defaultEngine
        : Object.keys(engines)[0];

    const models = Array.isArray(fileConfig.models) && fileConfig.models.length
        ? fileConfig.models.map((item, index) => ({
            key: item.key || `model-${index}`,
            label: item.label || item.key || `模型 ${index + 1}`,
            providerID: item.providerID || '',
            modelID: item.modelID || '',
        }))
        : [{ key: 'default', label: '引擎默认模型', providerID: '', modelID: '' }];

    // 环境变量覆盖：便于容器/临时调试，不必改文件
    if (process.env.OPENCODE_BASE_URL) {
        engines[defaultEngine].baseUrl = process.env.OPENCODE_BASE_URL.replace(/\/+$/, '');
    }
    if (process.env.OPENCODE_PASSWORD) {
        engines[defaultEngine].password = process.env.OPENCODE_PASSWORD;
    }
    if (process.env.OPENCODE_VERSION) {
        engines[defaultEngine].version = process.env.OPENCODE_VERSION;
    }

    return {
        configPath: path,
        port: Number(process.env.PORT || fileConfig.port || 8090),
        host: process.env.HOST || fileConfig.host || '0.0.0.0',
        defaultEngine,
        engines,
        models,
        wechat: {
            appId: process.env.WECHAT_APP_ID || fileConfig.wechat?.appId || '',
            appSecret: process.env.WECHAT_APP_SECRET || fileConfig.wechat?.appSecret || '',
            // 开发登录开关：开启后允许用 deviceId 登录（仅本地调试，生产必须关闭）
            allowDevLogin: process.env.WECHAT_ALLOW_DEV_LOGIN === 'true'
                || fileConfig.wechat?.allowDevLogin === true,
        },
        chat: {
            systemPrompt: fileConfig.chat?.systemPrompt || '',
            turnTimeoutMs: Number(fileConfig.chat?.turnTimeoutMs || 300000),
            heartbeatMs: Number(fileConfig.chat?.heartbeatMs || 15000),
        },
        dataDir: process.env.AGENT_DATA_DIR || join(SERVER_ROOT, 'data'),
    };
}
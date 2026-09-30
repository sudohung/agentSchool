/**
 * 机器人配置管理
 * 集中加载 .env 并提供校验，替代旧版分散的配置读取
 */

import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync, existsSync, writeFileSync, renameSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));

dotenv.config({ path: join(__dirname, '../../.env') });

/** bot.json 路径（运行时可变配置：服务地址 + 模型列表） */
const BOT_JSON_PATH = join(__dirname, '../../config/bot.json');

const int = (val, fallback) => {
    const n = parseInt(val, 10);
    return Number.isFinite(n) ? n : fallback;
};

/**
 * 读取 bot.json（不存在或损坏返回 null）
 */
function readBotJson() {
    try {
        if (existsSync(BOT_JSON_PATH)) {
            return JSON.parse(readFileSync(BOT_JSON_PATH, 'utf-8'));
        }
    } catch (error) {
        console.error(`[BotConfig] bot.json 读取失败: ${error.message}`);
    }
    return null;
}

export const BotConfig = {
    // 飞书应用配置
    appId: process.env.FEISHU_APP_ID || '',
    appSecret: process.env.FEISHU_APP_SECRET || '',
    defaultChatId: process.env.FEISHU_DEFAULT_CHAT_ID || '',

    // Webhook 通知
    webhookUrl: process.env.FEISHU_WEBHOOK_URL || '',
    webhookSecret: process.env.FEISHU_WEBHOOK_SECRET || '',

    // OpenCode 服务
    opencodeBaseUrl: process.env.OPENCODE_BASE_URL || 'http://127.0.0.1:4096',
    opencodeProvider: process.env.OPENCODE_PROVIDER || 'CodingPlan',
    defaultAgentKey: process.env.OPENCODE_DEFAULT_AGENT || 'main',

    // 消息处理配置
    messageConfig: {
        messageIdTtl: int(process.env.FEISHU_MESSAGE_ID_TTL, 3600000),
        messageExpiryTime: int(process.env.FEISHU_MESSAGE_EXPIRY_TIME, 120000),
        processingTimeout: int(process.env.FEISHU_PROCESSING_TIMEOUT, 5000),
    },

    // 日志配置
    logConfig: {
        level: process.env.FEISHU_LOG_LEVEL || 'info',
        debug: process.env.FEISHU_DEBUG === 'true',
    },

    /**
     * 校验配置完整性
     * @returns {boolean}
     */
    isValid() {
        return !!(this.appId && this.appSecret);
    },

    isDebugEnabled() {
        return this.logConfig.debug;
    },

    /**
     * 获取 OpenCode 服务地址（bot.json 优先，其次环境变量）
     * @returns {string}
     */
    getOpencodeBaseUrl() {
        return readBotJson()?.opencodeBaseUrl || this.opencodeBaseUrl;
    },

    /**
     * 加载完整运行时配置（bot.json 优先，旧 agents.json 做迁移兜底）
     * @returns {{opencodeBaseUrl:string, defaultKey:string, agents:Array, source:string}}
     */
    loadBotConfig() {
        const bj = readBotJson();
        if (bj?.agents?.length) {
            return {
                opencodeBaseUrl: bj.opencodeBaseUrl || this.opencodeBaseUrl,
                defaultKey: bj.defaultKey || 'main',
                agents: bj.agents,
                source: 'bot.json',
            };
        }
        // 迁移兜底：读旧 agents.json
        const legacy = this.loadAgentsConfig();
        return {
            opencodeBaseUrl: this.opencodeBaseUrl,
            defaultKey: legacy.defaultKey,
            agents: legacy.agents,
            source: 'agents.json',
        };
    },

    /**
     * 校验并保存运行时配置（原子写入 bot.json）
     * @param {{opencodeBaseUrl:string, defaultKey:string, agents:Array}} cfg
     * @returns {{urlChanged:boolean}} 保存结果
     */
    saveBotConfig({ opencodeBaseUrl, defaultKey, agents }) {
        // 校验服务地址
        if (!opencodeBaseUrl || !/^https?:\/\//.test(opencodeBaseUrl)) {
            throw new Error('OpenCode 地址必须以 http:// 或 https:// 开头');
        }

        // 校验 Agent 定义
        if (!Array.isArray(agents) || agents.length === 0) {
            throw new Error('至少需要配置一个 Agent');
        }
        const keys = new Set();
        for (const a of agents) {
            if (!a?.key || !a?.provider || !a?.model) {
                throw new Error('Agent 定义不完整：key/provider/model 均必填');
            }
            if (keys.has(a.key)) throw new Error(`Agent key 重复: ${a.key}`);
            keys.add(a.key);
        }
        if (!keys.has(defaultKey)) {
            throw new Error(`默认 Agent "${defaultKey}" 不在列表中`);
        }

        // 原子写入：先写临时文件再重命名
        const prevUrl = this.getOpencodeBaseUrl();
        const tmp = `${BOT_JSON_PATH}.tmp`;
        writeFileSync(tmp, JSON.stringify({ opencodeBaseUrl, defaultKey, agents }, null, 2));
        renameSync(tmp, BOT_JSON_PATH);

        return { urlChanged: prevUrl !== opencodeBaseUrl };
    },

    /**
     * 加载 Agent 注册表配置（兼容旧调用）
     * @returns {{agents: Array, defaultKey: string}}
     */
    loadAgentsConfig() {
        const agentsPath = join(__dirname, '../../config/agents.json');
        if (!existsSync(agentsPath)) {
            throw new Error(`Agent 配置文件不存在: ${agentsPath}`);
        }
        try {
            return JSON.parse(readFileSync(agentsPath, 'utf-8'));
        } catch (error) {
            throw new Error(`Agent 配置文件解析失败: ${error.message}`);
        }
    },
};

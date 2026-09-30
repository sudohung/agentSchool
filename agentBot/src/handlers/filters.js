/**
 * 消息过滤器
 * 责任链：群@校验 -> 黑名单过滤
 * 返回统一结构 { pass, type, reason }
 */

import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BAN_FILE = join(__dirname, '../../config/ban.json');

/** 黑名单缓存 */
let banCache = null;
let banCacheTime = 0;
const BAN_CACHE_TTL = 60_000;

/**
 * 读取黑名单 chatId 集合（1 分钟缓存）
 * @returns {Set<string>}
 */
function getBlockedChatIds() {
    const now = Date.now();
    if (banCache && now - banCacheTime < BAN_CACHE_TTL) return banCache;
    try {
        if (existsSync(BAN_FILE)) {
            const data = JSON.parse(readFileSync(BAN_FILE, 'utf-8'));
            banCache = new Set(data.blockedChatId || []);
        } else {
            banCache = new Set();
        }
    } catch (error) {
        console.error(`[Filters] 黑名单文件读取失败: ${error.message}`);
        banCache = new Set();
    }
    banCacheTime = now;
    return banCache;
}

/**
 * @typedef {Object} FilterResult
 * @property {boolean} pass
 * @property {string} type
 * @property {string} reason
 */

/**
 * 群消息过滤：群聊必须@机器人
 * @param {Object} messageContext - 飞书消息上下文
 * @returns {FilterResult|null} null 表示通过
 */
export function groupMentionFilter(messageContext) {
    if (messageContext?.chat_type !== 'group') return null;
    const mentioned = Array.isArray(messageContext.mentions)
        && messageContext.mentions.some((m) => m.key === '@_user_1');
    if (!mentioned) {
        return { pass: false, type: 'group', reason: '群消息未@机器人' };
    }
    return null;
}

/**
 * 黑名单过滤
 * @param {string} chatId
 * @returns {FilterResult|null}
 */
export function banFilter(chatId) {
    if (chatId && getBlockedChatIds().has(chatId)) {
        return { pass: false, type: 'ban', reason: `chatId ${chatId} 在黑名单中` };
    }
    return null;
}

/**
 * 执行完整过滤链
 * @returns {FilterResult} pass=true 表示放行
 */
export function runFilterChain(chatId, messageContext) {
    const results = [
        groupMentionFilter(messageContext),
        banFilter(chatId),
    ].filter(Boolean);
    return results.length > 0 ? results[0] : { pass: true, type: 'none', reason: '' };
}

/**
 * 预处理用户消息：移除 @机器人 占位符
 * @param {string} message
 * @returns {string}
 */
export function preprocessMessage(message) {
    return message.replace(/@_user_1\s*/g, '').trim();
}

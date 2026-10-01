/**
 * 出站内容脱敏过滤器
 * 所有写回飞书的内容（AI 回复/流式思考/提问卡片/错误卡片）统一经过此处，
 * 防止服务器路径、内网 IP、密钥凭证等系统敏感信息泄漏给聊天用户。
 * 开关：config/bot.json 的 security.maskSensitive（管理页可控制），默认开启。
 */

import { BotConfig } from '../config/bot-config.js';
import { LogPrefix } from '../constants.js';

/** 脱敏占位符 */
export const MaskPlaceholder = {
    IP: '[IP已脱敏]',
    PATH: '[路径已脱敏]',
    CREDENTIAL: '[凭证已脱敏]',
    CONN: '[连接串已脱敏]',
    STACK: '[堆栈已脱敏]',
};

/**
 * 脱敏规则表（按顺序执行）
 * 每条规则：{ name, pattern, placeholder }
 */
const RULES = [
    {
        name: 'connection-string',
        // mysql://user:pass@host:port/db、redis://、mongodb:// 等
        pattern: /\b[a-z][a-z0-9+.-]{1,15}:\/{2}[^\s'"<>]*@[^\s'"<>]+/gi,
        placeholder: MaskPlaceholder.CONN,
    },
    {
        name: 'credential',
        // sk- 开头密钥、Bearer token、JWT、AK/SK 赋值、长 hex/base64 串
        pattern: /\b(?:sk-[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._-]{8,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}|(?:ak|sk|secret|token|password|passwd|api[_-]?key)\s*[:=]\s*["']?[^\s"',;)]{6,})/gi,
        placeholder: MaskPlaceholder.CREDENTIAL,
    },
    {
        name: 'private-ip',
        // 内网/本机 IPv4：10.x、192.168.x、172.16-31.x、127.x
        pattern: /\b(?:(?:10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b/g,
        placeholder: MaskPlaceholder.IP,
    },
    {
        name: 'windows-path',
        // Windows 盘符绝对路径：E:\workspace\xxx、C:\Users\xxx
        pattern: /[A-Za-z]:\\(?:[^\\\/:*?"<>|\r\n]+\\)*[^\\\/:*?"<>|\r\n]+/g,
        placeholder: MaskPlaceholder.PATH,
    },
    {
        name: 'unix-path',
        // Unix 绝对路径：/workspace/xxx、/home/xxx、/root/xxx、/etc/xxx（避免误伤普通斜杠，限定常见根）
        pattern: /\/(?:workspace|home|root|etc|usr|var|opt|tmp|data)(?:\/[A-Za-z0-9._-]+)+/g,
        placeholder: MaskPlaceholder.PATH,
    },
    {
        name: 'stack-frame',
        // 堆栈帧：at xxx (file:line:col)
        pattern: /^\s*at\s+.+$/gm,
        placeholder: MaskPlaceholder.STACK,
    },
    {
        name: 'at-tag',
        // AI 回复中回显的 at 标签（如 <at id=open_id></at> 语法示例）：
        // 直接渲染会因无效用户资源导致卡片创建失败(230099)，机器人自己的 @ 前缀在脱敏后注入，不受影响
        pattern: /<at\s[^>]*>(?:\s*<\/at>)?|<\/at>/gi,
        placeholder: '',
    },
];

/** 单条内容长度上限：超过先截断再脱敏，防止超长卡片 */
const MAX_CONTENT_LENGTH = 4000;

/**
 * 判断脱敏开关是否开启（每次调用实时读取，管理页切换后立即生效）
 */
function maskEnabled() {
    return BotConfig.isMaskSensitiveEnabled();
}

/**
 * 对文本执行脱敏
 * @param {string} text - 原始文本
 * @param {string} [scene] - 调用场景（日志用）
 * @returns {string} 脱敏后的文本
 */
export function sanitizeText(text, scene = '') {
    if (typeof text !== 'string' || text.length === 0) return text || '';
    if (!maskEnabled()) return text;

    let result = text;
    let maskedCount = 0;
    for (const rule of RULES) {
        result = result.replace(rule.pattern, (match) => {
            maskedCount++;
            return rule.placeholder;
        });
    }
    if (maskedCount > 0) {
        console.warn(`${LogPrefix.SECURITY} 内容脱敏: 命中 ${maskedCount} 处（场景: ${scene || '未知'}）`);
    }

    // 长度保护：超长内容截断（飞书卡片有大小限制）
    if (result.length > MAX_CONTENT_LENGTH) {
        result = `${result.slice(0, MAX_CONTENT_LENGTH)}\n...（内容过长已截断）`;
    }
    return result;
}

/**
 * 脱敏对象中递归的字符串字段（用于提问 questions 等结构化数据）
 * @param {Object|Array} data - 任意嵌套结构
 * @param {string} [scene]
 * @returns {Object|Array} 脱敏后的新结构
 */
export function sanitizeDeep(data, scene = '') {
    if (!maskEnabled() || data === null || data === undefined) return data;
    if (typeof data === 'string') return sanitizeText(data, scene);
    if (Array.isArray(data)) return data.map((item) => sanitizeDeep(item, scene));
    if (typeof data === 'object') {
        const out = {};
        for (const [key, value] of Object.entries(data)) {
            out[key] = sanitizeDeep(value, scene);
        }
        return out;
    }
    return data;
}

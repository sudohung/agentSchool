/**
 * Webhook 通知发送模块
 * 用于群机器人通知（带签名与重试），独立于聊天消息通道
 */

import crypto from 'crypto';
import { BotConfig } from '../config/bot-config.js';
import { LogPrefix } from '../constants.js';

const RETRIES = 2;
const RETRY_BASE_DELAY = 500;

/**
 * 构造带签名的 webhook URL
 * @param {string} secret
 */
function signWebhookUrl(secret) {
    const webhookUrl = BotConfig.webhookUrl;
    if (!secret) return webhookUrl;
    try {
        const timestamp = Date.now().toString();
        const hmac = crypto.createHmac('sha256', secret);
        hmac.update(`${timestamp}\n${secret}`);
        const sign = hmac.digest('base64');
        const sep = webhookUrl.includes('?') ? '&' : '?';
        return `${webhookUrl}${sep}timestamp=${encodeURIComponent(timestamp)}&sign=${encodeURIComponent(sign)}`;
    } catch (error) {
        console.warn(`${LogPrefix.WEBHOOK} 签名生成失败，使用未签名 URL: ${error.message}`);
        return webhookUrl;
    }
}

/**
 * 发送 webhook 卡片消息
 * @param {string} title
 * @param {string} content - markdown 内容
 * @returns {Promise<boolean>}
 */
export async function sendWebhookMessage(title, content) {
    if (!BotConfig.webhookUrl) {
        console.warn(`${LogPrefix.WEBHOOK} 未配置 webhook URL，跳过通知`);
        return false;
    }

    const body = {
        msg_type: 'interactive',
        card: {
            header: {
                title: { tag: 'plain_text', content: title },
                template: 'red',
            },
            elements: [{ tag: 'markdown', content }],
        },
    };

    const url = signWebhookUrl(BotConfig.webhookSecret);

    for (let attempt = 0; attempt <= RETRIES; attempt++) {
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // 全局 dispatcher 已放开响应超时，这里对单次请求设 30s 上限防挂死
                signal: AbortSignal.timeout(30000),
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                console.error(`${LogPrefix.WEBHOOK} HTTP ${res.status}: ${await res.text()}`);
                if (res.status >= 500 && attempt < RETRIES) {
                    await new Promise((r) => setTimeout(r, RETRY_BASE_DELAY * 2 ** attempt));
                    continue;
                }
                return false;
            }

            const result = await res.json();
            if (result?.code !== 0) {
                console.error(`${LogPrefix.WEBHOOK} API 错误: ${result?.msg}`);
                return false;
            }
            return true;
        } catch (error) {
            console.error(`${LogPrefix.WEBHOOK} 发送异常: ${error.message}`);
            if (attempt < RETRIES) {
                await new Promise((r) => setTimeout(r, RETRY_BASE_DELAY * 2 ** attempt));
                continue;
            }
            return false;
        }
    }
    return false;
}

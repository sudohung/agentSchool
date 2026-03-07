/**
 * Webhook 消息发送模块
 */

import crypto from 'crypto';
import { FeishuConfig } from '../config.js';

/**
 * 发送 webhook 消息
 * @param {string} title - 消息标题（interactive card 时使用；text 时会被忽略）
 * @param {string} content - 消息内容
 * @param {object} [options] - 可选项
 * @param {'interactive'|'text'} [options.type='interactive'] - 消息类型
 * @param {number} [options.retries=2] - 失败重试次数（网络/5xx）
 * @returns {Promise<boolean>} 发送是否成功
 */
export async function sendWebhookMessage(title, content, options = {}) {
    const { type = 'interactive', retries = 2 } = options;
    let webhookUrl = FeishuConfig.webhookUrl;
    const secret = FeishuConfig.webhookSecret;

    if (!webhookUrl) {
        console.error('[Webhook] 未配置 webhook URL');
        return false;
    }

    // 如果配置了 secret，则为 webhook 添加签名（timestamp + sign）
    if (secret) {
        try {
            const timestamp = Date.now().toString();
            const stringToSign = `${timestamp}\n${secret}`;
            const hmac = crypto.createHmac('sha256', secret);
            hmac.update(stringToSign);
            const sign = hmac.digest('base64');

            const separator = webhookUrl.includes('?') ? '&' : '?';
            webhookUrl = `${webhookUrl}${separator}timestamp=${encodeURIComponent(timestamp)}&sign=${encodeURIComponent(sign)}`;
        } catch (err) {
            console.warn('[Webhook] 生成签名失败，将使用未签名 URL：', err && err.message);
        }
    }

    // Ensure fetch exists (Node.js older versions may not have global fetch)
    if (typeof fetch === 'undefined') {
        try {
            const nodeFetch = await import('node-fetch');
            globalThis.fetch = nodeFetch.default;
        } catch (err) {
            console.warn('[Webhook] fetch 未定义，且无法加载 node-fetch：', err && err.message);
            // proceed and let the later fetch call fail with a clear error
        }
    }

    // Build request body depending on message type
    const buildBody = () => {
        if (type === 'text') {
            return {
                msg_type: 'text',
                content: {
                    text: content
                }
            };
        }

        // interactive card (default). Keep the previous structure for compatibility.
        return {
            msg_type: 'interactive',
            card: {
                header: {
                    title: {
                        tag: 'plain_text',
                        content: title
                    },
                    template: 'red'
                },
                elements: [
                    {
                        tag: 'markdown',
                        content: content
                    }
                ]
            }
        };
    };

    const body = buildBody();

    // Simple retry loop with exponential backoff for transient errors
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const response = await fetch(webhookUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[Webhook] 发送失败 (HTTP ${response.status}):`, errorText);
                // Retry on 5xx status
                if (response.status >= 500 && attempt < retries) {
                    const waitMs = Math.pow(2, attempt) * 500;
                    await new Promise((res) => setTimeout(res, waitMs));
                    continue;
                }
                return false;
            }

            const result = await response.json();
            // Feishu 返回 { code: 0, msg: 'ok', ... }
            if (result && result.code !== 0) {
                console.error('[Webhook] API 错误:', result.msg || result);
                return false;
            }

            return true;
        } catch (error) {
            console.error('[Webhook] 发送异常:', error && error.message);
            // Retry on network errors
            if (attempt < retries) {
                const waitMs = Math.pow(2, attempt) * 500;
                await new Promise((res) => setTimeout(res, waitMs));
                continue;
            }
            return false;
        }
    }

    return false;
}

/**
 * 发送事件通知
 * @param {string} eventType - 事件类型
 * @param {string} eventDescription - 事件描述
 */
export async function sendEventNotification(eventType, eventDescription) {
    return await sendWebhookMessage(`📢 ${eventType}`, eventDescription);
}

/**
 * 发送错误消息
 * @param {string} errorMessage - 错误信息
 * @param {string} prefix - 错误前缀
 */
export async function sendErrorMessage(errorMessage, prefix = '❌ 发生错误') {
    return await sendWebhookMessage(prefix, `错误：${errorMessage}`);
}

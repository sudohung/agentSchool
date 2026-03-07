/**
 * Webhook 消息发送模块
 */

import { FeishuConfig } from '../config.js';

/**
 * 发送 webhook 消息
 * @param {string} title - 消息标题
 * @param {string} content - 消息内容
 * @returns {Promise<boolean>} 发送是否成功
 */
export async function sendWebhookMessage(title, content) {
    const webhookUrl = FeishuConfig.webhookUrl;
    
    if (!webhookUrl) {
        console.error('[Webhook] 未配置 webhook URL');
        return false;
    }

    try {
        const response = await fetch(webhookUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
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
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Webhook] 发送失败:', response.status, errorText);
            return false;
        }

        const result = await response.json();
        if (result.code !== 0) {
            console.error('[Webhook] API 错误:', result.msg);
            return false;
        }

        console.log('[Webhook] 消息发送成功:', title);
        return true;
    } catch (error) {
        console.error('[Webhook] 发送异常:', error.message);
        return false;
    }
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

/**
 * 飞书消息通知插件
 * 监听 OpenCode 事件并发送消息到 Webhook
 */

import { FeishuConfig } from './config.js';
import { createEventHandlerChain } from './handlers/index.js';

// 验证配置
if (!FeishuConfig.isValid()) {
    console.error('[FeishuBot] 缺少必要的环境变量配置：FEISHU_WEBHOOK_URL');
    throw new Error('Webhook 配置不完整');
}

/**
 * opencode 的 飞书插件主函数
 * @param {Object} context - 插件上下文
 * @param {Object} context.project - 项目信息
 */
export const OpencodeFeishuPlugin = async (context) => {
    const { project } = context;

    console.log('[FeishuBot] 插件已启动');

    const eventChain = createEventHandlerChain(project);

    /**
     * 监听所有opencode事件
     */
    return {
        /**
         * 监听所有事件
         */
        event: async ({ event }) => {
            await eventChain.handle(event, { project });
        },

        /**
         * 监听消息更新事件
         */
        "message.updated": async (input, output) => {
        },

        /**
         * 监听文件编辑事件
         */
        "file.edited": async (input, output) => {
        }
    };
};

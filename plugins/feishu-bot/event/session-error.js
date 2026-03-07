import { EventHandler } from './handler.js';

export class SessionErrorHandler extends EventHandler {
    constructor() {
        super('session.error');
    }

    async process(event, context) {
        const sessionID = event.properties?.sessionID || '未知会话';
        const errorMessage = event.properties?.errorMessage || event.error?.message || '未知错误';
        const timestamp = new Date().toLocaleString('zh-CN');

        // 优先使用 context 中的 notifyWebhook，如果没有则使用默认的 sendErrorMessage
        if (context?.notifyWebhook) {
            return await context.notifyWebhook(
                `❌ 会话异常：${sessionID}`,
                `会话 ${sessionID} 发生异常\n错误信息：${errorMessage}\n时间：${timestamp}`
            );
        }

        // 降级处理：直接导入 sendErrorMessage（需要确保该函数存在）
        const { sendErrorMessage } = await import('../webhook/index.js');
        return await sendErrorMessage(
            `会话 ${sessionID} 发生异常，错误信息：${errorMessage}`,
            "❌ 发生错误"
        );
    }
}

/**
 * 飞书消息模块入口文件
 * 导出所有消息相关的功能
 */

export {
    createFeishuClient,
    sendTextMessage,
    sendCardMessage,
    sendThinkingMessage,
    sendErrorMessage,
    sendAIResponse,
    sendEventNotification,
    sendEmptyResponse,
    updateMessage
} from './feishu-message-sender.js';

import { EventHandler } from './handler.js';
import { sendWebhookMessage } from '../webhook/index.js';

/**
 * 状态处理策略接口
 */
class StatusStrategy {
    /**
     * 判断是否支持该状态类型
     * @param {string} statusType - 状态类型
     * @returns {boolean}
     */
    supports(statusType) {
        throw new Error('supports method must be implemented');
    }

    /**
     * 处理状态
     * @param {object} status - 状态对象
     * @param {object} event - 原始事件
     * @returns {Promise<boolean>} 处理结果
     */
    async handle(status, event) {
        throw new Error('handle method must be implemented');
    }
}

/**
 * 重试状态处理策略（attempt=1 时通知）
 */
class RetryFirstAttemptStrategy extends StatusStrategy {
    supports(statusType) {
        return statusType === 'retry';
    }

    async handle(status, event, context) {
        // 仅在第一次重试时发送通知
        if (status.attempt !== 1) {
            return false;
        }

        const sessionID = event.properties?.sessionID || '未知会话';
        const message = status.message || '未知错误';
        const nextRetryTime = status.next ? new Date(status.next).toLocaleString() : '未知';

        const content =
`会话 ID: ${sessionID}
状态：重试中
重试次数：${status.attempt}
错误信息：${message}
下次重试时间：${nextRetryTime}`;
        
        // 优先使用 context 中的 notify（发送文本消息到聊天）
        if (context?.notify) {
            return await context.notify('⚠️ 会话重试通知', content);
        }
        
        // 其次使用 notifyWebhook（发送 webhook 消息）
        if (context?.notifyWebhook) {
            return await context.notifyWebhook('⚠️ 会话重试通知A', content);
        }
        
        // 降级处理：动态导入 sendWebhookMessage
        const { sendWebhookMessage } = await import('../webhook/index.js');
        return await sendWebhookMessage(
            '⚠️ 会话重试通知',
            content,
            { type: 'interactive' }
        );
    }
}

/**
 * 策略管理器
 */
class StatusStrategyManager {
    constructor() {
        this.strategies = [];
        this.registerDefaultStrategies();
    }

    /**
     * 注册默认策略
     */
    registerDefaultStrategies() {
        this.register(new RetryFirstAttemptStrategy());
    }

    /**
     * 注册策略
     * @param {StatusStrategy} strategy - 策略实例
     */
    register(strategy) {
        this.strategies.push(strategy);
    }

    /**
     * 查找并执行匹配的策略
     * @param {string} statusType - 状态类型
     * @param {object} status - 状态对象
     * @param {object} event - 原始事件
     * @param {object} context - 上下文（包含 notify 等回调）
     * @returns {Promise<boolean>} 处理结果
     */
    async execute(statusType, status, event, context) {
        for (const strategy of this.strategies) {
            if (strategy.supports(statusType)) {
                return await strategy.handle(status, event, context);
            }
        }
        console.log(`[SessionStatusHandler] 未找到匹配的状态处理器：${statusType}`);
        return null;
    }
}

// 创建全局策略管理器实例
const strategyManager = new StatusStrategyManager();

/**
 * 会话状态处理器（使用策略模式）
 * 处理 session.status 事件，根据不同类型的 status 采用不同的处理策略
 */
export class SessionStatusHandler extends EventHandler {
    constructor() {
        super('session.status');
        this.strategyManager = strategyManager;
    }

    async process(event, context) {
        const status = event.properties?.status;
        
        if (!status || !status.type) {
            return null;
        }

        // 使用策略模式处理不同状态，传递 context 以便策略可以使用 notify 回调
        return await this.strategyManager.execute(status.type, status, event, context);
    }
}

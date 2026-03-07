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

    async handle(status, event) {
        // 仅在第一次重试时发送通知
        if (status.attempt !== 1) {
            return false;
        }

        const sessionID = event.properties?.sessionID || '未知会话';
        const message = status.message || '未知错误';
        const nextRetryTime = status.next ? new Date(status.next).toLocaleString() : '未知';

        const content = `**会话 ID**: ${sessionID}
                            **状态**: 重试中
                            **重试次数**: ${status.attempt}
                            **错误信息**: ${message}
                            **下次重试时间**: ${nextRetryTime}`;
        
        return await sendWebhookMessage(
            '⚠️ 会话重试通知',
            content,
            { type: 'interactive' }
        );
    }
}

/**
 * 重试状态处理策略（所有重试都通知）
 */
class RetryAllAttemptsStrategy extends StatusStrategy {
    supports(statusType) {
        return statusType === 'retry_all';
    }

    async handle(status, event) {
        const sessionID = event.properties?.sessionID || '未知会话';
        const message = status.message || '未知错误';
        const nextRetryTime = status.next ? new Date(status.next).toLocaleString() : '未知';

        const content = `**会话 ID**: ${sessionID}\n**状态**: 重试中（第${status.attempt}次）\n**错误信息**: ${message}\n**下次重试时间**: ${nextRetryTime}`;
        
        return await sendWebhookMessage(
            '🔄 会话重试通知',
            content,
            { type: 'interactive' }
        );
    }
}

/**
 * 完成状态处理策略
 */
class CompletedStrategy extends StatusStrategy {
    supports(statusType) {
        return statusType === 'completed';
    }

    async handle(status, event) {
        const sessionID = event.properties?.sessionID || '未知会话';
        
        const content = `**会话 ID**: ${sessionID}\n**状态**: 已完成`;
        
        return await sendWebhookMessage(
            '✅ 会话完成通知',
            content,
            { type: 'interactive' }
        );
    }
}

/**
 * 失败状态处理策略
 */
class FailedStrategy extends StatusStrategy {
    supports(statusType) {
        return statusType === 'failed';
    }

    async handle(status, event) {
        const sessionID = event.properties?.sessionID || '未知会话';
        const message = status.message || '未知错误';

        const content = `**会话 ID**: ${sessionID}\n**状态**: 失败\n**错误信息**: ${message}`;
        
        return await sendWebhookMessage(
            '❌ 会话失败通知',
            content,
            { type: 'interactive' }
        );
    }
}

/**
 * 超时状态处理策略
 */
class TimeoutStrategy extends StatusStrategy {
    supports(statusType) {
        return statusType === 'timeout';
    }

    async handle(status, event) {
        const sessionID = event.properties?.sessionID || '未知会话';
        const message = status.message || '会话超时';

        const content = `**会话 ID**: ${sessionID}\n**状态**: 超时\n**错误信息**: ${message}`;
        
        return await sendWebhookMessage(
            '⏰ 会话超时通知',
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
        this.register(new RetryAllAttemptsStrategy());
        this.register(new CompletedStrategy());
        this.register(new FailedStrategy());
        this.register(new TimeoutStrategy());
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
     * @returns {Promise<boolean>} 处理结果
     */
    async execute(statusType, status, event) {
        for (const strategy of this.strategies) {
            if (strategy.supports(statusType)) {
                return await strategy.handle(status, event);
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

        // 使用策略模式处理不同状态
        return await this.strategyManager.execute(status.type, status, event);
    }
}

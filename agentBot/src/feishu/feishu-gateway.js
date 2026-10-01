/**
 * 飞书 WebSocket 长连接网关
 * 职责：建立长连接、消息去重、过期消息丢弃、触发回调
 */

import * as lark from '@larksuiteoapi/node-sdk';
import { LogPrefix } from '../constants.js';

/**
 * 飞书长连接网关类
 */
export class FeishuGateway {
    /** @type {lark.WSClient|null} */
    #wsClient = null;
    /** @type {boolean} */
    #connected = false;
    /** @type {NodeJS.Timeout|null} 全量重启防抖定时器 */
    #restartTimer = null;
    /** @type {(chatId: string, text: string, messageContext: Object) => Promise<void>|null} */
    #onMessage = null;
    /** @type {Set<string>} 已处理消息 ID */
    #processedIds = new Set();
    /** @type {Map<string, number>} 消息 ID -> 处理时间戳 */
    #processedTimestamps = new Map();

    /**
     * @param {{appId:string, appSecret:string, messageTtl:number, expiryTime:number, logLevel?:string}} config
     */
    constructor(config) {
        if (!config?.appId || !config?.appSecret) {
            throw new Error('FeishuGateway 配置不完整：缺少 appId/appSecret');
        }
        this.#config = {
            appId: config.appId,
            appSecret: config.appSecret,
            messageTtl: config.messageTtl || 3600000,
            expiryTime: config.expiryTime || 120000,
            logLevel: config.logLevel || 'info',
        };
    }

    #config;

    /**
     * 清理过期去重记录
     */
    #cleanupExpired(now) {
        for (const [id, ts] of this.#processedTimestamps.entries()) {
            if (now - ts > this.#config.messageTtl) {
                this.#processedIds.delete(id);
                this.#processedTimestamps.delete(id);
            }
        }
    }

    /**
     * 判断消息是否应跳过（过旧或重复）
     */
    #shouldSkip(messageId, messageTime) {
        const now = Date.now();
        if (Number.isFinite(messageTime) && now - messageTime > this.#config.expiryTime) {
            console.log(`${LogPrefix.GATEWAY} 消息过旧，跳过：${messageId}`);
            return true;
        }
        if (this.#processedIds.has(messageId)) {
            return true;
        }
        this.#processedIds.add(messageId);
        this.#processedTimestamps.set(messageId, now);
        if (this.#processedIds.size % 20 === 0) {
            this.#cleanupExpired(now);
        }
        return false;
    }

    /**
     * 启动长连接并注册消息/卡片交互事件
     * @param {(chatId: string, text: string, messageContext: Object) => Promise<void>} onMessage
     * @param {(data: Object) => Promise<Object|null>} [onCardAction] - 卡片按钮回调，返回卡片 JSON 将原地更新卡片
     */
    start(onMessage, onCardAction) {
        if (this.#connected) {
            console.warn(`${LogPrefix.GATEWAY} 长连接已启动，忽略重复启动`);
            return;
        }

        // onMessage 需在重建连接时复用，保存引用
        this.#onMessage = onMessage;

        this.#wsClient = new lark.WSClient({
            appId: this.#config.appId,
            appSecret: this.#config.appSecret,
            loggerLevel: this.#config.logLevel === 'debug'
                ? lark.LoggerLevel.debug
                : this.#config.logLevel === 'error'
                    ? lark.LoggerLevel.error
                    : lark.LoggerLevel.info,
            // 看门狗：ping 后超过该秒数无任何服务端消息即判定连接死亡并重连。
            // 切换网络时旧 TCP 呈僵尸状态（无 FIN/RST），没有看门狗会永远"假活"
            wsConfig: { pingTimeout: 30 },
            // 握手超时：切网后 DNS/代理路径变化可能让握手无限悬挂
            handshakeTimeoutMs: 15000,
            onReady: () => {
                this.#connected = true;
                console.log(`${LogPrefix.GATEWAY} 飞书长连接已就绪`);
            },
            onReconnecting: () => {
                this.#connected = false;
                console.warn(`${LogPrefix.GATEWAY} 飞书长连接断开，进入重连...`);
            },
            onReconnected: () => {
                this.#connected = true;
                console.log(`${LogPrefix.GATEWAY} 飞书长连接已恢复`);
            },
            // 重连次数耗尽进入 terminal failed 后，全量重建客户端自愈
            onError: (err) => {
                this.#connected = false;
                console.error(`${LogPrefix.GATEWAY} 飞书长连接最终失败: ${err?.message || err}，30s 后重建连接`);
                this.#scheduleRestart();
            },
        });

        const handles = {
            'im.message.receive_v1': async (data) => {
                try {
                    const { chat_id, message_id, create_time, content } = data.message || {};
                    if (!chat_id || !message_id) {
                        console.warn(`${LogPrefix.GATEWAY} 消息缺少 chat_id/message_id，忽略`);
                        return {};
                    }

                    const messageTime = typeof create_time === 'string'
                        ? parseInt(create_time, 10)
                        : create_time;
                    if (this.#shouldSkip(message_id, messageTime)) {
                        return {};
                    }

                    // 仅处理文本消息，其他类型（图片/文件等）提示不支持
                    let text = '';
                    try {
                        text = JSON.parse(content)?.text || '';
                    } catch {
                        text = '';
                    }
                    if (!text) {
                        console.log(`${LogPrefix.GATEWAY} 非文本消息，跳过：${message_id}`);
                        return {};
                    }

                    await this.#onMessage(chat_id, text, data.message);
                } catch (error) {
                    console.error(`${LogPrefix.GATEWAY} 消息处理异常: ${error.message}`);
                }
                return {};
            },
        };

        // 卡片按钮回调：长连接模式接收 card.action.trigger，返回值作为回执卡片原地更新
        if (typeof onCardAction === 'function') {
            handles['card.action.trigger'] = async (data) => {
                try {
                    console.log(`${LogPrefix.GATEWAY} 收到卡片按钮回调: ${JSON.stringify(data)?.slice(0, 500)}`);
                    const result = (await onCardAction(data)) || {};
                    console.log(`${LogPrefix.GATEWAY} 卡片回调处理完成，返回回执: ${result?.header ? result.header.title?.content : JSON.stringify(result).slice(0, 200)}`);
                    return result;
                } catch (error) {
                    console.error(`${LogPrefix.GATEWAY} 卡片交互处理异常: ${error.message}`, error.stack);
                    return {};
                }
            };
        }

        this.#wsClient.start({
            eventDispatcher: new lark.EventDispatcher({}).register(handles),
        });

        this.#connected = true;
        console.log(`${LogPrefix.GATEWAY} 飞书长连接已启动`);
    }

    /**
     * 延迟全量重建连接（关闭旧客户端后重新 start），带防抖
     */
    #scheduleRestart() {
        if (this.#restartTimer) return;
        this.#restartTimer = setTimeout(() => {
            this.#restartTimer = null;
            this.#connected = false;
            try {
                this.#wsClient?.close?.();
            } catch (error) {
                console.warn(`${LogPrefix.GATEWAY} 关闭旧连接失败（忽略）: ${error.message}`);
            }
            this.#wsClient = null;
            try {
                this.start(this.#onMessage);
            } catch (error) {
                console.error(`${LogPrefix.GATEWAY} 重建连接失败: ${error.message}，将继续重试`);
                this.#scheduleRestart();
            }
        }, 30000);
    }

    /**
     * 查询连接状态（供配置页/诊断使用）
     * @returns {{state:string, reconnectAttempts:number}|null}
     */
    getConnectionStatus() {
        try {
            const s = this.#wsClient?.getConnectionStatus?.();
            return s ? { state: s.state, reconnectAttempts: s.reconnectAttempts } : null;
        } catch {
            return null;
        }
    }

    isConnected() {
        return this.#connected;
    }
}

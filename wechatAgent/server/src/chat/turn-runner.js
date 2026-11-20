/**
 * 一轮问答的执行器
 *
 * 职责：
 *  1. 保证业务会话与 OpenCode 会话的映射（懒创建）
 *  2. 先订阅事件总线、再发 prompt，避免漏掉开头 delta
 *  3. 把事件写成 NDJSON 帧刷给小程序（chunked）
 *  4. 落库用户消息与助手消息
 *  5. 客户端断开/用户点停止时中断引擎生成
 */

import { FrameType, MessageRole, MessageStatus, TurnStatus, LogPrefix, ErrorCode } from '../constants.js';

/** 心跳间隔下限：太短浪费带宽，太长会被中间层判定僵死 */
const MIN_PING_MS = 8000;

export class TurnRunner {
    /** @type {import('../store/chat-store.js').ChatStore} */
    #store;
    /** @type {import('../opencode/engine-registry.js').EngineRegistry} */
    #engines;
    /** @type {Object} */
    #config;
    /** @type {Map<string, {abort:Function}>} 业务会话 id -> 进行中的轮次 */
    #active = new Map();

    constructor({ store, engines, config }) {
        this.#store = store;
        this.#engines = engines;
        this.#config = config;
    }

    /**
     * 会话是否有进行中的轮次
     * @param {string} sessionId
     */
    isBusy(sessionId) {
        return this.#active.has(sessionId);
    }

    /**
     * 中断进行中的轮次
     * @param {string} sessionId
     */
    async abort(sessionId) {
        const active = this.#active.get(sessionId);
        if (!active) return false;
        await active.abort();
        return true;
    }

    /**
     * 执行一轮问答，结果以 NDJSON 帧写入 res
     * @param {Object} input
     * @param {Object} input.session       业务会话
     * @param {string} input.text          用户提问
     * @param {{providerID:string,modelID:string}|null} input.model
     * @param {import('http').ServerResponse} input.res
     */
    async run({ session, text, model, res }) {
        const sessionId = session.id;
        if (this.#active.has(sessionId)) {
            throw Object.assign(new Error('该会话正在生成中，请先停止'), {
                status: 409,
                code: ErrorCode.CONFLICT,
            });
        }

        const runtime = this.#engines.get(session.engine);
        const opencodeSessionId = await this.#ensureOpencodeSession(session, runtime, model);

        // 先落库，保证即使流式中途失败，历史里也有完整上下文
        this.#store.appendMessage(sessionId, { role: MessageRole.USER, content: text });
        const assistant = this.#store.appendMessage(sessionId, {
            role: MessageRole.ASSISTANT,
            content: '',
            status: MessageStatus.STREAMING,
        });
        const isDefaultTitle = !session.title || session.title === '新的对话';
        this.#store.updateSession(sessionId, isDefaultTitle ? { title: text.slice(0, 20) } : {});

        const writer = new FrameWriter(res);
        const turn = this.#createTurn({
            sessionId,
            opencodeSessionId,
            runtime,
            writer,
            assistantId: assistant.id,
        });

        this.#active.set(sessionId, { abort: turn.abort });
        // 客户端主动断开（小程序退出/网络断）时停止生成，避免引擎白跑
        const onClientClose = () => {
            if (!writer.closed) turn.abort().catch(() => {});
        };
        res.on('close', onClientClose);

        writer.write({
            t: FrameType.START,
            sessionId,
            messageId: assistant.id,
            engine: session.engine,
        });
        writer.startPing(Math.min(this.#config.chat.heartbeatMs, MIN_PING_MS));

        try {
            await turn.execute(text);
        } finally {
            res.off('close', onClientClose);
            this.#active.delete(sessionId);
            writer.close();
            this.#store.flush();
        }
    }

    /**
     * 构造一轮的执行上下文
     */
    #createTurn({ sessionId, opencodeSessionId, runtime, writer, assistantId }) {
        const store = this.#store;
        const config = this.#config;
        let content = '';
        let reasoning = '';
        let promptAccepted = false;
        let finished = false;
        /** 用户主动停止：引擎随后会回 Aborted 错误，需归为 aborted 而非 error */
        let aborting = false;

        /**
         * 收尾：落库 + 下发终态帧（幂等）
         * @param {string} status
         * @param {string} [errorMessage]
         */
        const settle = (status, errorMessage) => {
            if (finished) return;
            finished = true;
            // 停止过程中引擎回的错误一律按「已停止」处理
            const finalStatus = aborting && status === TurnStatus.ERROR ? TurnStatus.ABORTED : status;
            const finalMessage = finalStatus === TurnStatus.ABORTED ? '已停止生成' : errorMessage;
            const messageStatus = {
                [TurnStatus.DONE]: MessageStatus.DONE,
                [TurnStatus.ABORTED]: MessageStatus.ABORTED,
            }[finalStatus] || MessageStatus.ERROR;

            store.patchMessage(sessionId, assistantId, { content, reasoning, status: messageStatus }, true);
            writer.write({
                t: FrameType.DONE,
                status: finalStatus,
                messageId: assistantId,
                ...(finalStatus === TurnStatus.DONE ? {} : { error: finalMessage || '生成失败' }),
            });
        };

        const unsubscribe = runtime.bus.subscribeSession(opencodeSessionId, (event) => {
            if (finished) return;
            switch (event.kind) {
                case 'text':
                    // prompt 返回前的历史事件（如上一轮残留）不采用
                    if (!promptAccepted) return;
                    content += event.delta;
                    writer.write({ t: FrameType.DELTA, text: event.delta });
                    store.patchMessage(sessionId, assistantId, { content, reasoning });
                    break;
                case 'reasoning':
                    if (!promptAccepted) return;
                    reasoning += event.delta;
                    writer.write({ t: FrameType.REASONING, text: event.delta });
                    break;
                case 'tool':
                    if (!promptAccepted) return;
                    writer.write({ t: FrameType.TOOL, tool: event.tool, status: event.status, title: event.title });
                    break;
                case 'question':
                    writer.write({ t: FrameType.QUESTION, id: event.id, questions: event.questions });
                    break;
                case 'questionClosed':
                    writer.write({ t: FrameType.QUESTION, id: event.id, questions: [], closed: true });
                    break;
                case 'permission':
                    writer.write({ t: FrameType.PERMISSION, id: event.id, action: event.action });
                    break;
                case 'error':
                    settle(TurnStatus.ERROR, event.message);
                    break;
                case 'idle':
                    if (!promptAccepted) return;
                    settle(TurnStatus.DONE);
                    break;
                default:
                    break;
            }
        });

        let timer = null;

        /** 中断：先告诉引擎停，再落库收尾 */
        const abort = async () => {
            if (finished || aborting) return;
            aborting = true;
            await runtime.client.abort(opencodeSessionId).catch(() => {});
            settle(TurnStatus.ABORTED, '已停止生成');
        };

        /** 真正执行 */
        const execute = async (text) => {
            timer = setTimeout(() => {
                settle(TurnStatus.TIMEOUT, `生成超时（${Math.round(config.chat.turnTimeoutMs / 1000)} 秒）`);
                runtime.client.abort(opencodeSessionId).catch(() => {});
            }, config.chat.turnTimeoutMs);

            try {
                await runtime.client.promptAsync(opencodeSessionId, text, {
                    system: config.chat.systemPrompt,
                });
                promptAccepted = true;
                // 本轮由事件流驱动结束，这里阻塞到 settle
                await waitUntil(() => finished, config.chat.turnTimeoutMs);
                if (!finished) settle(TurnStatus.ERROR, '等待引擎响应超时');
            } catch (error) {
                settle(TurnStatus.ERROR, error.message);
            } finally {
                if (timer) clearTimeout(timer);
                unsubscribe();
            }
        };

        return { execute, abort };
    }

    /**
     * 确保 OpenCode 会话存在（首次提问时创建）
     * @param {Object} session
     * @param {{client: import('../opencode/client.js').OpencodeClient}} runtime
     * @param {{providerID:string,modelID:string}|null} model
     */
    async #ensureOpencodeSession(session, runtime, model) {
        if (session.opencodeSessionId) return session.opencodeSessionId;
        const created = await runtime.client.createSession({ title: session.title, model });
        this.#store.updateSession(session.id, { opencodeSessionId: created });
        console.log(`${LogPrefix.CHAT} 会话映射建立 ${session.id} -> ${created}`);
        return created;
    }
}

/**
 * NDJSON 帧写入器
 * 关键点：只 writeHead + write，不设 Content-Length，Node 自动走 chunked，
 *         小程序 enableChunked 才能逐块收到。
 */
class FrameWriter {
    /** @type {import('http').ServerResponse} */
    #res;
    /** @type {NodeJS.Timeout|null} */
    #pingTimer = null;
    /** @type {boolean} */
    #closed = false;

    constructor(res) {
        this.#res = res;
        res.writeHead(200, {
            'Content-Type': 'application/x-ndjson; charset=utf-8',
            'Cache-Control': 'no-cache, no-transform',
            Connection: 'keep-alive',
            // 显式关闭 Nginx 等反向代理的缓冲
            'X-Accel-Buffering': 'no',
        });
        res.socket?.setNoDelay?.(true);
    }

    /** 是否已关闭 */
    get closed() {
        return this.#closed;
    }

    /**
     * 写一帧
     * @param {Object} frame
     */
    write(frame) {
        if (this.#closed || this.#res.writableEnded) return;
        try {
            this.#res.write(`${JSON.stringify(frame)}\n`);
        } catch {
            this.#closed = true;
        }
    }

    /** 启动心跳 */
    startPing(intervalMs) {
        if (this.#pingTimer) return;
        this.#pingTimer = setInterval(() => this.write({ t: FrameType.PING, ts: Date.now() }), intervalMs);
        this.#pingTimer.unref?.();
    }

    /** 停止心跳 */
    stopPing() {
        if (this.#pingTimer) clearInterval(this.#pingTimer);
        this.#pingTimer = null;
    }

    /** 结束响应 */
    close() {
        this.stopPing();
        if (this.#closed || this.#res.writableEnded) return;
        this.#closed = true;
        try {
            this.#res.end();
        } catch {
            // 客户端已断开，忽略
        }
    }
}

/**
 * 轮询等待条件成立
 * @param {()=>boolean} predicate
 * @param {number} timeoutMs
 */
function waitUntil(predicate, timeoutMs) {
    return new Promise((resolve) => {
        const started = Date.now();
        const timer = setInterval(() => {
            if (predicate() || Date.now() - started > timeoutMs) {
                clearInterval(timer);
                resolve();
            }
        }, 150);
        timer.unref?.();
    });
}
/**
 * 流式对话客户端
 *
 * 关键实现点：
 *  1. wx.request 必须显式 enableChunked: true（基础库 >= 2.20.2）
 *  2. onChunkReceived 必须在 wx.request 返回后立刻挂载，不能等到 success
 *  3. 服务端返回 NDJSON（一行一帧），这里做跨 chunk 的半行拼接
 *  4. enableChunked 没有「结束」事件，靠协议里的 done 帧判定结束
 */

const config = require('../config');
const storage = require('./storage');

/** 帧类型（与后端 FrameType 对齐） */
const Frame = {
    START: 'start',
    DELTA: 'delta',
    REASONING: 'reasoning',
    TOOL: 'tool',
    QUESTION: 'question',
    PERMISSION: 'permission',
    DONE: 'done',
    ERROR: 'error',
    PING: 'ping',
};

/**
 * 增量 UTF-8 解码器
 * chunk 边界可能把一个中文字符的 3 个字节切开，必须保留尾部不完整字节到下一次
 */
function createDecoder() {
    /** @type {number[]} 上一块遗留的不完整字节 */
    let pending = [];

    /**
     * 判断从 index 开始是否构成一个完整 UTF-8 字符
     * @param {Uint8Array} bytes
     * @param {number} index
     * @returns {number} 需要的字节数（1~4），不足时返回 0
     */
    const charLength = (bytes, index) => {
        const byte = bytes[index];
        if (byte < 0x80) return 1;
        if (byte >= 0xc0 && byte < 0xe0) return 2;
        if (byte >= 0xe0 && byte < 0xf0) return 3;
        if (byte >= 0xf0 && byte < 0xf8) return 4;
        return 1; // 非法起始字节，按单字节吞掉，避免死循环
    };

    /**
     * 解码一段完整字节
     * @param {Uint8Array} bytes
     * @returns {string}
     */
    const decodeAll = (bytes) => {
        let result = '';
        let i = 0;
        while (i < bytes.length) {
            const need = charLength(bytes, i);
            if (i + need > bytes.length) break;
            const byte = bytes[i];

            if (need === 1) {
                result += String.fromCharCode(byte);
            } else if (need === 2) {
                result += String.fromCharCode(((byte & 0x1f) << 6) | (bytes[i + 1] & 0x3f));
            } else if (need === 3) {
                result += String.fromCharCode(
                    ((byte & 0x0f) << 12) | ((bytes[i + 1] & 0x3f) << 6) | (bytes[i + 2] & 0x3f)
                );
            } else {
                let codePoint =
                    ((byte & 0x07) << 18) |
                    ((bytes[i + 1] & 0x3f) << 12) |
                    ((bytes[i + 2] & 0x3f) << 6) |
                    (bytes[i + 3] & 0x3f);
                codePoint -= 0x10000;
                result += String.fromCharCode(0xd800 + (codePoint >> 10), 0xdc00 + (codePoint & 0x3ff));
            }
            i += need;
        }
        // 剩余不完整字节留到下一块
        pending = Array.from(bytes.slice(i));
        return result;
    };

    return {
        /**
         * 输入一块数据，返回可解码的文本
         * @param {ArrayBuffer} buffer
         * @returns {string}
         */
        push(buffer) {
            const incoming = new Uint8Array(buffer);
            const bytes = pending.length
                ? Uint8Array.from([...pending, ...incoming])
                : incoming;
            pending = [];
            return decodeAll(bytes);
        },
        /** 冲刷残留字节（流结束时调用） */
        flush() {
            if (!pending.length) return '';
            const rest = Uint8Array.from(pending);
            pending = [];
            return decodeAll(rest);
        },
    };
}

/**
 * 从一次性响应体里取出文本（兼容 arraybuffer / string / 空）
 * @param {ArrayBuffer|string|null} data
 * @returns {string}
 */
function extractWholeBody(data) {
    if (!data) return '';
    if (typeof data === 'string') return data;
    try {
        return createDecoder().push(data);
    } catch (e) {
        return '';
    }
}

/**
 * 发起一轮流式对话
 * @param {Object} options
 * @param {string} options.sessionId
 * @param {string} options.text
 * @param {(frame:Object)=>void} options.onFrame
 * @param {(error:Error)=>void} [options.onError]
 * @param {()=>void} [options.onComplete]
 * @returns {{abort:Function}} 控制句柄
 */
function streamChat({ sessionId, text, onFrame, onError, onComplete }) {
    const token = storage.get(storage.KEYS.TOKEN);
    const decoder = createDecoder();
    let task = null;
    let finished = false;
    let buffer = '';
    let idleTimer = null;

    const clearIdle = () => {
        if (idleTimer) clearTimeout(idleTimer);
        idleTimer = null;
    };

    /** 重置空闲超时：长时间无帧视为断线 */
    const resetIdle = () => {
        clearIdle();
        idleTimer = setTimeout(() => {
            if (finished) return;
            finished = true;
            try {
                task && task.abort();
            } catch (e) {
                // ignore
            }
            onError && onError(new Error('连接超时，未收到响应'));
        }, config.STREAM_IDLE_TIMEOUT);
    };

    /** 处理一行帧 */
    const handleLine = (line) => {
        const trimmed = line.trim();
        if (!trimmed) return;
        let frame;
        try {
            frame = JSON.parse(trimmed);
        } catch (e) {
            return;
        }
        if (frame.t === Frame.PING) return;

        onFrame && onFrame(frame);

        if (frame.t === Frame.DONE) {
            finished = true;
            clearIdle();
            onComplete && onComplete(frame);
        }
    };

    resetIdle();

    task = wx.request({
        url: `${config.BASE_URL}/api/sessions/${sessionId}/messages`,
        method: 'POST',
        header: {
            'Content-Type': 'application/json',
            Authorization: token ? `Bearer ${token}` : '',
        },
        data: { text },
        timeout: config.REQUEST_TIMEOUT,
        enableChunked: true,
        responseType: 'arraybuffer',
        success: (res) => {
            if (finished) return;
            // 兜底：部分环境（低版本基础库/模拟器）不触发 onChunkReceived，
            // 此时整个响应体会一次性出现在 res.data 里，这里再解析一遍。
            const rest = extractWholeBody(res.data);
            if (rest) {
                rest.split('\n').forEach((line) => handleLine(line));
            }
            if (finished) return;
            finished = true;
            clearIdle();
            onError && onError(new Error('连接意外结束，未收到完成标记'));
        },
        fail: (error) => {
            if (finished) return;
            finished = true;
            clearIdle();
            onError && onError(new Error(error.errMsg || '网络请求失败'));
        },
    });

    // 必须在 request 返回后立刻挂载
    if (typeof task.onChunkReceived === 'function') {
        task.onChunkReceived((res) => {
            resetIdle();
            buffer += decoder.push(res.data);
            let index;
            while ((index = buffer.indexOf('\n')) >= 0) {
                const line = buffer.slice(0, index);
                buffer = buffer.slice(index + 1);
                handleLine(line);
            }
        });
    } else {
        // 低版本基础库：没有 onChunkReceived，只能等 success 里一次性解析（无打字机效果）
        console.warn('[stream] 当前基础库不支持 onChunkReceived，将退化为整段返回');
    }

    return {
        abort() {
            if (finished) return;
            finished = true;
            clearIdle();
            try {
                task && task.abort();
            } catch (e) {
                // ignore
            }
        },
    };
}

module.exports = { streamChat, Frame };
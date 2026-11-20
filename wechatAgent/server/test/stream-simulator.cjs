/**
 * 小程序流式联调模拟器
 *
 * 在浏览器里用 shim 模拟 wx.request({enableChunked:true}) + onChunkReceived，
 * 用 fetch + ReadableStream 逐块喂给真实的小程序 stream.js，验证：
 *  1. NDJSON 跨 chunk 半行拼接
 *  2. 中文多字节字符被切开时不乱码
 *  3. done/stats 帧正确收尾
 */
const fs = require('fs');
const http = require('http');
const path = require('path');

const MINI_DIR = '/root/workspace/agentHarness/wechatAgent/miniprogram';
const BASE = 'http://127.0.0.1:8090';

/** 极简 localStorage */
const memory = new Map();
global.wx = {
    getStorageSync: (key) => (memory.has(key) ? memory.get(key) : ''),
    setStorageSync: (key, value) => memory.set(key, value),
    removeStorageSync: (key) => memory.delete(key),
    login: ({ success }) => success({ code: '' }),
    request: () => {
        throw new Error('本模拟器只覆盖流式接口，普通请求走 fetch');
    },
};

/**
 * 用 fetch 模拟 wx.request + enableChunked
 * @param {Object} options
 * @returns {{abort:Function, onChunkReceived:Function}}
 */
function fakeWxRequest(options) {
    const controller = new AbortController();
    let chunkHandler = null;
    let doneHandler = null;
    let failHandler = null;

    (async () => {
        try {
            const res = await fetch(options.url, {
                method: options.method || 'GET',
                headers: options.header || {},
                body: options.data ? JSON.stringify(options.data) : undefined,
                signal: controller.signal,
            });

            if (!res.ok) {
                const text = await res.text();
                failHandler && failHandler({ errMsg: `HTTP ${res.status}: ${text.slice(0, 200)}` });
                return;
            }

            const reader = res.body.getReader();
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                // 关键：模拟真实网络把字节切成不规则大小的块（含 1 字节块，专门打碎中文）
                let offset = 0;
                while (offset < value.length) {
                    const size = Math.min(1 + Math.floor(Math.random() * 7), value.length - offset);
                    const slice = value.slice(offset, offset + size);
                    offset += size;
                    if (chunkHandler) chunkHandler({ data: slice.buffer });
                }
            }
            doneHandler && doneHandler();
            options.success && options.success({ statusCode: res.status, data: null });
        } catch (error) {
            if (error.name === 'AbortError') {
                failHandler && failHandler({ errMsg: 'request:fail abort' });
            } else {
                failHandler && failHandler({ errMsg: error.message });
            }
        }
    })();

    return {
        onChunkReceived(handler) {
            chunkHandler = handler;
        },
        abort() {
            controller.abort();
        },
    };
}

/**
 * 安全截断：避免把 emoji 的代理对切成两半
 * @param {string} text
 * @param {number} max
 */
function safeSlice(text, max) {
    if (text.length <= max) return text;
    let end = max;
    const code = text.charCodeAt(end - 1);
    // 高位代理说明此处正好切开了一个 emoji
    if (code >= 0xd800 && code <= 0xdbff) end -= 1;
    return text.slice(0, end);
}

async function main() {
    // ---------- 登录拿 token ----------
    const loginRes = await fetch(`${BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deviceId: 'stream-simulator' }),
    });
    const login = await loginRes.json();
    memory.set('auth_token', login.token);
    memory.set('auth_user', login.user);

    // ---------- 建会话 ----------
    const sessionRes = await fetch(`${BASE}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${login.token}` },
        body: JSON.stringify({ engine: 'default' }),
    });
    const session = await sessionRes.json();
    const sessionId = session.session.id;

    // ---------- 装载真实 stream.js ----------
    wx.request = fakeWxRequest;
    const streamPath = path.join(MINI_DIR, 'utils/stream.js');
    delete require.cache[require.resolve(streamPath)];
    // stream.js 依赖 config.js / storage.js，直接复用真实文件
    const { streamChat } = require(streamPath);

    // ---------- 跑一轮 ----------
    const frames = [];
    let content = '';
    let reasoning = '';
    let doneStatus = null;

    const question = '请用中文回答：列出微信小程序开发最关键的 3 个技术点，每点 30 字左右，务必使用中文并包含 emoji 🚀';

    await new Promise((resolve, reject) => {
        const started = Date.now();
        streamChat({
            sessionId,
            text: question,
            onFrame: (frame) => {
                frames.push({ ...frame, at: Date.now() - started });
                if (frame.t === 'delta') content += frame.text;
                if (frame.t === 'reasoning') reasoning += frame.text;
            },
            onComplete: (frame) => {
                doneStatus = frame.status;
                resolve();
            },
            onError: (error) => reject(error),
        });
    });

    const kinds = {};
    frames.forEach((f) => {
        kinds[f.t] = (kinds[f.t] || 0) + 1;
    });

    console.log('======== 联调结果 ========');
    console.log('会话:', sessionId);
    console.log('帧类型:', JSON.stringify(kinds));
    console.log('终态:', doneStatus);
    console.log('思考字数:', reasoning.length);
    console.log('正文字数:', content.length);
    console.log('首帧耗时:', frames[0]?.at, 'ms');
    console.log('首字耗时:', frames.find((f) => f.t === 'delta' || f.t === 'reasoning')?.at, 'ms');
    console.log('总耗时:', frames[frames.length - 1]?.at, 'ms');
    console.log('正文前 120 字:', safeSlice(content, 120).replace(/\n/g, '\\n'));
    console.log('乱码检查:', /[\uFFFD]|Ã|â€/.test(content) ? '发现乱码！' : '无乱码 ✓');
    console.log('emoji 保留:', /🚀/.test(content) ? '是 ✓' : '否（可能被模型省略）');

    // ---------- 断言 ----------
    const problems = [];
    if (doneStatus !== 'done') problems.push(`终态异常: ${doneStatus}`);
    if (!content.length) problems.push('没有收到正文');
    if (/[\uFFFD]/.test(content)) problems.push('正文包含替换字符（乱码）');
    if (frames[frames.length - 1].t !== 'done') problems.push('最后一帧不是 done');
    if (!frames.some((f) => f.t === 'start')) problems.push('缺少 start 帧');

    console.log('======== 断言 ========');
    console.log(problems.length === 0 ? '全部通过 ✓' : `失败: ${problems.join('; ')}`);
    process.exit(problems.length === 0 ? 0 : 1);
}

main().catch((error) => {
    console.error('联调失败:', error);
    process.exit(1);
});
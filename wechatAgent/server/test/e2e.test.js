/**
 * 端到端接口测试（需要后端已启动，且 OpenCode 实例可访问）
 *
 * 运行：node test/e2e.test.js
 * 环境变量：BASE（默认 http://127.0.0.1:8090）
 */

import test from 'node:test';
import assert from 'node:assert/strict';

const BASE = process.env.BASE || 'http://127.0.0.1:8090';

/**
 * 发 JSON 请求
 * @param {string} path
 * @param {{method?:string, body?:Object, token?:string}} [options]
 */
async function api(path, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (options.token) headers.Authorization = `Bearer ${options.token}`;
    const res = await fetch(`${BASE}${path}`, {
        method: options.method || 'GET',
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
    });
    const text = await res.text();
    let data = null;
    try {
        data = text ? JSON.parse(text) : null;
    } catch {
        data = text;
    }
    return { status: res.status, data };
}

/**
 * 登录两个独立用户
 */
async function loginPair() {
    const [a, b] = await Promise.all([
        api('/api/auth/login', { method: 'POST', body: { deviceId: `e2e-a-${Date.now()}` } }),
        api('/api/auth/login', { method: 'POST', body: { deviceId: `e2e-b-${Date.now()}` } }),
    ]);
    assert.equal(a.status, 200, '用户 A 登录失败');
    assert.equal(b.status, 200, '用户 B 登录失败');
    return { tokenA: a.data.token, tokenB: b.data.token };
}

/**
 * 跑一轮流式对话，返回聚合结果
 * @param {string} token
 * @param {string} sessionId
 * @param {string} text
 */
async function runTurn(token, sessionId, text) {
    const res = await fetch(`${BASE}/api/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text }),
    });
    assert.equal(res.status, 200, `流式接口应返回 200，实际 ${res.status}`);
    assert.ok(!res.headers.get('content-length'), '流式响应不能带 Content-Length');

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    const frames = [];

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let index;
        while ((index = buffer.indexOf('\n')) >= 0) {
            const line = buffer.slice(0, index).trim();
            buffer = buffer.slice(index + 1);
            if (line) frames.push(JSON.parse(line));
        }
    }

    const content = frames.filter((f) => f.t === 'delta').map((f) => f.text).join('');
    const doneFrame = frames.find((f) => f.t === 'done');
    return { frames, content, done: doneFrame, kinds: countKinds(frames) };
}

/**
 * @param {Array} frames
 */
function countKinds(frames) {
    return frames.reduce((acc, frame) => {
        acc[frame.t] = (acc[frame.t] || 0) + 1;
        return acc;
    }, {});
}

// ==================== 健康检查 ====================

test('health: 返回服务与引擎状态', async () => {
    const { status, data } = await api('/api/health');
    assert.equal(status, 200);
    assert.equal(data.ok, true);
    assert.ok(Array.isArray(data.engines));
    assert.ok(data.engines.length >= 1);
});

// ==================== 鉴权 ====================

test('auth: 无 token 访问受保护接口返回 401', async () => {
    const list = await api('/api/sessions');
    assert.equal(list.status, 401);
    assert.equal(list.data.error.code, 'UNAUTHORIZED');

    const bootstrap = await api('/api/bootstrap');
    assert.equal(bootstrap.status, 401);
});

test('auth: 伪造 token 被拒绝', async () => {
    const res = await api('/api/sessions', { token: 'forged.token' });
    assert.equal(res.status, 401);
});

test('auth: dev 模式同一设备标识登录到同一用户', async () => {
    const deviceId = `e2e-stable-${Date.now()}`;
    const first = await api('/api/auth/login', { method: 'POST', body: { deviceId } });
    const second = await api('/api/auth/login', { method: 'POST', body: { deviceId } });
    assert.equal(first.data.user.id, second.data.user.id);
});

// ==================== 会话管理 ====================

test('session: 创建、重命名、查询、删除', async () => {
    const { tokenA } = await loginPair();

    const created = await api('/api/sessions', {
        method: 'POST',
        token: tokenA,
        body: { title: '新的对话' },
    });
    assert.equal(created.status, 201);
    const sessionId = created.data.session.id;

    const renamed = await api(`/api/sessions/${sessionId}`, {
        method: 'PATCH',
        token: tokenA,
        body: { title: '测试标题' },
    });
    assert.equal(renamed.status, 200);
    assert.equal(renamed.data.session.title, '测试标题');

    const detail = await api(`/api/sessions/${sessionId}`, { token: tokenA });
    assert.equal(detail.data.session.title, '测试标题');

    const removed = await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
    assert.equal(removed.status, 200);

    const gone = await api(`/api/sessions/${sessionId}`, { token: tokenA });
    assert.equal(gone.status, 404);
});

test('session: 重命名拒绝空标题', async () => {
    const { tokenA } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    const res = await api(`/api/sessions/${sessionId}`, {
        method: 'PATCH',
        token: tokenA,
        body: { title: '   ' },
    });
    assert.equal(res.status, 400);
    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

test('session: 不能访问他人会话（越权防护）', async () => {
    const { tokenA, tokenB } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    const read = await api(`/api/sessions/${sessionId}`, { token: tokenB });
    assert.equal(read.status, 403);

    const messages = await api(`/api/sessions/${sessionId}/messages`, { token: tokenB });
    assert.equal(messages.status, 403);

    const removed = await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenB });
    assert.equal(removed.status, 403);

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

// ==================== 流式对话 ====================

test('chat: 单轮流式返回 start/delta/done 且内容入库', async () => {
    const { tokenA } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    const turn = await runTurn(tokenA, sessionId, '只回复两个字：收到');
    assert.ok(turn.kinds.start === 1, '应有 1 个 start 帧');
    assert.ok((turn.kinds.delta || 0) >= 1, '应至少收到 1 个 delta 帧');
    assert.equal(turn.done.status, 'done');
    assert.ok(turn.content.length > 0, '正文不能为空');

    const history = await api(`/api/sessions/${sessionId}/messages`, { token: tokenA });
    const messages = history.data.messages;
    assert.equal(messages.length, 2);
    assert.equal(messages[0].role, 'user');
    assert.equal(messages[1].role, 'assistant');
    assert.equal(messages[1].status, 'done');
    assert.equal(messages[1].content, turn.content, '落库内容应与流式内容一致');

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

test('chat: 首条提问自动成为会话标题', async () => {
    const { tokenA } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    await runTurn(tokenA, sessionId, '帮我总结一下这个小程序的架构');
    const detail = await api(`/api/sessions/${sessionId}`, { token: tokenA });
    assert.ok(detail.data.session.title.includes('帮我总结'), `标题应取自问题，实际: ${detail.data.session.title}`);

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

test('chat: 多轮对话保持上下文', async () => {
    const { tokenA } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    await runTurn(tokenA, sessionId, '请记住这个数字：8848，只回复「记住了」');
    const second = await runTurn(tokenA, sessionId, '我刚才让你记的数字是多少？只回复数字');

    assert.ok(/8848/.test(second.content), `模型应记得上下文，实际回答: ${second.content}`);

    const history = await api(`/api/sessions/${sessionId}/messages`, { token: tokenA });
    assert.equal(history.data.messages.length, 4, '两轮对话应有 4 条消息');

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

test('chat: 空提问被拒绝', async () => {
    const { tokenA } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    const res = await api(`/api/sessions/${sessionId}/messages`, {
        method: 'POST',
        token: tokenA,
        body: { text: '   ' },
    });
    assert.equal(res.status, 400);

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

test('chat: 超长提问被拒绝', async () => {
    const { tokenA } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    const res = await api(`/api/sessions/${sessionId}/messages`, {
        method: 'POST',
        token: tokenA,
        body: { text: 'x'.repeat(8001) },
    });
    assert.equal(res.status, 400);

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

// ==================== 中断 ====================

test('chat: 停止生成后状态为 aborted', async () => {
    const { tokenA } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    // 后台发起长任务
    const pending = runTurn(tokenA, sessionId, '写一篇 2000 字的文章介绍小程序架构').catch((error) => ({ error }));

    // 等首字出现后再停止
    await new Promise((resolve) => setTimeout(resolve, 6000));
    const stop = await api(`/api/sessions/${sessionId}/stop`, { method: 'POST', token: tokenA });
    assert.equal(stop.status, 200);
    assert.equal(stop.data.aborted, true);

    const result = await pending;
    assert.ok(!result.error, `流不应异常结束: ${result.error?.message}`);
    assert.ok(['aborted', 'done'].includes(result.done.status), `终态应为 aborted，实际 ${result.done.status}`);

    const history = await api(`/api/sessions/${sessionId}/messages`, { token: tokenA });
    const last = history.data.messages.at(-1);
    assert.ok(['aborted', 'done'].includes(last.status), `落库状态应为 aborted，实际 ${last.status}`);

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

test('chat: 空闲会话 stop 返回 aborted=false', async () => {
    const { tokenA } = await loginPair();
    const created = await api('/api/sessions', { method: 'POST', token: tokenA, body: {} });
    const sessionId = created.data.session.id;

    const res = await api(`/api/sessions/${sessionId}/stop`, { method: 'POST', token: tokenA });
    assert.equal(res.status, 200);
    assert.equal(res.data.aborted, false);

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

// ==================== v2 引擎 ====================

test('chat: v2 引擎同样支持流式（若已配置）', async () => {
    const { tokenA } = await loginPair();
    const bootstrap = await api('/api/bootstrap', { token: tokenA });
    const hasV2 = (bootstrap.data.engines || []).some((engine) => engine.key === 'v2');
    if (!hasV2) return;

    const created = await api('/api/sessions', {
        method: 'POST',
        token: tokenA,
        body: { engine: 'v2' },
    });
    const sessionId = created.data.session.id;

    const turn = await runTurn(tokenA, sessionId, '只回复三个字：没问题');
    assert.equal(turn.done.status, 'done');
    assert.ok(turn.content.length > 0);

    await api(`/api/sessions/${sessionId}`, { method: 'DELETE', token: tokenA });
});

test('chat: 未知引擎被拒绝', async () => {
    const { tokenA } = await loginPair();
    const res = await api('/api/sessions', {
        method: 'POST',
        token: tokenA,
        body: { engine: 'not-exist' },
    });
    assert.equal(res.status, 400);
});
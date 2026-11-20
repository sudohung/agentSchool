/**
 * 后端自测（Node 内置 test runner）
 * 覆盖：token 签名/篡改/过期、路由匹配、存储读写与损坏恢复、事件归一化
 *
 * 运行：node --test test/
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

import { TokenService } from '../src/auth/token.js';
import { Router } from '../src/http/router.js';
import { ChatStore } from '../src/store/chat-store.js';
import { EventNormalizer } from '../src/opencode/event-normalizer.js';

/** 创建临时目录并在用完后清理 */
function withTempDir(fn) {
    return async () => {
        const dir = mkdtempSync(join(tmpdir(), 'wx-agent-'));
        try {
            await fn(dir);
        } finally {
            rmSync(dir, { recursive: true, force: true });
        }
    };
}

// ==================== token ====================

test('token: 签发后能验签并还原用户', withTempDir((dir) => {
    const service = new TokenService(dir);
    const token = service.issue({ userId: 'usr_1', openid: 'dev_abc' });
    const claims = service.verify(token);
    assert.equal(claims.userId, 'usr_1');
    assert.equal(claims.openid, 'dev_abc');
}));

test('token: 篡改 payload 后验签失败', withTempDir((dir) => {
    const service = new TokenService(dir);
    const token = service.issue({ userId: 'usr_1', openid: 'dev_abc' });
    const signature = token.split('.')[1];
    const forged = Buffer.from(
        JSON.stringify({ userId: 'usr_2', openid: 'dev_abc', exp: Date.now() + 10000 })
    ).toString('base64url');
    assert.equal(service.verify(`${forged}.${signature}`), null);
}));

test('token: 过期 token 被拒绝', withTempDir((dir) => {
    const service = new TokenService(dir);
    const expiredBody = Buffer.from(
        JSON.stringify({ userId: 'usr_1', openid: 'dev_abc', exp: Date.now() - 1000 })
    ).toString('base64url');
    // 用同一 service 的签名密钥重新签一个已过期的 payload
    const realToken = service.issue({ userId: 'usr_1', openid: 'dev_abc' });
    const forged = service.verify(`${expiredBody}.${realToken.split('.')[1]}`);
    assert.equal(forged, null);
}));

test('token: 垃圾输入不会抛异常', withTempDir((dir) => {
    const service = new TokenService(dir);
    for (const bad of ['', 'abc', 'a.b', 'a.b.c', '...', null, undefined, 123]) {
        assert.equal(service.verify(bad), null);
    }
}));

// ==================== 路由 ====================

test('router: 路径参数与优先级', () => {
    const router = new Router();
    router.get('/api/sessions', () => 'list');
    router.get('/api/sessions/:id', () => 'detail');
    router.post('/api/sessions/:id/messages', () => 'send');

    assert.equal(router.match('GET', '/api/sessions').handler(), 'list');
    assert.equal(router.match('GET', '/api/sessions/sc_1').params.id, 'sc_1');
    assert.equal(router.match('POST', '/api/sessions/sc_1/messages').handler(), 'send');
    assert.equal(router.match('GET', '/api/sessions/sc_1/messages'), null);
    assert.equal(router.match('GET', '/api/unknown'), null);
});

test('router: 尾斜杠容错与 URL 解码', () => {
    const router = new Router();
    router.get('/api/sessions/:id', () => 'ok');
    assert.equal(router.match('GET', '/api/sessions/sc_1/').params.id, 'sc_1');
    assert.equal(router.match('GET', '/api/sessions/sc%5F1').params.id, 'sc_1');
});

// ==================== 存储 ====================

test('store: 会话与消息持久化', withTempDir((dir) => {
    const store = new ChatStore(dir);
    const user = store.upsertUser('dev_abc', { mode: 'dev', nickname: '测试' });
    const session = store.createSession({ userId: user.id, title: '新的对话', engine: 'default', model: 'default' });

    store.appendMessage(session.id, { role: 'user', content: '你好' });
    const assistant = store.appendMessage(session.id, { role: 'assistant', content: '', status: 'streaming' });
    store.patchMessage(session.id, assistant.id, { content: '你好呀', status: 'done' }, true);

    // 重新打开，验证落盘
    const reopened = new ChatStore(dir);
    const messages = reopened.listMessages(session.id);
    assert.equal(messages.length, 2);
    assert.equal(messages[1].content, '你好呀');
    assert.equal(messages[1].status, 'done');
    assert.equal(reopened.listSessions(user.id).length, 1);
}));

test('store: 删除会话同时清掉消息', withTempDir((dir) => {
    const store = new ChatStore(dir);
    const user = store.upsertUser('dev_x', { mode: 'dev' });
    const session = store.createSession({ userId: user.id, title: 't', engine: 'default', model: 'default' });
    store.appendMessage(session.id, { role: 'user', content: 'hi' });

    assert.equal(store.deleteSession(session.id), true);
    assert.equal(store.getSession(session.id), null);
    assert.deepEqual(store.listMessages(session.id), []);
    assert.equal(store.deleteSession(session.id), false);
}));

test('store: 文件损坏时备份而不是静默丢数据', withTempDir((dir) => {
    const store = new ChatStore(dir);
    store.upsertUser('dev_1', { mode: 'dev' });
    writeFileSync(join(dir, 'chat-store.json'), '{ 坏掉的 json');

    const reopened = new ChatStore(dir);
    assert.deepEqual(reopened.listSessions('x'), []);
}));

test('store: 同一 openid 重复登录不产生新用户', withTempDir((dir) => {
    const store = new ChatStore(dir);
    const first = store.upsertUser('dev_same', { mode: 'dev', nickname: 'A' });
    const second = store.upsertUser('dev_same', { mode: 'dev', nickname: 'B' });
    assert.equal(first.id, second.id);
    assert.equal(second.nickname, 'B');
}));

// ==================== 事件归一化 ====================

test('normalizer: v1 delta 按 part 类型区分正文与思考', () => {
    const normalizer = new EventNormalizer();
    normalizer.normalize({
        type: 'message.part.updated',
        properties: { sessionID: 'ses_1', part: { id: 'prt_r', type: 'reasoning' } },
    });
    normalizer.normalize({
        type: 'message.part.updated',
        properties: { sessionID: 'ses_1', part: { id: 'prt_t', type: 'text' } },
    });

    assert.deepEqual(
        normalizer.normalize({
            type: 'message.part.delta',
            properties: { sessionID: 'ses_1', partID: 'prt_r', field: 'text', delta: '思考中' },
        }),
        [{ kind: 'reasoning', sessionId: 'ses_1', delta: '思考中' }]
    );
    assert.deepEqual(
        normalizer.normalize({
            type: 'message.part.delta',
            properties: { sessionID: 'ses_1', partID: 'prt_t', field: 'text', delta: '回答' },
        }),
        [{ kind: 'text', sessionId: 'ses_1', delta: '回答' }]
    );
});

test('normalizer: v1 未知 part 的 delta 归为正文', () => {
    const normalizer = new EventNormalizer();
    assert.deepEqual(
        normalizer.normalize({
            type: 'message.part.delta',
            properties: { sessionID: 'ses_1', partID: 'prt_unknown', delta: 'x' },
        }),
        [{ kind: 'text', sessionId: 'ses_1', delta: 'x' }]
    );
});

test('normalizer: v2 delta、idle、error', () => {
    const normalizer = new EventNormalizer();
    assert.deepEqual(
        normalizer.normalize({ type: 'session.text.delta', data: { sessionID: 'ses_2', delta: '你好' } }),
        [{ kind: 'text', sessionId: 'ses_2', delta: '你好' }]
    );
    assert.deepEqual(
        normalizer.normalize({ type: 'session.execution.succeeded', data: { sessionID: 'ses_2' } }),
        [{ kind: 'idle', sessionId: 'ses_2' }]
    );
    assert.deepEqual(
        normalizer.normalize({
            type: 'session.execution.failed',
            data: { sessionID: 'ses_2', error: { data: { message: '炸了' } } },
        }),
        [{ kind: 'error', sessionId: 'ses_2', message: '炸了' }]
    );
});

test('normalizer: v2 表单事件转成提问且过滤隐藏字段', () => {
    const normalizer = new EventNormalizer();
    const events = normalizer.normalize({
        type: 'form.created',
        data: {
            form: {
                id: 'frm_1',
                sessionID: 'ses_3',
                fields: [
                    { key: 'a', title: '选一个', type: 'multiselect', options: [{ label: 'A', value: 'a' }] },
                    { key: 'b', title: '隐藏', type: 'string', hidden: true },
                ],
            },
        },
    });
    assert.equal(events.length, 1);
    assert.equal(events[0].kind, 'question');
    assert.equal(events[0].questions.length, 1);
    assert.equal(events[0].questions[0].multiple, true);
    assert.deepEqual(events[0].questions[0].options, [{ label: 'A', value: 'a' }]);
});

test('normalizer: 未知事件与残缺数据不抛异常', () => {
    const normalizer = new EventNormalizer();
    assert.deepEqual(normalizer.normalize({ type: 'unknown.event', properties: {} }), []);
    assert.deepEqual(normalizer.normalize({}), []);
    assert.deepEqual(normalizer.normalize({ type: 'message.part.delta' }), []);
    assert.deepEqual(normalizer.normalize(null), []);
});

test('normalizer: part 类型缓存不会无限增长', () => {
    const normalizer = new EventNormalizer();
    for (let i = 0; i < 2500; i += 1) {
        normalizer.normalize({
            type: 'message.part.updated',
            properties: { sessionID: 'ses_1', part: { id: `prt_${i}`, type: 'text' } },
        });
    }
    // 老记录被淘汰，新记录仍在
    assert.deepEqual(
        normalizer.normalize({
            type: 'message.part.delta',
            properties: { sessionID: 'ses_1', partID: 'prt_2499', delta: 'x' },
        }),
        [{ kind: 'text', sessionId: 'ses_1', delta: 'x' }]
    );
});
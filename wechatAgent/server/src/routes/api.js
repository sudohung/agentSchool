/**
 * API 路由定义
 *
 * 约定：
 *  - 除 /api/health、/api/auth/login 外，全部要求 Bearer token
 *  - 所有以 /api/sessions/{id} 开头的接口都会校验会话归属，防止越权访问他人会话
 */

import { Router } from '../http/router.js';
import { readJsonBody, sendJson, sendError, httpError } from '../http/respond.js';
import { ErrorCode, MessageStatus } from '../constants.js';

/**
 * 构造路由表
 * @param {{config:Object, auth:Object, store:Object, engines:Object, runner:Object}} deps
 */
export function buildRouter(deps) {
    const { config, auth, store, engines, runner } = deps;
    const router = new Router();

    // ==================== 基础 ====================

    router.get('/api/health', async ({ res }) => {
        const engineHealth = await engines.health();
        sendJson(res, 200, {
            ok: true,
            uptime: Math.round(process.uptime()),
            mode: auth.mode,
            allowDevLogin: auth.allowDevLogin,
            engines: engineHealth,
        });
    });

    router.post('/api/auth/login', async ({ req, res }) => {
        const body = await readJsonBody(req);
        const result = await auth.login(body);
        sendJson(res, 200, { ok: true, ...result });
    });

    // ==================== 启动配置（前端一次性拿全） ====================

    router.get('/api/bootstrap', async ({ req, res }) => {
        const user = requireUser(auth, req);
        sendJson(res, 200, {
            ok: true,
            user: toPublicUser(store.getUser(user.userId)),
            loginMode: auth.mode,
            allowDevLogin: auth.allowDevLogin,
            defaultEngine: engines.defaultKey,
            engines: engines.list(),
            models: config.models,
        });
    });

    // ==================== 会话 ====================

    router.get('/api/sessions', async ({ req, res }) => {
        const user = requireUser(auth, req);
        const sessions = store.listSessions(user.userId).map((session) => ({
            ...toPublicSession(session),
            busy: runner.isBusy(session.id),
            messageCount: store.listMessages(session.id).length,
        }));
        sendJson(res, 200, { ok: true, sessions });
    });

    router.post('/api/sessions', async ({ req, res }) => {
        const user = requireUser(auth, req);
        const body = await readJsonBody(req);
        const engineKey = body.engine || engines.defaultKey;
        engines.get(engineKey); // 校验引擎存在
        const session = store.createSession({
            userId: user.userId,
            title: body.title || '新的对话',
            engine: engineKey,
            model: body.modelKey || 'default',
        });
        sendJson(res, 201, {
            ok: true,
            session: toPublicSession(session),
        });
    });

    router.get('/api/sessions/:id', async ({ req, res, params }) => {
        const user = requireUser(auth, req);
        const session = requireSession(store, params.id, user.userId);
        sendJson(res, 200, {
            ok: true,
            session: { ...toPublicSession(session), busy: runner.isBusy(session.id) },
        });
    });

    router.patch('/api/sessions/:id', async ({ req, res, params }) => {
        const user = requireUser(auth, req);
        const session = requireSession(store, params.id, user.userId);
        const body = await readJsonBody(req);
        const title = String(body.title || '').trim();
        if (!title) throw httpError(400, ErrorCode.BAD_REQUEST, '标题不能为空');
        const updated = store.updateSession(session.id, { title: title.slice(0, 60) });
        sendJson(res, 200, { ok: true, session: toPublicSession(updated) });
    });

    router.delete('/api/sessions/:id', async ({ req, res, params }) => {
        const user = requireUser(auth, req);
        const session = requireSession(store, params.id, user.userId);
        await runner.abort(session.id);
        store.deleteSession(session.id);
        sendJson(res, 200, { ok: true });
    });

    // ==================== 消息 ====================

    router.get('/api/sessions/:id/messages', async ({ req, res, params }) => {
        const user = requireUser(auth, req);
        const session = requireSession(store, params.id, user.userId);
        sendJson(res, 200, {
            ok: true,
            messages: store.listMessages(session.id).map(toPublicMessage),
            busy: runner.isBusy(session.id),
        });
    });

    /**
     * 流式发送：返回 NDJSON（chunked），小程序用 enableChunked 逐帧读取
     */
    router.post('/api/sessions/:id/messages', async ({ req, res, params }) => {
        const user = requireUser(auth, req);
        const session = requireSession(store, params.id, user.userId);
        const body = await readJsonBody(req);
        const text = String(body.text || '').trim();
        if (!text) throw httpError(400, ErrorCode.BAD_REQUEST, '提问内容不能为空');
        if (text.length > 8000) throw httpError(400, ErrorCode.BAD_REQUEST, '提问内容过长（上限 8000 字）');

        await runner.run({
            session,
            text,
            model: resolveModel(config, session.model),
            res,
        });
    });

    router.post('/api/sessions/:id/stop', async ({ req, res, params }) => {
        const user = requireUser(auth, req);
        const session = requireSession(store, params.id, user.userId);
        const aborted = await runner.abort(session.id);
        sendJson(res, 200, { ok: true, aborted });
    });

    // ==================== 交互闭环 ====================

    router.post('/api/sessions/:id/form', async ({ req, res, params }) => {
        const user = requireUser(auth, req);
        const session = requireSession(store, params.id, user.userId);
        const body = await readJsonBody(req);
        if (!body.formId) throw httpError(400, ErrorCode.BAD_REQUEST, '缺少 formId');
        if (!session.opencodeSessionId) throw httpError(400, ErrorCode.BAD_REQUEST, '会话尚未建立引擎映射');

        const runtime = engines.get(session.engine);
        await runtime.client.replyForm(session.opencodeSessionId, body.formId, body.answers || []);
        sendJson(res, 200, { ok: true });
    });

    router.post('/api/sessions/:id/permission', async ({ req, res, params }) => {
        const user = requireUser(auth, req);
        const session = requireSession(store, params.id, user.userId);
        const body = await readJsonBody(req);
        if (!body.requestId) throw httpError(400, ErrorCode.BAD_REQUEST, '缺少 requestId');
        const decision = ['once', 'always', 'reject'].includes(body.decision) ? body.decision : 'reject';
        if (!session.opencodeSessionId) throw httpError(400, ErrorCode.BAD_REQUEST, '会话尚未建立引擎映射');

        const runtime = engines.get(session.engine);
        await runtime.client.replyPermission(session.opencodeSessionId, body.requestId, decision);
        sendJson(res, 200, { ok: true });
    });

    return router;
}

/**
 * 从请求中取登录用户，未登录抛 401
 * @param {Object} auth
 * @param {import('http').IncomingMessage} req
 */
function requireUser(auth, req) {
    const user = auth.authenticate(req);
    if (!user) throw httpError(401, ErrorCode.UNAUTHORIZED, '登录已失效，请重新登录');
    return user;
}

/**
 * 取会话并校验归属
 * @param {Object} store
 * @param {string} sessionId
 * @param {string} userId
 */
function requireSession(store, sessionId, userId) {
    const session = store.getSession(sessionId);
    if (!session) throw httpError(404, ErrorCode.NOT_FOUND, '会话不存在');
    if (session.userId !== userId) throw httpError(403, ErrorCode.FORBIDDEN, '无权访问该会话');
    return session;
}

/**
 * 按 key 取模型定义
 * @param {Object} config
 * @param {string} [key]
 * @returns {{providerID:string, modelID:string}|null}
 */
function resolveModel(config, key) {
    // default 条目若配置了具体模型则优先使用；未配置时回退引擎默认模型
    const model = config.models.find((item) => item.key === (key || 'default'));
    if (!model?.providerID || !model?.modelID) return null;
    return { providerID: model.providerID, modelID: model.modelID };
}

/**
 * 用户对外结构
 * @param {Object|null} user
 */
function toPublicUser(user) {
    if (!user) return null;
    return { id: user.id, nickname: user.nickname, avatar: user.avatar };
}

/**
 * 会话对外结构
 * @param {Object} session
 */
function toPublicSession(session) {
    return {
        id: session.id,
        title: session.title,
        engine: session.engine,
        model: session.model,
        createdAt: session.createdAt,
        updatedAt: session.updatedAt,
    };
}

/**
 * 消息对外结构（隐藏内部状态细节）
 * @param {Object} message
 */
function toPublicMessage(message) {
    return {
        id: message.id,
        role: message.role,
        content: message.content,
        reasoning: message.reasoning,
        status: message.status || MessageStatus.DONE,
        createdAt: message.createdAt,
    };
}
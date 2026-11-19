// opencode Server HTTP 客户端
// 兼容两种服务端协议：
//  - v1：/session、/session/:id/message（无鉴权）
//  - v2：/api/session、/api/session/:id/prompt（HTTP Basic 认证，prompt 异步，需轮询消息直至 idle）
// 协议版本按实例自动探测（结果缓存）：v2 的 SPA 会对任意路径返回 HTML 200，因此所有 v1 请求都要求响应体是 JSON。
import { config } from './config.js';

// 所有函数支持传入目标实例 baseUrl（多实例路由）；缺省使用全局默认实例
const normalize = base => String(base ?? config.opencodeBaseUrl).replace(/\/+$/, '');

const sleep = ms => new Promise(r => setTimeout(r, ms));

/** v2 协议探测结果缓存：baseUrl -> { version, at } */
const VERSION_CACHE_TTL_MS = 5 * 60 * 1000;
const versionCache = new Map();

/** v2 轮询间隔（毫秒） */
const V2_POLL_MS = 5_000;

const isJsonBody = v => v !== null && typeof v === 'object';

/** HTTP Basic 认证头（v2 用户名固定 opencode；未配置密码时不加头） */
function authHeaders(password) {
  const pwd = password ?? config.opencodePassword ?? '';
  if (!pwd) return {};
  return { authorization: `Basic ${Buffer.from(`opencode:${pwd}`).toString('base64')}` };
}

/** 实例需要认证但未提供密码时的统一错误 */
function authRequiredError(baseUrl) {
  const err = new Error(`opencode 实例需要认证（v2）：${normalize(baseUrl)} 未提供密码，请在注册实例时传 password 或配置 OPENCODE_PASSWORD`);
  err.status = 401;
  return err;
}

/** 解析 model：支持 "provider/model-id" 字符串或 {providerID, modelID} 对象 */
function parseModel(model) {
  if (!model) return null;
  if (typeof model !== 'string') return model;
  const [providerID, ...rest] = model.split('/');
  if (!providerID || rest.length === 0) return null;
  return { providerID, modelID: rest.join('/') };
}

/** 底层单次 HTTP 请求，返回 { status, ok, body }（body 已尝试 JSON 解析） */
async function rawRequest(pathname, options = {}, timeoutMs = 30_000, baseUrl, password) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(new Error(`request timeout: ${pathname}`)), timeoutMs);
  try {
    const res = await fetch(normalize(baseUrl) + pathname, {
      ...options,
      headers: { ...authHeaders(password), ...(options.headers ?? {}) },
      signal: ctrl.signal,
    });
    const text = await res.text();
    let body = null;
    try { body = text ? JSON.parse(text) : null; } catch { body = text; }
    return { status: res.status, ok: res.ok, body };
  } finally {
    clearTimeout(timer);
  }
}

/**
 * 带错误抛出的请求。
 * jsonOnly=true 时要求响应体为 JSON：v2 服务的 SPA 对任意路径返回 HTML 200，
 * 仅看 2xx 会把“网页/代理错误页”误判为接口成功。
 */
async function request(pathname, options = {}, timeoutMs = 30_000, baseUrl, password, { jsonOnly = true } = {}) {
  const res = await rawRequest(pathname, options, timeoutMs, baseUrl, password);
  if (!res.ok) {
    if (res.status === 401 || res.status === 403) throw authRequiredError(baseUrl);
    const detail = typeof res.body === 'string'
      ? res.body.slice(0, 500)
      : JSON.stringify(res.body)?.slice(0, 500);
    const err = new Error(`opencode API ${res.status}: ${detail ?? 'null'}`);
    err.status = res.status;
    throw err;
  }
  if (jsonOnly && !isJsonBody(res.body)) {
    const err = new Error(`opencode API 返回非 JSON 响应: ${pathname}（可能是网页/代理错误页，不是 opencode 接口）`);
    err.status = res.status;
    err.nonJson = true;
    throw err;
  }
  return res.body;
}

/**
 * 探测实例 API 版本（结果缓存 5 分钟）。
 * 判定顺序：
 *  1) /api/info（v2 需要 Basic 认证）：200 且 version 以 2 开头 → v2；401/403 → v2（缺密码）
 *  2) /session?limit=1 返回 JSON → v1
 * 两者都不满足则报错，避免把网页/网关当成 opencode。
 * @param {string} baseUrl
 * @param {string} [password]
 * @returns {Promise<'v1'|'v2'>}
 */
export async function detectVersion(baseUrl, password) {
  const key = normalize(baseUrl);
  const cached = versionCache.get(key);
  if (cached && Date.now() - cached.at < VERSION_CACHE_TTL_MS) return cached.version;

  const remember = version => {
    versionCache.set(key, { version, at: Date.now() });
    return version;
  };

  const info = await rawRequest('/api/info', {}, 5_000, key, password).catch(() => null);
  if (info) {
    if (info.ok && isJsonBody(info.body) && String(info.body?.version ?? '').startsWith('2')) {
      return remember('v2');
    }
    if (info.status === 401 || info.status === 403) return remember('v2');
  }

  const legacy = await rawRequest('/session?limit=1', {}, 5_000, key, password).catch(() => null);
  if (legacy?.ok && isJsonBody(legacy.body)) return remember('v1');
  if (legacy?.status === 401 || legacy?.status === 403) return remember('v2');

  throw new Error(`无法识别 opencode 实例协议：${key}（请确认地址是 opencode server，而不是网页或网关）`);
}

/** 清除版本缓存（实例升级 v1→v2 时使用） */
export function invalidateVersionCache(baseUrl) {
  if (baseUrl) versionCache.delete(normalize(baseUrl));
  else versionCache.clear();
}

/** 会话是否存在 */
export async function sessionExists(sessionId, baseUrl, password) {
  if (!sessionId) return false;
  const version = await detectVersion(baseUrl, password);
  try {
    if (version === 'v2') {
      await request(`/api/session/${encodeURIComponent(sessionId)}`, {}, 10_000, baseUrl, password);
    } else {
      await request(`/session/${encodeURIComponent(sessionId)}`, {}, 10_000, baseUrl, password);
    }
    return true;
  } catch (err) {
    if (err.status === 404) return false;
    if (err.status === 401) throw err; // 认证问题不能被当成“会话不存在”
    if (err.nonJson) return false; // 非 opencode 响应，不能当作“会话存在”
    throw err;
  }
}

/**
 * 新建会话
 * @param {string} title
 * @param {string} [baseUrl]
 * @param {string} [password]
 * @param {string|{providerID:string, modelID:string}} [model] - v2 在会话维度指定模型
 * @returns {Promise<string>} 会话 ID
 */
export async function createSession(title, baseUrl, password, model) {
  const version = await detectVersion(baseUrl, password);
  const sessionTitle = title?.slice(0, 80) || 'opencode-scheduler';
  const parsedModel = parseModel(model);

  if (version === 'v2') {
    const body = { title: sessionTitle };
    if (parsedModel) body.model = { providerID: parsedModel.providerID, id: parsedModel.modelID };
    if (process.env.OPENCODE_DIRECTORY) body.location = { directory: process.env.OPENCODE_DIRECTORY };
    const res = await request('/api/session', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    }, 30_000, baseUrl, password);
    const sessionId = res?.data?.id ?? res?.id;
    if (!sessionId) throw new Error(`创建 v2 会话成功但未拿到 ID: ${JSON.stringify(res)?.slice(0, 300)}`);
    return sessionId;
  }

  const body = { title: sessionTitle };
  if (process.env.OPENCODE_DIRECTORY) body.directory = process.env.OPENCODE_DIRECTORY;
  if (parsedModel) body.model = parsedModel;
  const res = await request('/session', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }, 30_000, baseUrl, password);
  const sessionId = res?.id ?? res?.data?.id;
  if (!sessionId) throw new Error(`创建会话成功但未拿到 ID: ${JSON.stringify(res)?.slice(0, 300)}`);
  return sessionId;
}

/** 向会话发送消息（触发 agent 执行），返回响应 */
export async function sendMessage(sessionId, text, model, baseUrl, password) {
  const version = await detectVersion(baseUrl, password);

  if (version === 'v2') {
    // v2：prompt 异步提交，结果通过轮询消息获取（模型在会话维度生效）
    return request(`/api/session/${encodeURIComponent(sessionId)}/prompt`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ text }),
    }, 15_000, baseUrl, password);
  }

  const body = { parts: [{ type: 'text', text }] };
  const parsedModel = parseModel(model);
  if (parsedModel) body.model = parsedModel;
  return request(`/session/${encodeURIComponent(sessionId)}/message`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }, 15_000, baseUrl, password);
}

/**
 * 提交 prompt 并等待本轮 agent 执行完成，返回最终 assistant 文本。
 * v1 与 v2 分开实现：
 *  - v1：轮询消息，最新 assistant 已完成且静默 8s 视为结束；
 *  - v2：轮询消息，直到出现本轮 idle 事件，汇总本轮所有 assistant 文本。
 */
export async function runPromptAndWait(sessionId, prompt, model, timeoutMs = config.aiTimeoutMs, baseUrl, password) {
  const version = await detectVersion(baseUrl, password);
  return version === 'v2'
    ? runPromptV2(sessionId, prompt, model, timeoutMs, baseUrl, password)
    : runPromptV1(sessionId, prompt, model, timeoutMs, baseUrl, password);
}

/** v1：轮询等待 */
async function runPromptV1(sessionId, prompt, model, timeoutMs, baseUrl, password) {
  const submitTime = Date.now();
  // 提交 prompt：若会话繁忙导致 POST 阻塞/中断，prompt 通常已在服务端入队，
  // 此时不应判失败，继续轮询获取本轮结果
  try {
    await sendMessage(sessionId, prompt, model, baseUrl, password);
  } catch (err) {
    if (!/request timeout|terminated|aborted/i.test(err.message)) throw err;
  }

  const QUIET_MS = 8000;
  const POLL_MS = 5000;
  const deadline = submitTime + timeoutMs;

  while (Date.now() < deadline) {
    await sleep(POLL_MS);
    let msgs;
    try {
      msgs = await fetchMessages(sessionId, baseUrl, password);
    } catch { continue; } // 拉取失败（网络抖动）继续重试
    const list = Array.isArray(msgs) ? msgs : msgs?.data ?? [];
    // 倒序找提交之后创建的最新 assistant 消息
    for (let i = list.length - 1; i >= 0; i--) {
      const m = list[i];
      const info = m?.info ?? m;
      if (info?.role !== 'assistant') continue;
      const created = info.time?.created ?? 0;
      if (created < submitTime - 3000) return '(本轮未产生 assistant 回复)';
      // 模型调用出错时抛出异常，让任务正确判定为失败（而非误报成功）
      const apiErr = info.error ?? m?.error;
      if (apiErr) {
        const detail = apiErr.data?.message ?? apiErr.message ?? JSON.stringify(apiErr).slice(0, 300);
        throw new Error(`opencode 模型调用失败 (${apiErr.name}): ${detail}`.slice(0, 800));
      }
      const completed = info.time?.completed ?? 0;
      if (!completed) break; // 最新一轮还在跑，继续轮询
      if (Date.now() - completed > QUIET_MS) {
        // 已完成且静默 8s，提取文本
        const text = (m.parts ?? [])
          .filter(p => p.type === 'text' && p.text)
          .map(p => p.text)
          .join('\n')
          .trim();
        return text || '(assistant 回复无文本内容)';
      }
      break; // 完成但静默不足，继续等待确认
    }
  }
  throw new Error(`等待 AI 执行超时（${Math.round(timeoutMs / 1000)}s）`);
}

/** v2：提交 prompt 后轮询，直到本轮 idle（或模型报错） */
async function runPromptV2(sessionId, prompt, model, timeoutMs, baseUrl, password) {
  const submitTime = Date.now();
  try {
    await sendMessage(sessionId, prompt, model, baseUrl, password);
  } catch (err) {
    if (!/request timeout|terminated|aborted/i.test(err.message)) throw err;
  }

  const deadline = submitTime + timeoutMs;
  let text = '';

  while (Date.now() < deadline) {
    await sleep(V2_POLL_MS);
    let list;
    try {
      list = await fetchMessages(sessionId, baseUrl, password);
    } catch { continue; } // 网络抖动继续重试

    const recent = list.filter(m => (m?.info?.time?.created ?? 0) >= submitTime - 2000);

    // 模型/运行错误
    for (const m of recent) {
      const info = m?.info ?? {};
      const apiErr = info.error;
      if (apiErr) {
        const detail = apiErr.data?.message ?? apiErr.message ?? JSON.stringify(apiErr).slice(0, 300);
        throw new Error(`opencode 模型调用失败 (${apiErr.name}): ${detail}`.slice(0, 800));
      }
      if (info.type === 'assistant' && info.finish === 'error') {
        throw new Error(`opencode 模型调用失败: session=${sessionId}`.slice(0, 500));
      }
      if (info.type === 'idle' && info.outcome === 'failed') {
        throw new Error(`opencode 会话执行失败（idle outcome=failed）: session=${sessionId}`.slice(0, 500));
      }
    }

    // 汇总本轮所有 assistant 文本（v2 一步一条 assistant 消息）
    const collected = recent
      .filter(m => (m?.info?.type ?? m?.info?.role) === 'assistant')
      .map(m => (m.parts ?? [])
        .filter(p => p.type === 'text' && p.text)
        .map(p => p.text)
        .join(''))
      .join('\n')
      .trim();
    if (collected) text = collected;

    // 本轮 idle 已出现即视为执行结束
    const idle = recent
      .filter(m => m?.info?.type === 'idle')
      .sort((a, b) => (a.info.time?.created ?? 0) - (b.info.time?.created ?? 0))
      .pop();
    if (idle) return text || '(assistant 回复无文本内容)';
  }

  throw new Error(`等待 AI 执行超时（${Math.round(timeoutMs / 1000)}s）`);
}

/**
 * 拉取会话消息列表，统一成 v1 结构 [{info:{role,time,error,type,...}, parts:[...]}]，
 * 便于上层按同一套字段处理两种协议。
 */
async function fetchMessages(sessionId, baseUrl, password) {
  const version = await detectVersion(baseUrl, password);

  if (version === 'v2') {
    const res = await request(`/api/session/${encodeURIComponent(sessionId)}/message?order=desc&limit=50`, {}, 30_000, baseUrl, password);
    const raw = Array.isArray(res) ? res : (res?.data ?? []);
    return raw.map(toV1Message);
  }

  const res = await request(`/session/${encodeURIComponent(sessionId)}/message`, {}, 30_000, baseUrl, password);
  return Array.isArray(res) ? res : (res?.data ?? []);
}

/** v2 消息 → v1 结构（保留原始 type/outcome 供 idle 判定） */
function toV1Message(m) {
  const type = m?.type ?? m?.info?.role ?? 'assistant';
  const content = Array.isArray(m?.content) ? m.content : (m?.parts ?? []);
  return {
    info: {
      ...(m?.info ?? {}),
      id: m?.id ?? m?.info?.id,
      role: type === 'user' ? 'user' : 'assistant',
      type,
      finish: m?.finish ?? m?.info?.finish,
      outcome: m?.outcome ?? m?.info?.outcome,
      error: m?.error ?? m?.info?.error,
      time: m?.time ?? m?.info?.time ?? {},
    },
    parts: content,
  };
}

/** 拉取会话消息，提取最后一轮 assistant 文本 */
export async function fetchLastAssistantText(sessionId, baseUrl, password) {
  const list = await fetchMessages(sessionId, baseUrl, password);
  for (let i = list.length - 1; i >= 0; i--) {
    const m = list[i];
    const info = m?.info ?? m;
    if (info?.role !== 'assistant') continue;
    // 模型调用出错时抛出异常，让任务正确判定为失败（而非误报成功）
    const apiErr = info.error ?? m?.error;
    if (apiErr) {
      const detail = apiErr.data?.message ?? apiErr.message ?? JSON.stringify(apiErr).slice(0, 300);
      throw new Error(`opencode 模型调用失败 (${apiErr.name}): ${detail}`.slice(0, 800));
    }
    const text = (m.parts ?? [])
      .filter(p => p.type === 'text' && p.text)
      .map(p => p.text)
      .join('\n')
      .trim();
    if (text) return text;
  }
  return '(未提取到 assistant 回复文本)';
}

/**
 * opencode server 健康检查（baseUrl 指定目标实例，缺省为默认实例）。
 * 关键：v2 的 SPA 会对任意路径返回 HTML 200，因此必须校验响应体为 JSON，
 * 不能仅凭 2xx 判定健康。v2 返回 401/403 说明服务在线但缺密码，仍视为可达。
 */
export async function ping(baseUrl, password) {
  try {
    const version = await detectVersion(baseUrl, password);
    if (version === 'v2') {
      const res = await rawRequest('/api/info', {}, 5_000, baseUrl, password);
      return res.ok || res.status === 401 || res.status === 403;
    }
    const res = await rawRequest('/session?limit=1', {}, 5_000, baseUrl, password);
    return res.ok && isJsonBody(res.body);
  } catch {
    return false;
  }
}

// opencode Server HTTP 客户端
// 负责会话管理、prompt 提交、SSE 事件监听与最终结果提取
import { config } from './config.js';

// 所有函数支持传入目标实例 baseUrl（多实例路由）；缺省使用全局默认实例
const normalize = base => String(base ?? config.opencodeBaseUrl).replace(/\/+$/, '');

async function request(pathname, options = {}, timeoutMs = 30_000, baseUrl) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(new Error(`request timeout: ${pathname}`)), timeoutMs);
  try {
    const res = await fetch(normalize(baseUrl) + pathname, { ...options, signal: ctrl.signal });
    const text = await res.text();
    let body = null;
    try { body = text ? JSON.parse(text) : null; } catch { body = text; }
    if (!res.ok) {
      const err = new Error(`opencode API ${res.status}: ${typeof body === 'string' ? body.slice(0, 500) : JSON.stringify(body)?.slice(0, 500)}`);
      err.status = res.status;
      throw err;
    }
    return body;
  } finally {
    clearTimeout(timer);
  }
}

/** 会话是否存在 */
/** 会话是否存在（baseUrl 指定目标实例） */
export async function sessionExists(sessionId, baseUrl) {
  if (!sessionId) return false;
  try {
    await request(`/session/${sessionId}`, {}, 10_000, baseUrl);
    return true;
  } catch (err) {
    if (err.status === 404) return false;
    throw err; // 网络等问题不当作"会话不存在"
  }
}

/** 新建会话 */
export async function createSession(title, baseUrl) {
  const body = { title: title?.slice(0, 80) || 'opencode-scheduler' };
  if (process.env.OPENCODE_DIRECTORY) body.directory = process.env.OPENCODE_DIRECTORY;
  const res = await request('/session', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }, 30_000, baseUrl);
  return res?.id ?? res?.data?.id;
}

/** 向会话发送消息（触发 agent 执行），返回响应 */
export async function sendMessage(sessionId, text, model, baseUrl) {
  const body = { parts: [{ type: 'text', text }] };
  // model 支持 "provider/model-id" 字符串或 {providerID, modelID} 对象
  if (model) {
    body.model = typeof model === 'string'
      ? (() => {
          const [providerID, ...rest] = model.split('/');
          return { providerID, modelID: rest.join('/') };
        })()
      : model;
  }
  return request(`/session/${sessionId}/message`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }, 15_000, baseUrl);
}

/**
 * 提交 prompt 并等待本轮 agent 执行完成，返回最终 assistant 文本。
 * 采用轮询判定（SSE 长连接不稳定，易中途断开）：
 * 每 5s 拉取会话消息，找到提交后创建的 assistant 消息，
 * 其已完成且静默超过 8s（无新消息产生）即认为本轮执行结束。
 */
export async function runPromptAndWait(sessionId, prompt, model, timeoutMs = config.aiTimeoutMs, baseUrl) {
  const submitTime = Date.now();
  // 提交 prompt：若会话繁忙导致 POST 阻塞/中断，prompt 通常已在服务端入队，
  // 此时不应判失败，继续轮询获取本轮结果
  try {
    await sendMessage(sessionId, prompt, model, baseUrl);
  } catch (err) {
    if (!/request timeout|terminated|aborted/i.test(err.message)) throw err;
  }

  const QUIET_MS = 8000;
  const POLL_MS = 5000;
  const deadline = submitTime + timeoutMs;

  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, POLL_MS));
    let msgs;
    try {
      msgs = await fetchMessages(sessionId, baseUrl);
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

/** 拉取会话消息列表 */
async function fetchMessages(sessionId, baseUrl) {
  return request(`/session/${sessionId}/message`, {}, 30_000, baseUrl);
}

/** 拉取会话消息，提取最后一轮 assistant 文本 */
export async function fetchLastAssistantText(sessionId, baseUrl) {
  const msgs = await request(`/session/${sessionId}/message`, {}, 30_000, baseUrl);
  const list = Array.isArray(msgs) ? msgs : msgs?.data ?? [];
  for (let i = list.length - 1; i >= 0; i--) {
    const m = list[i];
    const role = m?.info?.role ?? m?.role;
    if (role !== 'assistant') continue;
    // 模型调用出错时抛出异常，让任务正确判定为失败（而非误报成功）
    const apiErr = m?.info?.error ?? m?.error;
    if (apiErr) {
      const detail = apiErr.data?.message ?? apiErr.message ?? JSON.stringify(apiErr).slice(0, 300);
      throw new Error(`opencode 模型调用失败 (${apiErr.name}): ${detail}`.slice(0, 800));
    }
    const parts = m?.parts ?? [];
    const text = parts
      .filter(p => p.type === 'text' && p.text)
      .map(p => p.text)
      .join('\n')
      .trim();
    if (text) return text;
  }
  return '(未提取到 assistant 回复文本)';
}

/** opencode server 健康检查（baseUrl 指定目标实例，缺省为默认实例） */
export async function ping(baseUrl) {
  try {
    await request('/session?limit=1', {}, 5_000, baseUrl);
    return true;
  } catch {
    return false;
  }
}

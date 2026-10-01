// 实例服务：opencode 多实例注册（被动发现）、会话归属解析、健康检查
// 设计约定：
// - 注册来源是 agent 自报（instance_register 工具），scheduler 反向验证可达性
// - 归属优先级：任务显式指定 > session 绑定 > 遍历注册表探测 > 默认实例
// - 离线实例不删除记录（历史任务仍需路由信息），仅标记 offline
import { config } from './config.js';
import * as store from './store.js';
import { ping, sessionExists } from './opencode-client.js';

function fail(msg) { const e = new Error(msg); e.status = 400; throw e; }

/** 校验 baseUrl 格式并规范化（去尾部斜杠） */
function normalizeBaseUrl(input) {
  const url = String(input ?? '').trim().replace(/\/+$/, '');
  if (!/^https?:\/\/[\w.-]+(:\d+)?$/.test(url)) {
    fail(`baseUrl 格式无效: ${input}（应为 http(s)://ip:port）`);
  }
  return url;
}

/**
 * 注册/续期实例：agent 自报自己的 opencode server 地址与当前会话。
 * 反向验证：baseUrl 可达 且 sessionId 存在于该实例（防配错/谎报）。
 */
export async function registerInstance({ baseUrl, sessionId, name }) {
  const url = normalizeBaseUrl(baseUrl);

  if (!(await ping(url))) fail(`opencode 实例不可达: ${url}（请确认 ip:port 及防火墙）`);
  if (sessionId && !(await sessionExists(sessionId, url))) {
    fail(`会话 ${sessionId} 不存在于实例 ${url}，请检查 sessionId 是否为该实例的会话`);
  }

  const inst = store.upsertInstance({ baseUrl: url, name: name?.trim() || null });
  if (sessionId) store.bindSession(sessionId, inst.id);
  return store.updateInstance(inst.id, { status: 'online', last_seen_at: new Date().toISOString() });
}

/** 确保默认实例（全局 OPENCODE_BASE_URL）已注册，作为兜底路由 */
export async function ensureDefaultInstance() {
  if (!config.opencodeBaseUrl) return null;
  const existing = store.listInstances().find(i => i.base_url === config.opencodeBaseUrl.replace(/\/+$/, ''));
  if (existing) return existing;
  if (!(await ping(config.opencodeBaseUrl))) return null;
  return store.upsertInstance({ baseUrl: config.opencodeBaseUrl, name: 'default' });
}

/**
 * 解析会话归属的实例（被动发现的兜底探测）。
 * @returns {{instance: object, source: 'binding'|'probe'|'default'}|null}
 */
export async function resolveInstanceForSession(sessionId) {
  if (sessionId) {
    // 1. 绑定关系（注册时建立）
    const bound = store.getInstanceBySession(sessionId);
    if (bound && await sessionExists(sessionId, bound.base_url)) {
      return { instance: store.updateInstance(bound.id, { status: 'online', last_seen_at: new Date().toISOString() }), source: 'binding' };
    }
    // 2. 遍历注册表探测（绑定缺失/过期的兜底，防同一 agent 换实例后会话迁移）
    for (const inst of store.listInstances()) {
      if (await sessionExists(sessionId, inst.base_url)) {
        store.bindSession(sessionId, inst.id);
        return { instance: store.updateInstance(inst.id, { status: 'online', last_seen_at: new Date().toISOString() }), source: 'probe' };
      }
    }
  }
  // 3. 默认实例兜底（兼容未注册来源）
  const def = await ensureDefaultInstance();
  if (def && (!sessionId || await sessionExists(sessionId, def.base_url))) {
    return { instance: def, source: 'default' };
  }
  return null;
}

/** 按任务解析目标实例：显式指定 > 会话归属 */
export async function resolveInstanceForJob({ instanceBaseUrl, sessionId }) {
  if (instanceBaseUrl) {
    const url = normalizeBaseUrl(instanceBaseUrl);
    const inst = store.listInstances().find(i => i.base_url === url);
    if (!inst) fail(`实例 ${url} 未注册，请先由该实例的 agent 调用 instance_register`);
    return inst;
  }
  const resolved = await resolveInstanceForSession(sessionId);
  if (!resolved) {
    fail('无法归属 opencode 实例：请先由该实例的 agent 调用 instance_register（提供自身 ip:port 与当前 sessionId）');
  }
  return resolved.instance;
}

/** 执行前健康检查：实例离线时返回 false（failfast，等待恢复，不转移） */
export async function isInstanceAlive(instanceId) {
  const inst = store.getInstance(instanceId);
  if (!inst) return false;
  const alive = await ping(inst.base_url);
  store.updateInstance(inst.id, {
    status: alive ? 'online' : 'offline',
    ...(alive ? { last_seen_at: new Date().toISOString() } : {}),
  });
  return alive;
}

/** 实例列表（含被动活跃度判断：超过 OFFLINE_AFTER_MS 未见活跃标记为离线嫌疑） */
export async function listInstancesWithStatus() {
  return store.listInstances();
}

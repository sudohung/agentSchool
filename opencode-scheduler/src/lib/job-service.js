// 任务服务层：参数校验 + 业务操作，供 MCP 工具与 REST API 共用
import * as store from './store.js';
import { validateCron, computeNextRunAt, scheduleJobById, unscheduleJob } from '../scheduler.js';
import { fmtLocal } from './time-format.js';
import { resolveInstanceForJob } from './instance-service.js';

function fail(msg) { const e = new Error(msg); e.status = 400; throw e; }

function normalize(input) {
  const f = {
    name: input.name?.trim(),
    type: input.type,
    scheduleType: input.scheduleType ?? input.schedule_type,
    cronExpr: input.cronExpr ?? input.cron_expr ?? null,
    runAt: input.runAt ?? input.run_at ?? null,
    command: input.command ?? null,
    prompt: input.prompt ?? null,
    sessionId: input.sessionId ?? input.session_id ?? null,
    workdir: input.workdir ?? null,
    model: input.model ?? null,
    timeoutMs: input.timeoutMs ?? input.timeout_ms ?? null,
    maxRetries: input.maxRetries ?? input.max_retries ?? 1,
    feishuWebhook: input.feishuWebhook ?? input.feishu_webhook ?? null,
    instanceBaseUrl: input.instanceBaseUrl ?? input.instance_base_url ?? null,
    notifyOnSuccess: Boolean(input.notifyOnSuccess ?? input.notify_on_success ?? false),
  };
  // 校验
  if (!f.name) fail('name 不能为空');
  if (!['bash', 'ai'].includes(f.type)) fail("type 必须为 'bash' 或 'ai'");
  if (!['cron', 'once'].includes(f.scheduleType)) fail("schedule_type 必须为 'cron' 或 'once'");
  if (f.type === 'bash' && !f.command) fail('bash 任务必须提供 command');
  if (f.type === 'ai' && !f.prompt) fail('ai 任务必须提供 prompt');
  if (f.scheduleType === 'cron') {
    if (!f.cronExpr) fail('cron 任务必须提供 cronExpr（5 段标准表达式）');
    if (!validateCron(f.cronExpr)) fail(`cron 表达式无效: ${f.cronExpr}`);
  }
  if (f.scheduleType === 'once') {
    if (!f.runAt) fail('一次性任务必须提供 runAt（ISO 时间，如 2026-10-01T09:00:00+08:00）');
    if (Number.isNaN(new Date(f.runAt).getTime())) fail(`runAt 时间无效: ${f.runAt}`);
  }
  if (f.timeoutMs != null && (!Number.isFinite(f.timeoutMs) || f.timeoutMs < 1000)) {
    fail('timeout_ms 必须 >= 1000');
  }
  if (f.feishu_webhook && !/^https?:\/\//.test(f.feishu_webhook)) fail('feishuWebhook 必须是 http(s) URL');
  return f;
}

function toCamel(job) {
  if (!job) return null;
  return {
    id: job.id, name: job.name, type: job.type,
    scheduleType: job.schedule_type, cronExpr: job.cron_expr, runAt: job.run_at,
    command: job.command, prompt: job.prompt,
    sessionId: job.session_id, workdir: job.workdir, model: job.model,
    timeoutMs: job.timeout_ms, maxRetries: job.max_retries,
    feishuWebhook: job.feishu_webhook, notifyOnSuccess: !!job.notify_on_success,
    instanceId: job.instance_id,
    status: job.status, createdAt: job.created_at, updatedAt: job.updated_at,
    lastRunAt: job.last_run_at, nextRunAt: job.next_run_at, running: !!job.running,
  };
}

/** 追加本地时区展示字段（*Local），原始 ISO 字段保持不变以兼容编辑回填 */
function withLocalTimes(job) {
  if (!job) return null;
  const inst = job.instanceId ? store.getInstance(job.instanceId) : null;
  return {
    ...job,
    instanceName: inst?.name ?? null,
    instanceBaseUrl: inst?.base_url ?? null,
    runAtLocal: fmtLocal(job.runAt),
    nextRunAtLocal: fmtLocal(job.nextRunAt),
    lastRunAtLocal: fmtLocal(job.lastRunAt),
    createdAtLocal: fmtLocal(job.createdAt),
    updatedAtLocal: fmtLocal(job.updatedAt),
  };
}

/** 归属解析：显式 instanceBaseUrl > sessionId 绑定/探测 > 默认实例；失败即拒绝创建（failfast） */
async function attachInstance(fields, existing) {
  // 更新场景：未提供新的归属线索时保留原实例
  if (existing && !fields.instanceBaseUrl && fields.sessionId == null) return;
  const inst = await resolveInstanceForJob({
    instanceBaseUrl: fields.instanceBaseUrl,
    sessionId: fields.sessionId ?? existing?.sessionId,
  });
  fields.instanceId = inst.id;
}

export const jobService = {
  async create(input) {
    const f = normalize(input);
    await attachInstance(f);
    const job = store.createJob(f);
    scheduleJobById(job.id);
    return withLocalTimes(toCamel(store.getJob(job.id)));
  },

  async update(id, input) {
    const existing = store.getJob(id);
    if (!existing) fail(`job not found: ${id}`);
    const merged = { ...toCamel(existing), ...input, id: undefined };
    const f = normalize(merged);
    await attachInstance(f, toCamel(existing));
    store.updateJob(id, f);
    scheduleJobById(id); // 重新注册调度
    return withLocalTimes(toCamel(store.getJob(id)));
  },

  get: id => withLocalTimes(toCamel(store.getJob(id))),

  list: () => store.listJobs().map(j => withLocalTimes(toCamel(j))),

  pause(id) {
    const job = store.getJob(id);
    if (!job) fail(`job not found: ${id}`);
    unscheduleJob(id);
    return withLocalTimes(toCamel(store.updateJob(id, { status: 'paused' })));
  },

  resume(id) {
    const job = store.getJob(id);
    if (!job) fail(`job not found: ${id}`);
    if (job.schedule_type === 'once' && job.status === 'completed') {
      fail('一次性任务已完成，无法恢复；请新建任务');
    }
    store.updateJob(id, { status: 'active' });
    scheduleJobById(id);
    return withLocalTimes(toCamel(store.getJob(id)));
  },

  remove(id) {
    const job = store.getJob(id);
    if (!job) fail(`job not found: ${id}`);
    unscheduleJob(id);
    store.deleteJob(id);
    return { deleted: true };
  },

  previewCron(expr) {
    if (!validateCron(expr)) fail(`cron 表达式无效: ${expr}`);
    return cronPreviewSafe(expr);
  },
};

function cronPreviewSafe(expr) {
  // 延迟引用避免循环依赖
  return import('../scheduler.js').then(m => m.cronPreview(expr));
}

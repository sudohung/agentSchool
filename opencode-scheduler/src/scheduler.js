// 调度引擎：cron 循环任务 + 一次性定时任务，含并发控制与错过执行补偿
import cron from 'node-cron';
import parser from 'cron-parser';
import { config } from './lib/config.js';
import * as store from './lib/store.js';
import { runBash } from './executors/bash.js';
import { runAiPrompt } from './executors/ai-prompt.js';
import { notifyJobResult } from './lib/notifier.js';

// jobId -> { cronTask?: node-cron task, timer?: NodeJS.Timeout }
const scheduled = new Map();
let runningCount = 0;

// ---------- cron 工具 ----------
export function validateCron(expr) {
  try { parser.parseExpression(expr, { tz: config.timezone }); return true; }
  catch { return false; }
}

/** 计算下次执行时间（cron），一次性任务返回 run_at */
export function computeNextRunAt(job) {
  if (job.schedule_type === 'once') return job.run_at;
  if (job.schedule_type === 'cron' && job.cron_expr && validateCron(job.cron_expr)) {
    try {
      const next = parser.parseExpression(job.cron_expr, { tz: config.timezone }).next();
      return next.toISOString();
    } catch { return null; }
  }
  return null;
}

/** cron 表达式未来 n 次执行时间（供表单预览） */
export function cronPreview(expr, n = 5) {
  if (!validateCron(expr)) return [];
  const out = [];
  const it = parser.parseExpression(expr, { tz: config.timezone });
  for (let i = 0; i < n; i++) out.push(it.next().toISOString());
  return out;
}

// ---------- 任务执行 ----------
async function executeJob(job, trigger = 'schedule') {
  // 重新读取最新任务定义，避免闭包中旧对象的状态（running 等）失真
  const fresh0 = store.getJob(job.id) ?? job;
  job = fresh0;
  console.log(`[job ${job.id}] 触发(${trigger}) type=${job.type} running=${job.running} 并发=${runningCount}/${config.maxConcurrency}`);
  if (job.running) {
    console.log(`[job ${job.id}] 跳过：上轮未完成`);
    store.insertExecution({ jobId: job.id, jobName: job.name, status: 'skipped',
      startedAt: new Date().toISOString(), error: '上轮任务尚未完成，本轮跳过' });
    return { skipped: true };
  }
  if (runningCount >= config.maxConcurrency) {
    store.insertExecution({ jobId: job.id, jobName: job.name, status: 'skipped',
      startedAt: new Date().toISOString(), error: `达到全局并发上限 ${config.maxConcurrency}` });
    return { skipped: true };
  }

  job.running = 1;
  runningCount++;
  store.updateJob(job.id, { running: true, last_run_at: new Date().toISOString() });
  const startedAt = new Date();

  let outcome;
  try {
    if (job.type === 'bash') {
      const r = await runBash(job.command, job.workdir || config.defaultWorkdir,
        job.timeout_ms ?? config.bashTimeoutMs);
      outcome = { status: r.ok ? 'success' : (r.timedOut ? 'timeout' : 'failed'),
        rawOutput: r.output, error: r.error };
    } else {
      const r = await runAiPrompt(job);
      outcome = { status: r.ok ? 'success' : (r.timedOut ? 'timeout' : 'failed'),
        rawOutput: r.output, error: r.error, sessionId: r.sessionId };
    }
  } catch (err) {
    outcome = { status: 'failed', rawOutput: '', error: err.message };
  } finally {
    runningCount--;
  }

  const finishedAt = new Date();
  const durationMs = finishedAt - startedAt;
  console.log(`[job ${job.id}] 执行完成 status=${outcome.status} 耗时=${durationMs}ms ${outcome.error ?? ''}`);

  // 3. 通知（会话回传 + 飞书）
  let notifyInfo = {};
  try {
    notifyInfo = await notifyJobResult({ job, ...outcome });
    console.log(`[job ${job.id}] 通知完成 session=${notifyInfo.sessionTarget} feishu=${notifyInfo.feishuSent} ${notifyInfo.feishuError ?? ''}`);
  } catch (err) {
    console.log(`[job ${job.id}] 通知异常: ${err.message}`);
    notifyInfo = { feishuError: `通知失败: ${err.message}` };
  }

  // 4. 落库
  const outputFile = notifyInfo.outputFile
    ?? (outcome.rawOutput && outcome.rawOutput.length > 200
      ? store.saveOutput(`job-${job.id}`, outcome.rawOutput) : null);
  store.insertExecution({
    jobId: job.id, jobName: job.name, status: outcome.status,
    startedAt: startedAt.toISOString(), finishedAt: finishedAt.toISOString(),
    durationMs, outputFile,
    outputSummary: (outcome.rawOutput ?? '').slice(0, 2000),
    error: outcome.error, sessionId: outcome.sessionId ?? notifyInfo.sessionTarget ?? null,
  });

  // 一次性任务执行完标记完成并注销
  const fresh = store.getJob(job.id);
  if (fresh && fresh.schedule_type === 'once') {
    store.updateJob(job.id, { status: 'completed', next_run_at: null, running: false });
    unschedule(job.id);
  } else if (fresh) {
    store.updateJob(job.id, { next_run_at: computeNextRunAt(fresh), running: false });
  }
  return { ...outcome, durationMs, notifyInfo };
}

// ---------- 注册/注销 ----------
function scheduleJob(job) {
  unschedule(job.id);
  if (job.status !== 'active') return;

  if (job.schedule_type === 'cron') {
    if (!validateCron(job.cron_expr)) return;
    const task = cron.schedule(job.cron_expr, () => executeJob(job), {
      timezone: config.timezone, name: job.id,
    });
    scheduled.set(job.id, { cronTask: task });
  } else if (job.schedule_type === 'once') {
    const delay = new Date(job.run_at).getTime() - Date.now();
    if (Number.isNaN(delay)) return;
    if (delay <= 1000) {
      // 错过执行：标记 missed 并通知，不执行过期任务
      store.updateJob(job.id, { status: 'completed', next_run_at: null });
      store.insertExecution({ jobId: job.id, jobName: job.name, status: 'missed',
        startedAt: job.run_at, error: '容器重启/调度器离线期间错过执行时间，已跳过' });
      notifyJobResult({ job, status: 'missed', rawOutput: '', error: '错过预定执行时间' }).catch(() => {});
      return;
    }
    armOnceTimer(job);
  }
  store.updateJob(job.id, { next_run_at: computeNextRunAt(job) });
}

// Node setTimeout 上限 2^31-1 ms（约 24.8 天），超长延迟需分段挂载
const MAX_TIMEOUT_MS = 2147483000;

function armOnceTimer(job) {
  const fire = () => {
    const fresh = store.getJob(job.id);
    if (!fresh || fresh.status !== 'active') return;
    const remaining = new Date(fresh.run_at).getTime() - Date.now();
    if (remaining > 1000) { armOnceTimer(fresh); return; } // 未到时间，继续分段等待
    executeJob(fresh);
  };
  const remaining = new Date(job.run_at).getTime() - Date.now();
  const delay = Math.max(Math.min(remaining, MAX_TIMEOUT_MS), 1000);
  const timer = setTimeout(fire, delay);
  timer.unref?.();
  scheduled.set(job.id, { timer });
}

function unschedule(jobId) {
  const entry = scheduled.get(jobId);
  if (!entry) return;
  entry.cronTask?.stop();
  if (entry.timer) clearTimeout(entry.timer);
  scheduled.delete(jobId);
}

// ---------- 对外 API ----------
export function scheduleJobById(jobId) {
  const job = store.getJob(jobId);
  if (job) scheduleJob(job);
}

export function unscheduleJob(jobId) {
  unschedule(jobId);
  store.updateJob(jobId, { next_run_at: null });
}

/** 手动触发一次（立即执行，不走调度） */
export async function triggerJob(jobId) {
  const job = store.getJob(jobId);
  if (!job) throw new Error(`job not found: ${jobId}`);
  return executeJob(job, 'manual');
}

/** 启动：加载所有任务；一次性任务做错过补偿；重置残留的 running 标志（容器重启后进程内状态丢失） */
export function startScheduler() {
  store.resetRunningFlags();
  for (const job of store.listJobs()) {
    if (job.schedule_type === 'once' && job.status === 'active') {
      const delay = new Date(job.run_at).getTime() - Date.now();
      if (delay <= 0) {
        scheduleJob(job); // 进入 missed 补偿分支
        continue;
      }
    }
    scheduleJob(job);
  }
  console.log(`[scheduler] 已加载 ${store.listJobs().length} 个任务，并发上限 ${config.maxConcurrency}`);
}

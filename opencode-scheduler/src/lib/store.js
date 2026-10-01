// 存储层：基于 node:sqlite（Node 22+ 内置，免原生编译）
import { DatabaseSync } from 'node:sqlite';
import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { config } from './config.js';

fs.mkdirSync(path.dirname(config.dbPath), { recursive: true });
fs.mkdirSync(config.outputDir, { recursive: true });

const db = new DatabaseSync(config.dbPath);
db.exec('PRAGMA journal_mode = WAL;');
db.exec(`
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,              -- bash | ai
  schedule_type TEXT NOT NULL,     -- cron | once
  cron_expr TEXT,
  run_at TEXT,                     -- ISO 时间，一次性任务
  command TEXT,                    -- bash 命令
  prompt TEXT,                     -- AI prompt
  session_id TEXT,                 -- 源 opencode 会话
  workdir TEXT,
  model TEXT,
  timeout_ms INTEGER,
  max_retries INTEGER DEFAULT 1,
  feishu_webhook TEXT,
  notify_on_success INTEGER DEFAULT 0,   -- 成功时是否通知（失败总是通知）
  status TEXT DEFAULT 'active',    -- active | paused
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_run_at TEXT,
  next_run_at TEXT,
  running INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS executions (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  job_name TEXT,
  status TEXT NOT NULL,            -- success | failed | timeout | skipped | missed
  started_at TEXT,
  finished_at TEXT,
  duration_ms INTEGER,
  output_file TEXT,                -- 完整输出落盘路径
  output_summary TEXT,
  error TEXT,
  session_id TEXT,                 -- 结果回传的会话
  retried INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS instances (
  id TEXT PRIMARY KEY,
  base_url TEXT NOT NULL UNIQUE,   -- opencode server 地址 ip:port
  name TEXT,                       -- 实例名称（可读标识）
  status TEXT DEFAULT 'online',    -- online | offline
  last_seen_at TEXT,               -- 最近一次活跃时间（注册/归属/健康检查刷新）
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS session_bindings (
  session_id TEXT PRIMARY KEY,     -- opencode 会话 ID
  instance_id TEXT NOT NULL,       -- 所属实例
  updated_at TEXT NOT NULL
);
`);

// 轻量迁移：已存在的库补齐新增列
function ensureColumn(table, column, ddl) {
  const cols = db.prepare(`PRAGMA table_info(${table})`).all().map(c => c.name);
  if (!cols.includes(column)) db.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${ddl}`);
}
ensureColumn('jobs', 'instance_id', 'TEXT'); // 任务归属的 opencode 实例

const nowIso = () => new Date().toISOString();

// ---------- job CRUD ----------
export function createJob(fields) {
  const id = randomUUID().slice(0, 8);
  const t = nowIso();
  db.prepare(`INSERT INTO jobs
    (id, name, type, schedule_type, cron_expr, run_at, command, prompt, session_id,
     workdir, model, timeout_ms, max_retries, feishu_webhook, notify_on_success,
     instance_id, status, created_at, updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).run(
    id, fields.name, fields.type, fields.scheduleType,
    fields.cronExpr ?? null, fields.runAt ?? null,
    fields.command ?? null, fields.prompt ?? null,
    fields.sessionId ?? null, fields.workdir ?? null, fields.model ?? null,
    fields.timeoutMs ?? null, fields.maxRetries ?? 1,
    fields.feishuWebhook ?? null, fields.notifyOnSuccess ? 1 : 0,
    fields.instanceId ?? null,
    'active', t, t);
  return getJob(id);
}

export function updateJob(id, fields) {
  const allowed = ['name', 'type', 'schedule_type', 'cron_expr', 'run_at', 'command',
    'prompt', 'session_id', 'workdir', 'model', 'timeout_ms', 'max_retries',
    'feishu_webhook', 'notify_on_success', 'status', 'next_run_at', 'last_run_at',
    'running', 'instance_id'];
  const sets = [], vals = [];
  for (const [k, v] of Object.entries(fields)) {
    const col = k.replace(/[A-Z]/g, c => '_' + c.toLowerCase());
    if (!allowed.includes(col)) continue;
    sets.push(`${col} = ?`);
    vals.push(typeof v === 'boolean' ? (v ? 1 : 0) : v);
  }
  if (!sets.length) return getJob(id);
  sets.push('updated_at = ?');
  vals.push(nowIso(), id);
  db.prepare(`UPDATE jobs SET ${sets.join(', ')} WHERE id = ?`).run(...vals);
  return getJob(id);
}

export function getJob(id) {
  return db.prepare('SELECT * FROM jobs WHERE id = ?').get(id) ?? null;
}

export function listJobs() {
  return db.prepare('SELECT * FROM jobs ORDER BY created_at DESC').all();
}

/** 启动时重置 running 标志：调度器进程重启后进程内执行状态已丢失 */
export function resetRunningFlags() {
  db.prepare('UPDATE jobs SET running = 0 WHERE running = 1').run();
}

export function deleteJob(id) {
  db.prepare('DELETE FROM jobs WHERE id = ?').run(id);
  db.prepare('DELETE FROM executions WHERE job_id = ?').run(id);
}

// ---------- execution 记录 ----------
export function insertExecution(rec) {
  const id = randomUUID().slice(0, 12);
  db.prepare(`INSERT INTO executions
    (id, job_id, job_name, status, started_at, finished_at, duration_ms,
     output_file, output_summary, error, session_id, retried)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).run(
    id, rec.jobId, rec.jobName ?? null, rec.status,
    rec.startedAt ?? null, rec.finishedAt ?? null, rec.durationMs ?? null,
    rec.outputFile ?? null, rec.outputSummary ?? null, rec.error ?? null,
    rec.sessionId ?? null, rec.retried ?? 0);
  return id;
}

export function listExecutions(jobId, limit = 50) {
  if (jobId) {
    return db.prepare('SELECT * FROM executions WHERE job_id = ? ORDER BY started_at DESC LIMIT ?').all(jobId, limit);
  }
  return db.prepare('SELECT * FROM executions ORDER BY started_at DESC LIMIT ?').all(limit);
}

export function saveOutput(name, content) {
  const file = path.join(config.outputDir, `${Date.now()}-${name.replace(/[^\w.-]/g, '_')}.log`);
  fs.writeFileSync(file, content);
  return file;
}

// ---------- instance 注册表 ----------
export function upsertInstance({ baseUrl, name, id }) {
  const t = nowIso();
  const existing = db.prepare('SELECT * FROM instances WHERE base_url = ?').get(baseUrl);
  if (existing) {
    if (name) db.prepare('UPDATE instances SET name = ?, updated_at = ? WHERE id = ?').run(name, t, existing.id);
    return getInstance(existing.id);
  }
  const instId = id ?? randomUUID().slice(0, 8);
  db.prepare(`INSERT INTO instances (id, base_url, name, status, last_seen_at, created_at, updated_at)
    VALUES (?,?,?,?,?,?,?)`).run(instId, baseUrl, name ?? null, 'online', t, t, t);
  return getInstance(instId);
}

export function getInstance(id) {
  return db.prepare('SELECT * FROM instances WHERE id = ?').get(id) ?? null;
}

export function listInstances() {
  return db.prepare('SELECT * FROM instances ORDER BY created_at ASC').all();
}

export function updateInstance(id, fields) {
  const allowed = ['name', 'status', 'last_seen_at'];
  const sets = [], vals = [];
  for (const [k, v] of Object.entries(fields)) {
    const col = k.replace(/[A-Z]/g, c => '_' + c.toLowerCase());
    if (!allowed.includes(col)) continue;
    sets.push(`${col} = ?`);
    vals.push(v);
  }
  if (!sets.length) return getInstance(id);
  sets.push('updated_at = ?');
  vals.push(nowIso(), id);
  db.prepare(`UPDATE instances SET ${sets.join(', ')} WHERE id = ?`).run(...vals);
  return getInstance(id);
}

// ---------- session ↔ instance 绑定 ----------
export function bindSession(sessionId, instanceId) {
  db.prepare(`INSERT INTO session_bindings (session_id, instance_id, updated_at)
    VALUES (?,?,?)
    ON CONFLICT(session_id) DO UPDATE SET instance_id = excluded.instance_id, updated_at = excluded.updated_at`)
    .run(sessionId, instanceId, nowIso());
}

export function getInstanceBySession(sessionId) {
  const row = db.prepare(`SELECT i.* FROM session_bindings b
    JOIN instances i ON i.id = b.instance_id WHERE b.session_id = ?`).get(sessionId);
  return row ?? null;
}

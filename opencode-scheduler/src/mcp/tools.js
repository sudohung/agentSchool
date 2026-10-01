// MCP 工具定义与执行逻辑（Streamable HTTP, JSON-RPC 2.0）
import { jobService } from '../lib/job-service.js';
import { triggerJob } from '../scheduler.js';
import { registerInstance, listInstancesWithStatus } from '../lib/instance-service.js';

const tool = (name, description, inputSchema, handler) => ({ name, description, inputSchema, handler });

const REGISTER_HINT = '【多实例注册】调用本服务前，agent 必须先调用 instance_register 注册自身所属的 opencode 实例（用 opencode-instance-discovery 技能获取本实例 ip:port，用 opencode-session-id 技能获取当前 sessionId）。';

export const tools = [
  tool('instance_register', '注册当前 agent 所属的 opencode 实例（被动发现）。agent 先自行获取本实例的 ip:port 与当前 sessionId，再调用本工具。注册后创建定时任务将自动路由回本实例（结果回传原会话）。', {
    type: 'object',
    required: ['baseUrl'],
    properties: {
      baseUrl: { type: 'string', description: '本实例的 opencode server 地址，如 http://10.1.2.3:4096' },
      sessionId: { type: 'string', description: '当前会话 ID（本次对话的 session id，用于验证并建立归属绑定）' },
      name: { type: 'string', description: '实例名称（可选，便于识别，如 dev-laptop-4096）' },
    },
  }, async args => JSON.stringify(await registerInstance(args), null, 2)),
  tool('job_add', `创建定时任务。支持 cron 循环任务与一次性定时任务；type=bash 执行 shell 命令，type=ai 向 opencode 提交 prompt 由 AI 执行并回传最终结果。\n【创建前必做】①${REGISTER_HINT}②sessionId 必须绑定：agent 必须先调用 opencode-session-id 技能脚本获取当前会话 ID 填入，否则用户在对话中收不到任务结果；③飞书通知（feishuWebhook）必须让用户明确决定是否使用，用户未表态时先询问，不得默认省略或替用户决定。`, {
    type: 'object',
    required: ['name', 'type', 'scheduleType'],
    properties: {
      name: { type: 'string', description: '任务名称' },
      type: { type: 'string', enum: ['bash', 'ai'], description: 'bash=执行命令; ai=提交 prompt 给 opencode 执行' },
      scheduleType: { type: 'string', enum: ['cron', 'once'] },
      cronExpr: { type: 'string', description: '5 段 cron 表达式，如 "0 9 * * 1-5"，scheduleType=cron 时必填' },
      runAt: { type: 'string', description: '一次性任务执行时间（ISO 格式，须含时区如 +08:00），scheduleType=once 时必填' },
      command: { type: 'string', description: 'type=bash 时必填：要执行的 shell 命令' },
      prompt: { type: 'string', description: 'type=ai 时必填：提交给 opencode 的提示词' },
      sessionId: { type: 'string', description: '【强制绑定】源 opencode 会话 ID，执行结果将回传该会话。agent 创建任务时必须先调用 opencode-session-id 技能脚本获取当前会话 ID 并填入此处，否则用户在对话中收不到结果；仅当用户明确不要回传会话时才可省略（结果将发到新建的独立会话）' },
      instanceBaseUrl: { type: 'string', description: '指定目标 opencode 实例地址（可选，仅当任务不绑定当前会话或需跨实例执行时填写，须为已注册实例）' },
      workdir: { type: 'string', description: 'bash 执行工作目录（默认 /workspace）' },
      model: { type: 'string', description: 'ai 任务覆盖模型，如 provider/model-id（可选，默认用 AI_DEFAULT_MODEL 环境变量）' },
      timeoutMs: { type: 'number', description: '执行超时毫秒数（bash 默认 300000，ai 默认 600000）' },
      maxRetries: { type: 'number', description: '失败重试次数，默认 1' },
      feishuWebhook: { type: 'string', description: '【用户必须明确决定】飞书机器人 webhook 地址。用户要求飞书通知时必须让用户提供 webhook 地址后填入；用户明确不要飞书通知时才可省略；不得替用户默认选择' },
      notifyOnSuccess: { type: 'boolean', description: '成功时是否也发通知（失败/超时总是通知），默认 false' },
    },
  }, async args => JSON.stringify(jobService.create(args), null, 2)),

  tool('job_list', '列出全部定时任务（含状态与下次执行时间）。时间为本地时区（Asia/Shanghai）格式：YYYY-MM-DD HH:mm:ss。', {
    type: 'object', properties: {},
    }, async () => {
    const jobs = jobService.list();
    return `${jobs.length} 个任务:\n${JSON.stringify(jobs.map(j => ({
      id: j.id, name: j.name, type: j.type, scheduleType: j.scheduleType,
      cronExpr: j.cronExpr, runAt: j.runAtLocal ?? j.runAt, status: j.status,
      nextRunAt: j.nextRunAtLocal ?? j.nextRunAt,
      instance: j.instanceName ? `${j.instanceName}(${j.instanceBaseUrl})` : j.instanceId,
      sessionId: j.sessionId,
    })), null, 2)}`;
  }),

  tool('instance_list', '列出已注册的 opencode 实例（含在线状态）。时间为本地时区（Asia/Shanghai）格式。', {
    type: 'object', properties: {},
  }, async () => {
    const list = await listInstancesWithStatus();
    return `${list.length} 个实例:\n${JSON.stringify(list.map(i => ({
      id: i.id, name: i.name, baseUrl: i.baseUrl, status: i.status,
      lastSeenAt: i.lastSeenAtLocal ?? i.lastSeenAt,
    })), null, 2)}`;
  }),

  tool('job_get', '查询单个任务详情。', {
    type: 'object', required: ['id'], properties: { id: { type: 'string' } },
  }, async ({ id }) => JSON.stringify(jobService.get(id), null, 2)),

  tool('job_pause', '暂停任务（不再调度执行）。', {
    type: 'object', required: ['id'], properties: { id: { type: 'string' } },
  }, async ({ id }) => JSON.stringify(jobService.pause(id), null, 2)),

  tool('job_resume', '恢复暂停的任务。', {
    type: 'object', required: ['id'], properties: { id: { type: 'string' } },
  }, async ({ id }) => JSON.stringify(jobService.resume(id), null, 2)),

  tool('job_delete', '删除任务及其执行历史。', {
    type: 'object', required: ['id'], properties: { id: { type: 'string' } },
  }, async ({ id }) => JSON.stringify(jobService.remove(id), null, 2)),

  tool('job_run', '手动立即触发一次任务执行（不影响调度计划），返回执行结果摘要。', {
    type: 'object', required: ['id'], properties: { id: { type: 'string' } },
  }, async ({ id }) => {
    const r = await triggerJob(id);
    return JSON.stringify({ status: r.status ?? (r.skipped ? 'skipped' : 'done'), durationMs: r.durationMs,
      output: (r.rawOutput ?? '').slice(0, 4000), error: r.error ?? null, notifyInfo: r.notifyInfo }, null, 2);
  }),
];

/** 执行 tools/call */
export async function callTool(name, args) {
  const t = tools.find(x => x.name === name);
  if (!t) throw new Error(`unknown tool: ${name}`);
  const text = await t.handler(args ?? {});
  return { content: [{ type: 'text', text }], isError: false };
}

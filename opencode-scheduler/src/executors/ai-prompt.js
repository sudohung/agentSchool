// AI-prompt 执行器：向任务归属的 opencode 实例提交 prompt，等待 agent 执行完成并提取最终结果
// 多实例约定：路由按 job.instance_id（创建时归属解析）；实例离线 failfast，不转移，等待恢复
import { config } from '../lib/config.js';
import * as store from '../lib/store.js';
import { isInstanceAlive } from '../lib/instance-service.js';
import { sessionExists, createSession, runPromptAndWait } from '../lib/opencode-client.js';

/**
 * 执行 AI 任务。
 * @param {object} job 任务记录
 * @returns {Promise<{ok: boolean, output: string, error: string|null, sessionId: string|null, timedOut: boolean}>}
 */
export async function runAiPrompt(job) {
  const timeoutMs = job.timeout_ms ?? config.aiTimeoutMs;

  // 0. failfast：目标实例健康检查，离线则直接失败并通知，等待下轮调度恢复
  const instance = job.instance_id ? store.getInstance(job.instance_id) : null;
  if (job.instance_id && !instance) {
    return { ok: false, output: '', error: `任务归属实例已不存在 (instance_id=${job.instance_id})`, sessionId: job.session_id, timedOut: false };
  }
  if (instance && !(await isInstanceAlive(instance.id))) {
    return { ok: false, output: '', error: `opencode 实例不可达 (${instance.name ? instance.name + ' ' : ''}${instance.base_url})，failfast 跳过本轮，等待实例恢复`, sessionId: job.session_id, timedOut: false };
  }
  const baseUrl = instance?.base_url;

  // 1. 确定目标会话：优先源会话，失效则新建
  let sessionId = job.session_id;
  if (sessionId && await sessionExists(sessionId, baseUrl)) {
    // 复用源会话
  } else {
    sessionId = await createSession(`定时 AI 任务: ${job.name}`, baseUrl);
  }

  // 2. 提交 prompt 并等待最终结果
  const prompt = [
    `[opencode-scheduler 定时任务触发]`,
    `任务名称: ${job.name}`,
    '',
    job.prompt,
  ].join('\n');

  try {
    const model = job.model || config.aiDefaultModel || undefined;
    const result = await runPromptAndWait(sessionId, prompt, model, timeoutMs, baseUrl);
    return { ok: true, output: result, error: null, sessionId, timedOut: false };
  } catch (err) {
    const timedOut = /超时/.test(err.message);
    return { ok: false, output: '', error: err.message, sessionId, timedOut };
  }
}

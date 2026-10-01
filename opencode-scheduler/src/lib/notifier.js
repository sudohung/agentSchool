// 通知器：优先回传 opencode 会话（会话不存在则新建），随后按配置触发飞书 webhook
// 多实例：会话回传打到任务归属实例的 baseUrl（结果会话只存在于该实例上）
import { config } from './config.js';
import * as store from './store.js';
import { sessionExists, createSession, sendMessage, ping } from './opencode-client.js';

// 组装通知文本
function buildMessage({ jobName, status, durationMs, summary, outputFile, error }) {
  const icon = status === 'success' ? '✅' : '❌';
  const lines = [
    `${icon} 定时任务通知 [${jobName}]`,
    `状态: ${status}${durationMs ? ` | 耗时: ${(durationMs / 1000).toFixed(1)}s` : ''}`,
  ];
  if (error) lines.push(`错误: ${String(error).slice(0, 500)}`);
  if (summary) {
    lines.push('', '--- 执行结果 ---', summary);
  }
  if (outputFile) lines.push('', `完整输出: ${outputFile}`);
  return lines.join('\n');
}

// 文本超过阈值时截断，完整内容落盘
function truncateForSession(text, jobId) {
  const bytes = Buffer.byteLength(text);
  if (bytes <= config.notifyMaxBytes) return { summary: text, outputFile: null };
  const file = store.saveOutput(`notify-${jobId}`, text);
  let cut = text.slice(0, config.notifyMaxBytes);
  // 避免截断在多字节字符中间
  while (Buffer.byteLength(cut) > config.notifyMaxBytes) cut = cut.slice(0, -1);
  return { summary: `${cut}\n...(内容过长已截断，完整输出见文件)`, outputFile: file };
}

/**
 * 发送任务结果通知。
 * @returns {{sessionTarget: string|null, sessionCreated: boolean, feishuSent: boolean, feishuError: string|null}}
 */
export async function notifyJobResult({ job, status, durationMs, rawOutput, error }) {
  const result = { sessionTarget: null, sessionCreated: false, feishuSent: false, feishuError: null };
  const shouldNotify = status !== 'success' || Boolean(job.notify_on_success);

  const { summary, outputFile } = truncateForSession(rawOutput ?? error ?? '', job.id);
  const text = buildMessage({ jobName: job.name, status, durationMs, summary, outputFile, error });

  if (!shouldNotify) return { ...result, outputFile };

  // AI 任务成功时：agent 的回复本身就在会话消息流里，无需再把结果作为消息发给 agent（避免多余的一轮触发）。
  // 仅失败/超时/missed 时才回传会话告知（此时会话里没有结果）。
  const skipSession = job.type === 'ai' && status === 'success';

  // 0. 会话回传必须路由到任务归属实例；实例离线时跳过会话回传（仍走飞书）
  const instance = job.instance_id ? store.getInstance(job.instance_id) : null;
  const baseUrl = instance?.base_url;
  const instanceDown = Boolean(instance) && !(await ping(baseUrl));

  // 1. 回传 opencode 会话（绑定会话发送失败时降级新建会话，确保结果可达）
  try {
    if (instanceDown) throw new Error(`opencode 实例不可达 (${baseUrl})，会话回传跳过`);
    let target = job.session_id;
    if (skipSession) {
      // 结果已在会话消息流中，只记录结果所在会话
      result.sessionTarget = job.session_id ?? null;
    } else if (target && await sessionExists(target, baseUrl)) {
      result.sessionCreated = false;
    } else {
      target = await createSession(`定时任务通知: ${job.name}`, baseUrl);
      result.sessionCreated = true;
    }
    if (target && !skipSession) {
      try {
        await sendMessage(target, text, undefined, baseUrl);
      } catch (sendErr) {
        // 绑定会话繁忙/不可达 → 新建会话兜底
        target = await createSession(`定时任务通知: ${job.name}`, baseUrl);
        await sendMessage(target, text, undefined, baseUrl);
        result.sessionCreated = true;
      }
      result.sessionTarget = target;
    }
  } catch (err) {
    result.sessionTarget = null;
    result.feishuError = `会话回传失败: ${err.message}`; // 暂存，随飞书通知一起说明
  }

  // 2. 飞书 webhook（10s 超时，避免挂死整个执行流程）
  if (job.feishu_webhook) {
    try {
      const res = await fetch(job.feishu_webhook, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          msg_type: 'text',
          content: { text: text + (result.sessionTarget ? `\n(会话: ${result.sessionTarget})` : '') },
        }),
        signal: AbortSignal.timeout(10_000),
      });
      result.feishuSent = res.ok;
      if (!res.ok) result.feishuError = `飞书 webhook 响应 ${res.status}`;
    } catch (err) {
      result.feishuSent = false;
      result.feishuError = `飞书 webhook 失败: ${err.message}`;
    }
  }

  return { ...result, outputFile };
}

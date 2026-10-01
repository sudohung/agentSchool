// 全局配置：环境变量优先，默认值兜底
import path from 'node:path';

const env = (key, def) => process.env[key] ?? def;

export const config = {
  // HTTP 服务端口（REST API + Web 管理页 + MCP 同端口）
  port: Number(env('PORT', 8080)),
  // 数据库文件路径
  dbPath: env('DB_PATH', path.join(process.cwd(), 'data', 'scheduler.db')),
  // opencode Server 地址
  opencodeBaseUrl: env('OPENCODE_BASE_URL', 'http://127.0.0.1:4096'),
  // AI 任务默认模型（job 未指定 model 时使用，格式 provider/model-id）
  aiDefaultModel: env('AI_DEFAULT_MODEL', ''),
  // AI 任务默认超时（毫秒）
  aiTimeoutMs: Number(env('AI_TIMEOUT_MS', 10 * 60 * 1000)),
  // bash 任务默认超时（毫秒）
  bashTimeoutMs: Number(env('BASH_TIMEOUT_MS', 5 * 60 * 1000)),
  // 全局并发上限
  maxConcurrency: Number(env('MAX_CONCURRENCY', 3)),
  // 回传会话的消息文本最大字节数，超过则截断并落盘完整输出
  notifyMaxBytes: Number(env('NOTIFY_MAX_BYTES', 8 * 1024)),
  // 完整输出落盘目录
  outputDir: env('OUTPUT_DIR', path.join(process.cwd(), 'data', 'outputs')),
  // 默认工作目录（bash 执行 & AI 会话 workspace）
  defaultWorkdir: env('DEFAULT_WORKDIR', '/workspace'),
  // 时区
  timezone: env('TZ', 'Asia/Shanghai'),
};

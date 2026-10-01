// 时间展示格式化：UTC ISO 字符串 → 本地时区（默认 Asia/Shanghai）可读字符串
// 存储层统一使用 UTC ISO（toISOString），仅展示层做时区转换
import { config } from './config.js';

const dtf = new Intl.DateTimeFormat('zh-CN', {
  timeZone: config.timezone,
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', second: '2-digit',
  hour12: false,
});

/** "2026-09-30T06:45:00.000Z" → "2026-09-30 14:45:00"（无效输入原样返回） */
export function fmtLocal(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const parts = {};
  for (const { type, value } of dtf.formatToParts(d)) parts[type] = value;
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`;
}

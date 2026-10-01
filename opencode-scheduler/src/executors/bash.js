// bash 执行器：子进程执行命令，捕获输出，超时保护
import { exec } from 'node:child_process';
import os from 'node:os';

/**
 * 执行 bash 命令。
 * @returns {Promise<{ok: boolean, output: string, error: string|null, timedOut: boolean}>}
 */
export function runBash(command, workdir, timeoutMs) {
  return new Promise(resolve => {
    const cwd = workdir && workdir.trim() ? workdir : os.tmpdir();
    const child = exec(command, {
      cwd,
      timeout: timeoutMs,
      maxBuffer: 10 * 1024 * 1024,
      shell: '/bin/bash',
      env: { ...process.env, TERM: 'dumb' },
    }, (err, stdout, stderr) => {
      const output = [stdout, stderr].filter(Boolean).join('\n').trim();
      if (err && err.killed) {
        resolve({ ok: false, output, error: `命令执行超时（${Math.round(timeoutMs / 1000)}s）`, timedOut: true });
      } else if (err) {
        resolve({ ok: false, output, error: `exit code ${err.code}: ${err.message.split('\n')[0]}`, timedOut: false });
      } else {
        resolve({ ok: true, output: output || '(无输出)', error: null, timedOut: false });
      }
    });
    // 防止句柄泄漏
    child.on('error', () => {});
  });
}

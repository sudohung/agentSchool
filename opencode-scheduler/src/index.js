// 入口：启动调度引擎 + HTTP 服务（MCP / REST / Web UI）
import { startScheduler } from './scheduler.js';
import { startHttpServer } from './http-server.js';

startScheduler();
startHttpServer();

// 兜底：任何遗漏 await 的异步拒绝只记日志，不允许打崩常驻调度进程
process.on('unhandledRejection', (err) => {
  console.error('[unhandledRejection]', err?.stack ?? err);
});

for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => {
    console.log(`[exit] 收到 ${sig}，退出`);
    process.exit(0);
  });
}

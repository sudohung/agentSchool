// 入口：启动调度引擎 + HTTP 服务（MCP / REST / Web UI）
import { startScheduler } from './scheduler.js';
import { startHttpServer } from './http-server.js';

startScheduler();
startHttpServer();

for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => {
    console.log(`[exit] 收到 ${sig}，退出`);
    process.exit(0);
  });
}

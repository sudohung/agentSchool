/**
 * 服务启动入口
 */

import { loadConfig } from './config.js';
import { createApp } from './http/server.js';
import { buildRouter } from './routes/api.js';
import { ChatStore } from './store/chat-store.js';
import { TokenService } from './auth/token.js';
import { AuthService } from './auth/auth-service.js';
import { EngineRegistry } from './opencode/engine-registry.js';
import { TurnRunner } from './chat/turn-runner.js';
import { AuthMode, LogPrefix } from './constants.js';

/**
 * 启动
 */
async function main() {
    const config = loadConfig();
    const store = new ChatStore(config.dataDir);
    const tokens = new TokenService(config.dataDir);
    const auth = new AuthService({ config, tokens, store });
    const engines = new EngineRegistry(config);
    const runner = new TurnRunner({ store, engines, config });
    const router = buildRouter({ config, auth, store, engines, runner });
    const server = createApp({ router });

    engines.start();

    server.listen(config.port, config.host, () => {
        console.log(`${LogPrefix.BOOT} 服务已启动 http://${config.host}:${config.port}`);
        console.log(`${LogPrefix.BOOT} 配置文件: ${config.configPath}`);
        console.log(`${LogPrefix.BOOT} 小程序 AppID: ${config.wechat.appId || '未配置'}`);
        console.log(`${LogPrefix.BOOT} 登录模式: ${auth.mode === AuthMode.DEV ? 'dev（按设备标识登录）' : 'wechat（code2session）'}`);
        if (auth.mode === AuthMode.WECHAT && auth.allowDevLogin) {
            console.warn(`${LogPrefix.BOOT} 已开启开发登录（allowDevLogin）：无 code 时按设备标识登录，生产环境请关闭`);
        }
        console.log(`${LogPrefix.BOOT} 默认引擎: ${engines.defaultKey}`);
        for (const [key, engine] of Object.entries(config.engines)) {
            console.log(`${LogPrefix.BOOT}   引擎 ${key}: ${engine.baseUrl} (${engine.version}) ${engine.directory ? `dir=${engine.directory}` : ''}`);
        }
    });

    /** 优雅退出：先停事件流，再把内存数据落盘 */
    const shutdown = async (signal) => {
        console.log(`${LogPrefix.BOOT} 收到 ${signal}，开始退出`);
        engines.stop();
        store.flush();
        server.close(() => process.exit(0));
        // 兜底：10 秒内没退干净就强制退出
        setTimeout(() => process.exit(0), 10000).unref();
    };
    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

    // 兜底捕获，避免未处理异常导致进程直接崩溃
    process.on('unhandledRejection', (reason) => {
        console.error(`${LogPrefix.BOOT} 未处理的 Promise 拒绝:`, reason);
    });
}

main().catch((error) => {
    console.error(`${LogPrefix.BOOT} 启动失败: ${error.stack || error.message}`);
    process.exit(1);
});
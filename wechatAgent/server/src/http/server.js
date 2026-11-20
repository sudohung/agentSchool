/**
 * HTTP 服务入口
 * 只做三件事：解析 URL、匹配路由、把异常统一转成错误响应
 */

import { createServer } from 'http';
import { sendError, httpError } from './respond.js';
import { ErrorCode, LogPrefix } from '../constants.js';

/** CORS 允许来源：小程序自身不发 Origin，这里兼容本地网页调试 */
const CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, PATCH, DELETE, OPTIONS',
};

/**
 * 创建并返回 http server
 * @param {{router:Object}} deps
 */
export function createApp({ router }) {
    const server = createServer(async (req, res) => {
        const started = Date.now();
        const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
        // 畸形百分号编码会让 decodeURIComponent 抛错，退化为原始路径
        let pathname;
        try {
            pathname = decodeURIComponent(url.pathname);
        } catch {
            pathname = url.pathname;
        }

        // 预检
        if (req.method === 'OPTIONS') {
            res.writeHead(204, CORS_HEADERS);
            res.end();
            return;
        }
        for (const [key, value] of Object.entries(CORS_HEADERS)) res.setHeader(key, value);

        // 客户端提前断开时，避免后续写操作抛 EPIPE 打崩进程
        res.on('error', () => {});

        const matched = router.match(req.method || 'GET', pathname);
        if (!matched) {
            sendError(res, httpError(404, ErrorCode.NOT_FOUND, `接口不存在: ${req.method} ${pathname}`));
            return;
        }

        try {
            await matched.handler({ req, res, params: matched.params, query: url.searchParams });
            logAccess(req, res, pathname, started);
        } catch (error) {
            logAccess(req, res, pathname, started, error);
            sendError(res, error);
        }
    });

    // 长连接场景下不要用 Node 默认 5s headers timeout 掐断
    server.headersTimeout = 65000;
    server.requestTimeout = 0;
    server.keepAliveTimeout = 65000;

    return server;
}

/**
 * 输出访问日志（流式接口在响应结束后才打印）
 * @param {import('http').IncomingMessage} req
 * @param {import('http').ServerResponse} res
 * @param {string} pathname
 * @param {number} started
 * @param {Error} [error]
 */
function logAccess(req, res, pathname, started, error) {
    const cost = Date.now() - started;
    const status = res.statusCode;
    const line = `${req.method} ${pathname} ${status} ${cost}ms`;
    if (error) {
        console.error(`${LogPrefix.HTTP} ${line} ERROR: ${error.message}`);
    } else if (cost > 3000) {
        console.log(`${LogPrefix.HTTP} ${line} (慢请求)`);
    } else {
        console.log(`${LogPrefix.HTTP} ${line}`);
    }
}
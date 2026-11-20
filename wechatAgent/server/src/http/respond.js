/**
 * 极简 HTTP 工具：请求体解析、JSON 响应、错误响应
 */

import { ErrorCode } from '../constants.js';

/** 单次请求体上限 1MB，防止异常大包 */
const MAX_BODY_BYTES = 1024 * 1024;

/**
 * 读取并解析 JSON 请求体
 * @param {import('http').IncomingMessage} req
 * @returns {Promise<Object>}
 */
export function readJsonBody(req) {
    return new Promise((resolve, reject) => {
        const chunks = [];
        let size = 0;
        req.on('data', (chunk) => {
            size += chunk.length;
            if (size > MAX_BODY_BYTES) {
                reject(Object.assign(new Error('请求体过大'), { code: ErrorCode.BAD_REQUEST, status: 413 }));
                req.destroy();
                return;
            }
            chunks.push(chunk);
        });
        req.on('end', () => {
            if (size === 0) return resolve({});
            const raw = Buffer.concat(chunks).toString('utf-8');
            try {
                resolve(JSON.parse(raw));
            } catch {
                reject(Object.assign(new Error('请求体不是合法 JSON'), { code: ErrorCode.BAD_REQUEST, status: 400 }));
            }
        });
        req.on('error', reject);
    });
}

/**
 * 输出 JSON 响应
 * @param {import('http').ServerResponse} res
 * @param {number} status
 * @param {any} payload
 */
export function sendJson(res, status, payload) {
    if (res.writableEnded) return;
    // 流式接口已经发过响应头，此时无法再改状态码，直接结束
    if (res.headersSent) {
        try {
            res.end();
        } catch {
            // 忽略
        }
        return;
    }
    const body = Buffer.from(JSON.stringify(payload), 'utf-8');
    res.writeHead(status, {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': body.length,
        'Cache-Control': 'no-store',
    });
    res.end(body);
}

/**
 * 输出统一错误结构
 * @param {import('http').ServerResponse} res
 * @param {Error & {status?:number, code?:string, details?:any}} error
 */
export function sendError(res, error) {
    const status = error?.status || 500;
    sendJson(res, status, {
        ok: false,
        error: {
            code: error?.code || ErrorCode.INTERNAL,
            message: error?.message || '服务内部错误',
            details: error?.details ?? null,
        },
    });
}

/**
 * 构造带状态码的业务错误
 * @param {number} status
 * @param {string} code
 * @param {string} message
 * @param {any} [details]
 */
export function httpError(status, code, message, details) {
    return Object.assign(new Error(message), { status, code, details });
}
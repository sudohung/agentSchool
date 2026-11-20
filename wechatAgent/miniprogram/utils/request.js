/**
 * HTTP 请求封装
 *  - 自动带 Bearer token
 *  - 统一错误结构解析
 *  - 401 自动清登录态
 */

const config = require('../config');
const storage = require('./storage');

/** 业务错误 */
class ApiError extends Error {
    constructor(message, code, status, details) {
        super(message);
        this.name = 'ApiError';
        this.code = code || 'INTERNAL';
        this.status = status || 0;
        this.details = details || null;
    }
}

/**
 * 拼完整地址
 * @param {string} path
 */
function url(path) {
    return path.startsWith('http') ? path : `${config.BASE_URL}${path}`;
}

/**
 * 统一处理响应
 * @param {Object} res wx.request 的 success 回调参数
 * @returns {*}
 */
function unwrap(res) {
    const { statusCode, data } = res;

    if (statusCode === 401) {
        storage.remove(storage.KEYS.TOKEN);
        storage.remove(storage.KEYS.USER);
    }

    const body = data && typeof data === 'object' ? data : null;
    if (statusCode >= 200 && statusCode < 300) {
        if (body && body.ok === false) {
            throw new ApiError(body.error?.message || '请求失败', body.error?.code, statusCode, body.error?.details);
        }
        return body;
    }

    throw new ApiError(
        body?.error?.message || `请求失败（HTTP ${statusCode}）`,
        body?.error?.code || 'HTTP_ERROR',
        statusCode,
        body?.error?.details
    );
}

/**
 * 发请求
 * @param {Object} options
 * @param {string} options.path
 * @param {string} [options.method]
 * @param {Object} [options.data]
 * @param {boolean} [options.auth]
 * @param {number} [options.timeout]
 * @returns {Promise<*>}
 */
function request({ path, method = 'GET', data, auth = true, timeout }) {
    return new Promise((resolve, reject) => {
        const header = { 'Content-Type': 'application/json' };
        if (auth) {
            const token = storage.get(storage.KEYS.TOKEN);
            if (token) header.Authorization = `Bearer ${token}`;
        }
        wx.request({
            url: url(path),
            method,
            data,
            header,
            timeout: timeout || 30000,
            success: (res) => {
                try {
                    resolve(unwrap(res));
                } catch (error) {
                    reject(error);
                }
            },
            fail: (error) => {
                reject(new ApiError(error.errMsg || '网络请求失败', 'NETWORK_ERROR', 0));
            },
        });
    });
}

module.exports = { request, ApiError, url };
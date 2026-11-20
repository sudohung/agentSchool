/**
 * 登录态管理
 *
 * 流程：
 *  1. 已存 token 且本地有用户 -> 直接返回
 *  2. 调 wx.login 拿 code（有 AppID 时有效）
 *  3. 调后端 /api/auth/login：后端有 AppID 走 code2session，没有则用 deviceId 走 dev 模式
 */

const config = require('../config');
const storage = require('./storage');
const { request } = require('./request');

/** 并发登录去重 */
let pending = null;

/**
 * 取 wx.login 的 code（失败返回空串）
 * @returns {Promise<string>}
 */
function wxLoginCode() {
    return new Promise((resolve) => {
        wx.login({
            success: (res) => resolve(res.code || ''),
            fail: () => resolve(''),
        });
    });
}

/**
 * 真正发起登录
 */
async function doLogin() {
    const code = await wxLoginCode();
    const result = await request({
        path: '/api/auth/login',
        method: 'POST',
        auth: false,
        data: {
            code,
            deviceId: storage.deviceId(),
        },
    });

    storage.set(storage.KEYS.TOKEN, result.token);
    storage.set(storage.KEYS.USER, result.user);
    return result;
}

/**
 * 确保已登录
 * @param {boolean} [force] 强制重新登录
 * @returns {Promise<{token:string,user:Object,mode:string}>}
 */
function ensureLogin(force = false) {
    const token = storage.get(storage.KEYS.TOKEN);
    const user = storage.get(storage.KEYS.USER);
    if (!force && token && user) {
        return Promise.resolve({ token, user, mode: '' });
    }

    if (pending) return pending;
    pending = doLogin().finally(() => {
        pending = null;
    });
    return pending;
}

/**
 * 登出
 */
function logout() {
    storage.remove(storage.KEYS.TOKEN);
    storage.remove(storage.KEYS.USER);
}

module.exports = { ensureLogin, logout, wxLoginCode };
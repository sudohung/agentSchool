/**
 * 本地存储封装
 */
const KEYS = {
    TOKEN: 'auth_token',
    USER: 'auth_user',
    DEVICE_ID: 'device_id',
    SESSIONS: 'cached_sessions',
    LAST_SESSION: 'last_session_id',
};

/**
 * 读取
 * @param {string} key
 * @param {*} fallback
 */
function get(key, fallback = null) {
    try {
        const value = wx.getStorageSync(key);
        return value === '' || value === undefined ? fallback : value;
    } catch (e) {
        return fallback;
    }
}

/**
 * 写入
 * @param {string} key
 * @param {*} value
 */
function set(key, value) {
    try {
        wx.setStorageSync(key, value);
    } catch (e) {
        // 存储失败不影响主流程
    }
}

/**
 * 删除
 * @param {string} key
 */
function remove(key) {
    try {
        wx.removeStorageSync(key);
    } catch (e) {
        // ignore
    }
}

/**
 * 获取/生成设备标识（dev 登录用，保证同一设备用户稳定）
 */
function deviceId() {
    let id = get(KEYS.DEVICE_ID);
    if (id) return id;
    id = `dev-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    set(KEYS.DEVICE_ID, id);
    return id;
}

module.exports = { KEYS, get, set, remove, deviceId };
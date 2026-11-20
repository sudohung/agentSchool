/**
 * 设置页：查看后端连接状态、登录模式、引擎健康
 */

const auth = require('../../utils/auth');
const storage = require('../../utils/storage');
const config = require('../../config');
const { request } = require('../../utils/request');

Page({
    data: {
        baseUrl: config.BASE_URL,
        loginMode: '',
        allowDevLogin: false,
        user: null,
        engines: [],
        healthOk: false,
        healthLoading: true,
        healthError: '',
    },

    onShow() {
        this.setData({ user: storage.get(storage.KEYS.USER) });
        this.checkHealth();
    },

    /**
     * 探测后端与引擎状态
     */
    async checkHealth() {
        this.setData({ healthLoading: true, healthError: '' });
        try {
            const res = await request({ path: '/api/health', auth: false, timeout: 15000 });
            this.setData({
                healthOk: Boolean(res.ok),
                loginMode: res.mode || '',
                allowDevLogin: Boolean(res.allowDevLogin),
                engines: (res.engines || []).map((item) => ({
                    ...item,
                    statusText: item.ok ? '在线' : '离线',
                })),
                healthLoading: false,
            });
        } catch (error) {
            this.setData({
                healthOk: false,
                healthLoading: false,
                healthError: error.message || '无法连接后端',
            });
        }
    },

    /**
     * 重新登录
     */
    async onRelogin() {
        wx.showLoading({ title: '登录中', mask: true });
        try {
            auth.logout();
            const result = await auth.ensureLogin(true);
            wx.hideLoading();
            wx.showToast({ title: '登录成功', icon: 'success' });
            this.setData({ user: result.user });
        } catch (error) {
            wx.hideLoading();
            wx.showToast({ title: error.message || '登录失败', icon: 'none' });
        }
    },

    /**
     * 复制后端地址，方便在开发者工具里核对
     */
    onCopyBaseUrl() {
        wx.setClipboardData({ data: config.BASE_URL });
    },
});
/**
 * 首页：会话列表
 */

const auth = require('../../utils/auth');
const storage = require('../../utils/storage');
const { request } = require('../../utils/request');

Page({
    data: {
        sessions: [],
        loading: true,
        error: '',
        engineLabel: '',
    },

    onShow() {
        this.loadSessions();
    },

    onPullDownRefresh() {
        this.loadSessions().finally(() => wx.stopPullDownRefresh());
    },

    /**
     * 加载会话列表
     */
    async loadSessions() {
        this.setData({ loading: true, error: '' });
        try {
            await auth.ensureLogin();
            const res = await request({ path: '/api/sessions' });
            this.setData({
                sessions: (res.sessions || []).map(formatSession),
                loading: false,
            });
        } catch (error) {
            this.setData({ loading: false, error: error.message || '加载失败' });
        }
    },

    /**
     * 新建对话
     */
    async onCreate() {
        wx.showLoading({ title: '创建中', mask: true });
        try {
            await auth.ensureLogin();
            const res = await request({
                path: '/api/sessions',
                method: 'POST',
                data: { title: '新的对话' },
            });
            wx.hideLoading();
            this.openChat(res.session.id);
        } catch (error) {
            wx.hideLoading();
            wx.showToast({ title: error.message || '创建失败', icon: 'none' });
        }
    },

    /**
     * 打开会话
     * @param {Object} e
     */
    onOpen(e) {
        this.openChat(e.currentTarget.dataset.id);
    },

    /**
     * @param {string} sessionId
     */
    openChat(sessionId) {
        storage.set(storage.KEYS.LAST_SESSION, sessionId);
        wx.navigateTo({ url: `/pages/chat/chat?id=${sessionId}` });
    },

    /**
     * 长按删除
     * @param {Object} e
     */
    onLongPress(e) {
        const { id, title } = e.currentTarget.dataset;
        wx.showModal({
            title: '删除对话',
            content: `确定删除「${title}」？删除后不可恢复。`,
            confirmColor: '#ff6b6b',
            success: async (res) => {
                if (!res.confirm) return;
                try {
                    await request({ path: `/api/sessions/${id}`, method: 'DELETE' });
                    this.loadSessions();
                } catch (error) {
                    wx.showToast({ title: error.message || '删除失败', icon: 'none' });
                }
            },
        });
    },

    /**
     * 打开设置
     */
    onSettings() {
        wx.navigateTo({ url: '/pages/settings/settings' });
    },
});

/**
 * 会话展示格式化
 * @param {Object} session
 */
function formatSession(session) {
    return {
        ...session,
        timeText: formatTime(session.updatedAt),
        preview: session.busy ? '生成中…' : `${session.messageCount} 条消息`,
    };
}

/**
 * 相对时间
 * @param {number} ts
 */
function formatTime(ts) {
    if (!ts) return '';
    const diff = Date.now() - ts;
    const minute = 60 * 1000;
    const hour = 60 * minute;
    const day = 24 * hour;

    if (diff < minute) return '刚刚';
    if (diff < hour) return `${Math.floor(diff / minute)} 分钟前`;
    if (diff < day) return `${Math.floor(diff / hour)} 小时前`;
    if (diff < 7 * day) return `${Math.floor(diff / day)} 天前`;

    const date = new Date(ts);
    return `${date.getMonth() + 1}月${date.getDate()}日`;
}
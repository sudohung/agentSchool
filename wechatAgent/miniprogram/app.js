/**
 * 小程序入口
 */

const auth = require('./utils/auth');

App({
    globalData: {
        user: null,
        loginMode: '',
        engines: [],
        models: [],
        defaultEngine: '',
    },

    onLaunch() {
        // 静默登录：有 token 直接可用，没有就发起一次登录
        auth.ensureLogin().catch(() => {
            // 登录失败由页面自己提示，这里不阻塞启动
        });
    },
});
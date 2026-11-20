/**
 * 小程序上传脚本（生成「开发版本」，之后在后台选为体验版）
 *
 * 用法：
 *   cd deploy && node upload.cjs [版本号] [版本描述]
 *
 * 前置条件：
 *   1. .keys/private.<appid>.key 已放好（后台「小程序代码上传」生成）
 *   2. 本机出口 IP 已加入后台 IP 白名单
 */

const ci = require('miniprogram-ci');
const path = require('path');
const fs = require('fs');

/** 项目根 = deploy 的上一级 */
const PROJECT_ROOT = path.resolve(__dirname, '..');
/** AppID 与私钥：私钥文件名固定带 AppID，便于校验 */
const APPID = 'wx7da1d84bfa65e857';
const KEY_PATH = path.join(PROJECT_ROOT, '.keys', `private.${APPID}.key`);

const VERSION = process.argv[2] || '0.1.0';
const DESC = process.argv[3] || '初版：会话列表 / 流式对话 / 设置';

/**
 * 上传前校验，避免报错信息晦涩
 */
function preflight() {
    if (!fs.existsSync(KEY_PATH)) {
        throw new Error(`找不到上传私钥：${KEY_PATH}\n请在小程序后台「开发 → 开发管理 → 开发设置 → 小程序代码上传」生成并下载。`);
    }
    if (!fs.existsSync(path.join(PROJECT_ROOT, 'project.config.json'))) {
        throw new Error('找不到 project.config.json，确认脚本位于 deploy/ 下');
    }
    const config = JSON.parse(fs.readFileSync(path.join(PROJECT_ROOT, 'project.config.json'), 'utf-8'));
    if (config.appid !== APPID) {
        throw new Error(`project.config.json 的 appid(${config.appid}) 与脚本不一致(${APPID})，请勿使用游客模式改过的配置`);
    }
}

(async () => {
    preflight();

    const project = new ci.Project({
        appid: APPID,
        type: 'miniProgram',
        projectPath: PROJECT_ROOT,
        privateKeyPath: KEY_PATH,
        ignores: [
            'node_modules/**/*',
            'deploy/**/*',
            'preview/**/*',
            'docs/**/*',
            '.keys/**/*',
            'server/**/*',
        ],
    });

    console.log(`[ci] 上传 ${APPID} v${VERSION}`);
    const result = await ci.upload({
        project,
        version: VERSION,
        desc: DESC,
        setting: { es6: true, minify: true, urlCheck: false },
        onProgressUpdate: (task) => {
            if (typeof task === 'string') return console.log('[进度]', task);
            if (task && task._msg) console.log('[进度]', task._msg, task._statusText || '');
        },
    });

    console.log('[ci] 上传成功');
    console.log(JSON.stringify(result, null, 2));
    console.log('\n下一步：小程序后台 → 管理 → 版本管理 → 找到刚上传的开发版本 → 「选为体验版」生成二维码。');
})().catch((err) => {
    const msg = err && err.message ? err.message : String(err);
    console.error('[ci] 上传失败:', msg);
    if (/invalid ip|ip not in whitelist/i.test(msg)) {
        console.error('  → 本机出口 IP 未加入后台 IP 白名单。');
    }
    if (/invalid credential|signature/i.test(msg)) {
        console.error('  → 私钥与 AppID 不匹配，或私钥已被重置。');
    }
    process.exit(1);
});
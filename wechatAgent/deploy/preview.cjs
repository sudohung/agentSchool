/**
 * 小程序预览二维码生成
 *
 * 与 upload.cjs 的区别：
 *   upload  → 生成「开发版本」，需在后台手动选为体验版
 *   preview → 直接生成二维码，扫码即可在微信里打开（面向开发者/体验成员）
 *
 * 用法：cd deploy && node preview.cjs
 */

const ci = require('miniprogram-ci');
const path = require('path');
const fs = require('fs');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const APPID = 'wx7da1d84bfa65e857';
const KEY_PATH = path.join(PROJECT_ROOT, '.keys', `private.${APPID}.key`);
const OUT_DIR = path.join(PROJECT_ROOT, 'deploy', 'out');

(async () => {
    if (!fs.existsSync(KEY_PATH)) throw new Error(`缺少私钥：${KEY_PATH}`);
    fs.mkdirSync(OUT_DIR, { recursive: true });

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

    console.log('[ci] 生成预览二维码…');
    const result = await ci.preview({
        project,
        desc: '预览：会话列表 / 流式对话 / 设置',
        // 关键：不校验合法域名，否则临时隧道域名会被拦
        setting: { es6: true, minify: false, urlCheck: false },
        qrcodeFormat: 'image',
        qrcodeOutputDest: path.join(OUT_DIR, 'qrcode.png'),
        onProgressUpdate: (task) => {
            if (typeof task === 'string') return console.log('[进度]', task);
            if (task && task._msg) console.log('[进度]', task._msg, task._statusText || '');
        },
    });

    console.log('[ci] 二维码已生成:', path.join(OUT_DIR, 'qrcode.png'));
    if (result && result.subPackageInfo) {
        console.log('[ci] 包大小:', JSON.stringify(result.subPackageInfo));
    }
})().catch((err) => {
    console.error('[ci] 预览失败:', err && err.message ? err.message : err);
    process.exit(1);
});
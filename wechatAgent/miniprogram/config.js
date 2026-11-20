/**
 * 全局配置
 * 修改 BASE_URL 指向你的后端服务：
 *  - 开发者工具调试：本机 IP + 端口，勾选「不校验合法域名」
 *  - 真机/正式版：必须是已备案的 HTTPS 域名（不能是 IP/localhost）
 *
 * 当前值是一条 cloudflared 临时隧道，仅供扫码试用：
 * 隧道进程重启后域名会失效，届时需更新此处并重新 preview / upload。
 * 正式上线请替换为自有已备案域名。
 */
const ENV = {
    /** 后端基址，末尾不要带斜杠 */
    BASE_URL: 'https://basics-mobiles-fleet-butler.trycloudflare.com',
    /** 请求超时（流式接口在 onChunkReceived 前的最长等待，不含流式过程） */
    REQUEST_TIMEOUT: 300000,
    /** 流式过程中多久没收到任何帧就认为断线 */
    STREAM_IDLE_TIMEOUT: 60000,
};

module.exports = ENV;
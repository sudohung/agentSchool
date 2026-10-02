/**
 * 全局 fetch 超时配置
 * 背景：OpenCode SDK 的 session.prompt 是阻塞式接口（完成后才返回响应头），
 * 而 Node 内置 fetch（undici）默认 headersTimeout/bodyTimeout = 300 秒，
 * 长推理任务（>5 分钟）会被客户端侧提前掐断（TypeError: fetch failed），
 * 服务端实际正常完成——表现为 OpenCode 端有回复、飞书端报"处理失败"。
 * 此处全局放开响应超时（连接超时保留 15s），对内置 fetch 生效（undici 共享全局 dispatcher 符号）。
 */

import { Agent, setGlobalDispatcher } from 'undici';

try {
    setGlobalDispatcher(new Agent({
        headersTimeout: 0,
        bodyTimeout: 0,
        connectTimeout: 15000,
    }));
    console.log('[FetchTimeout] 已配置全局 fetch 超时：响应等待不限时，连接超时 15s');
} catch (error) {
    console.warn(`[FetchTimeout] 全局 dispatcher 配置失败（长任务可能触发 300s 客户端超时）: ${error.message}`);
}

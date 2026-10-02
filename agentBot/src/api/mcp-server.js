/**
 * MCP Server（对外 Agent API 通道）
 * 协议：MCP Streamable HTTP（JSON-RPC 2.0 over HTTP POST，无状态模式，响应 application/json）
 * 职责：
 *  - 暴露 5 个工具：list_roles / apply_session / chat / get_result / close_session
 *  - 参数校验与统一错误包装（isError 标记）
 *  - 无新增依赖：自行实现 JSON-RPC 方法分发（initialize/tools/list/tools/call/ping）
 */

import { createServer } from 'http';
import { LogPrefix } from '../constants.js';

/** 请求体大小上限（字节） */
const BODY_LIMIT = 1024 * 1024;

/** JSON-RPC 标准错误码 */
const RPC_ERRORS = {
    PARSE_ERROR: -32700,
    INVALID_REQUEST: -32600,
    METHOD_NOT_FOUND: -32601,
    INVALID_PARAMS: -32602,
    INTERNAL_ERROR: -32603,
};

/** 支持的 MCP 协议版本（回显客户端版本，未提供时用最新稳定版） */
const DEFAULT_PROTOCOL_VERSION = '2025-03-26';

/** 工具定义（inputSchema 遵循 JSON Schema） */
function buildToolDefinitions() {
    return [
        {
            name: 'list_roles',
            description: '获取 agentBot 当前可用的职能列表。调用方按职能选择后用 apply_session 申请会话。',
            inputSchema: { type: 'object', properties: {}, required: [] },
        },
        {
            name: 'apply_session',
            description: '按职能申请一个 agentBot 会话。返回 callerSessionId，调用方必须保存并在后续 chat/close 时携带。可同时持有多个不同职能的会话。',
            inputSchema: {
                type: 'object',
                properties: {
                    role: { type: 'string', description: '职能 key（来自 list_roles）' },
                },
                required: ['role'],
            },
        },
        {
            name: 'chat',
            description: '向指定会话发送消息并获取回复。两种模式：①异步（默认，wait=false）：立即返回 taskId，用 get_result 轮询直到 done/failed/waiting_input——分析排查类长任务必须用此模式，且建议将「chat + 轮询」整体交给 subagent 任务执行，主会话不阻塞；②同步（wait=true）：最多等待 20 秒直接返回结果——适合极短任务，直接在当前会话调用即可，无需子 agent。注意：MCP 客户端工具调用通常有 30s 超时（超时报 -32001）。同一凭证的下一条消息在 agent 反问时会自动作为答案回传。',
            inputSchema: {
                type: 'object',
                properties: {
                    callerSessionId: { type: 'string', description: 'apply_session 返回的会话凭证' },
                    message: { type: 'string', description: '消息内容' },
                    wait: { type: 'boolean', description: '是否同步等待结果，默认 false（异步轮询）。长任务切勿设为 true' },
                    timeoutMs: { type: 'number', description: '同步等待超时毫秒数，仅 wait=true 时有效，上限 20000' },
                },
                required: ['callerSessionId', 'message'],
            },
        },
        {
            name: 'get_result',
            description: '查询任务结果（长轮询）：任务未完成时服务端最长等待 25s，完成后立即返回；超时未完成返回当前状态（pending/running），继续调用本接口即可。建议由 subagent 任务执行轮询，主会话无需阻塞等待。status: pending（排队/执行中）、waiting_input（agent 反问，见 question 字段）、done（见 reply 字段）、failed（见 error 字段）。优先用 taskId 查询；若同步调用时客户端超时（-32001）丢了 taskId，可直接传 callerSessionId 查询该会话最新任务。',
            inputSchema: {
                type: 'object',
                properties: {
                    taskId: { type: 'string', description: 'chat 异步模式返回的任务 ID（与 callerSessionId 二选一）' },
                    callerSessionId: { type: 'string', description: '会话凭证（taskId 丢失时的兜底查询，返回该会话最新任务）' },
                },
                required: [],
            },
        },
        {
            name: 'close_session',
            description: '主动释放会话凭证。释放后该凭证不可再用。',
            inputSchema: {
                type: 'object',
                properties: {
                    callerSessionId: { type: 'string', description: '要释放的会话凭证' },
                },
                required: ['callerSessionId'],
            },
        },
    ];
}

/**
 * MCP 服务类
 */
export class McpServer {
    /** @type {import('../agent/role-registry.js').RoleRegistry} */
    #roleRegistry;
    /** @type {import('./api-session-manager.js').ApiSessionManager} */
    #sessions;
    /** @type {import('./task-queue.js').TaskQueue} */
    #tasks;
    #port;

    /**
     * @param {Object} deps
     * @param {import('../agent/role-registry.js').RoleRegistry} deps.roleRegistry
     * @param {import('./api-session-manager.js').ApiSessionManager} deps.sessions
     * @param {import('./task-queue.js').TaskQueue} deps.tasks
     * @param {number} [deps.port]
     */
    constructor({ roleRegistry, sessions, tasks, port = 8082 }) {
        if (!roleRegistry || !sessions || !tasks) {
            throw new Error('McpServer 初始化失败：缺少依赖');
        }
        this.#roleRegistry = roleRegistry;
        this.#sessions = sessions;
        this.#tasks = tasks;
        this.#port = port;
    }

    /** 启动 HTTP 服务 */
    start() {
        const server = createServer((req, res) => {
            this.#route(req, res).catch((error) => {
                console.error(`${LogPrefix.MCP} 请求处理异常: ${error.message}`);
                this.#writeJson(res, 500, this.#rpcError(null, RPC_ERRORS.INTERNAL_ERROR, error.message));
            });
        });
        // 端口占用等启动失败只告警，不拖垮机器人主流程
        server.on('error', (error) => {
            console.error(`${LogPrefix.MCP} MCP 服务启动失败（机器人继续运行）: ${error.message}`);
        });
        server.listen(this.#port, () => {
            console.log(`${LogPrefix.MCP} MCP 服务已启动: http://0.0.0.0:${this.#port}/mcp`);
        });
    }

    /**
     * 路由分发
     */
    async #route(req, res) {
        const url = new URL(req.url, `http://localhost:${this.#port}`);
        if (url.pathname !== '/mcp') {
            return this.#writeJson(res, 404, { error: 'not found' });
        }

        // 仅支持 POST（无状态模式不提供 GET/SSE 流）
        if (req.method !== 'POST') {
            res.writeHead(405, { Allow: 'POST' });
            return res.end();
        }

        let body;
        try {
            body = await this.#readJson(req);
        } catch (error) {
            return this.#writeJson(res, 400, this.#rpcError(null, RPC_ERRORS.PARSE_ERROR, error.message));
        }

        // 批量请求（数组）逐条处理（MCP 规范支持批量）
        if (Array.isArray(body)) {
            const results = [];
            for (const item of body) {
                const out = await this.#handleRpc(item);
                if (out !== null) results.push(out);
            }
            return this.#writeJson(res, 200, results);
        }

        const result = await this.#handleRpc(body);
        // 通知类消息（无 id）无需响应体
        if (result === null) {
            res.writeHead(202);
            return res.end();
        }
        return this.#writeJson(res, 200, result);
    }

    /**
     * 处理单条 JSON-RPC 消息
     * @returns {Promise<Object|null>} null 表示通知消息无需响应
     */
    async #handleRpc(message) {
        if (!message || message.jsonrpc !== '2.0' || typeof message.method !== 'string') {
            return this.#rpcError(message?.id ?? null, RPC_ERRORS.INVALID_REQUEST, '无效的 JSON-RPC 请求');
        }
        const isNotification = message.id === undefined || message.id === null;

        try {
            switch (message.method) {
                case 'initialize':
                    return this.#rpcResult(message.id, {
                        protocolVersion: message.params?.protocolVersion || DEFAULT_PROTOCOL_VERSION,
                        capabilities: { tools: {} },
                        serverInfo: { name: 'agentBot', version: '1.1.0' },
                    });
                case 'notifications/initialized':
                case 'notifications/cancelled':
                    return null;
                case 'ping':
                    return this.#rpcResult(message.id, {});
                case 'tools/list':
                    return this.#rpcResult(message.id, { tools: buildToolDefinitions() });
                case 'tools/call':
                    return await this.#handleToolCall(message);
                default:
                    return isNotification
                        ? null
                        : this.#rpcError(message.id, RPC_ERRORS.METHOD_NOT_FOUND, `不支持的方法: ${message.method}`);
            }
        } catch (error) {
            console.error(`${LogPrefix.MCP} 方法执行失败 [${message.method}]: ${error.message}`);
            return isNotification
                ? null
                : this.#rpcError(message.id, RPC_ERRORS.INTERNAL_ERROR, error.message);
        }
    }

    /**
     * tools/call 分发到具体工具
     */
    async #handleToolCall(message) {
        const name = message.params?.name;
        const args = message.params?.arguments || {};

        let data;
        try {
            data = await this.#invokeTool(name, args);
        } catch (error) {
            console.warn(`${LogPrefix.MCP} 工具调用失败 [${name}]: ${error.message}`);
            return this.#rpcResult(message.id, {
                content: [{ type: 'text', text: JSON.stringify({ error: error.message }) }],
                isError: true,
            });
        }

        return this.#rpcResult(message.id, {
            content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
            isError: false,
        });
    }

    /**
     * 工具实现分发
     */
    async #invokeTool(name, args) {
        switch (name) {
            case 'list_roles': {
                return { roles: this.#roleRegistry.listRoles() };
            }
            case 'apply_session': {
                if (!args.role) throw new Error('缺少必填参数: role');
                return await this.#sessions.applySession(args.role);
            }
            case 'chat': {
                if (!args.callerSessionId) throw new Error('缺少必填参数: callerSessionId');
                if (!args.message) throw new Error('缺少必填参数: message');
                return await this.#tasks.submitChat(args.callerSessionId, args.message, {
                    wait: args.wait === true,
                    timeoutMs: args.timeoutMs,
                });
            }
            case 'get_result': {
                if (!args.taskId && !args.callerSessionId) {
                    throw new Error('taskId 与 callerSessionId 至少提供一个');
                }
                // taskId 优先；客户端同步超时（-32001）丢 taskId 时可凭证兜底找回
                return args.taskId
                    ? this.#tasks.getResult(args.taskId)
                    : this.#tasks.getResultByCredential(args.callerSessionId);
            }
            case 'close_session': {
                if (!args.callerSessionId) throw new Error('缺少必填参数: callerSessionId');
                const ok = this.#sessions.closeSession(args.callerSessionId);
                return { ok, closed: args.callerSessionId };
            }
            default:
                throw new Error(`未知工具: ${name}`);
        }
    }

    // ==================== 协议辅助 ====================

    #rpcResult(id, result) {
        return { jsonrpc: '2.0', id, result };
    }

    #rpcError(id, code, message) {
        return { jsonrpc: '2.0', id, error: { code, message } };
    }

    #writeJson(res, code, data) {
        res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify(data));
    }

    /**
     * 读取并解析 JSON 请求体
     */
    #readJson(req) {
        return new Promise((resolve, reject) => {
            let size = 0;
            const chunks = [];
            req.on('data', (c) => {
                size += c.length;
                if (size > BODY_LIMIT) {
                    reject(new Error('请求体过大'));
                    req.destroy();
                    return;
                }
                chunks.push(c);
            });
            req.on('end', () => {
                try {
                    resolve(JSON.parse(Buffer.concat(chunks).toString('utf-8')));
                } catch {
                    reject(new Error('无效的 JSON 请求体'));
                }
            });
            req.on('error', reject);
        });
    }
}

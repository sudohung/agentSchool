// MCP Streamable HTTP 端点处理（JSON-RPC 2.0）
import { tools, callTool } from './tools.js';

const SERVER_INFO = { name: 'opencode-scheduler', version: '1.0.0' };

function rpcResult(id, result) {
  return { jsonrpc: '2.0', id, result };
}
function rpcError(id, code, message) {
  return { jsonrpc: '2.0', id, error: { code, message } };
}

/**
 * 处理 POST /mcp 请求体，返回 {status, body, headers}
 */
export async function handleMcpRpc(body) {
  const { id, method, params } = body ?? {};
  switch (method) {
    case 'initialize':
      return {
        status: 200,
        body: rpcResult(id, {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          serverInfo: SERVER_INFO,
        }),
      };
    case 'notifications/initialized':
      return { status: 202, body: null };
    case 'ping':
      return { status: 200, body: rpcResult(id, {}) };
    case 'tools/list':
      return {
        status: 200,
        body: rpcResult(id, {
          tools: tools.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })),
        }),
      };
    case 'tools/call:': // 容错
    case 'tools/call': {
      try {
        const result = await callTool(params?.name, params?.arguments);
        return { status: 200, body: rpcResult(id, result) };
      } catch (err) {
        return {
          status: 200,
          body: rpcResult(id, {
            content: [{ type: 'text', text: `工具执行失败: ${err.message}` }],
            isError: true,
          }),
        };
      }
    }
    case undefined:
      return { status: 400, body: rpcError(null, -32600, 'invalid request: missing method') };
    default:
      return { status: 200, body: rpcError(id, -32601, `method not found: ${method}`) };
  }
}

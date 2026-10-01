// HTTP 服务：MCP 端点 + REST API + Web 管理页静态资源
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from './lib/config.js';
import { jobService } from './lib/job-service.js';
import { listExecutions, getJob } from './lib/store.js';
import { handleMcpRpc } from './mcp/server.js';
import { triggerJob, cronPreview, validateCron } from './scheduler.js';
import { ping as opencodePing } from './lib/opencode-client.js';
import { fmtLocal } from './lib/time-format.js';
import { listInstancesWithStatus } from './lib/instance-service.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = path.join(__dirname, '..', 'public');

function json(res, status, body) {
  const buf = Buffer.from(JSON.stringify(body ?? null));
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'content-length': buf.length });
  res.end(buf);
}

async function readBody(req, limit = 5 * 1024 * 1024) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw new Error('body too large');
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString('utf8');
}

async function handleApi(req, res, url) {
  const p = url.pathname;
  const method = req.method;

  if (p === '/api/health') {
    const oc = await opencodePing();
    return json(res, 200, { ok: true, opencode: oc ? 'connected' : 'unreachable' });
  }
  if (p === '/api/jobs' && method === 'GET') return json(res, 200, jobService.list());
  if (p === '/api/instances' && method === 'GET') {
    const list = await listInstancesWithStatus();
    return json(res, 200, list.map(i => ({
      ...i, lastSeenAtLocal: fmtLocal(i.last_seen_at),
      createdAtLocal: fmtLocal(i.created_at), updatedAtLocal: fmtLocal(i.updated_at),
    })));
  }
  if (p === '/api/jobs' && method === 'POST') {
    try { return json(res, 201, await jobService.create(JSON.parse(await readBody(req)))); }
    catch (err) { return json(res, err.status ?? 500, { error: err.message }); }
  }
  const m = p.match(/^\/api\/jobs\/([^/]+)(\/(run|pause|resume|executions))?$/);
  if (m) {
    const [, id, , action] = m;
    try {
      if (!action && method === 'GET') return json(res, 200, jobService.get(id));
        if (!action && (method === 'PUT' || method === 'PATCH')) {
          return json(res, 200, await jobService.update(id, JSON.parse(await readBody(req))));
        }
      if (!action && method === 'DELETE') return json(res, 200, jobService.remove(id));
      if (action === 'pause') return json(res, 200, jobService.pause(id));
      if (action === 'resume') return json(res, 200, jobService.resume(id));
      if (action === 'executions') return json(res, 200, listExecutions(id, 50));
      if (action === 'run' && method === 'POST') {
        const result = await triggerJob(id);
        return json(res, 200, {
          status: result.status ?? (result.skipped ? 'skipped' : 'done'),
          durationMs: result.durationMs ?? null,
          output: (result.rawOutput ?? '').slice(0, 4000),
          error: result.error ?? null,
          notifyInfo: result.notifyInfo ?? null,
        });
      }
    } catch (err) {
      if (err.message?.includes('not found')) return json(res, 404, { error: err.message });
      return json(res, err.status ?? 500, { error: err.message });
    }
  }
  if (p === '/api/executions' && method === 'GET') return json(res, 200, listExecutions(null, 100));
  if (p === '/api/cron/preview' && method === 'GET') {
    const expr = url.searchParams.get('expr') ?? '';
    if (!validateCron(expr)) return json(res, 400, { error: `cron 表达式无效: ${expr}` });
    return json(res, 200, { next: cronPreview(expr, 5).map(fmtLocal) });
  }
  return json(res, 404, { error: 'not found' });
}

function serveStatic(res, url) {
  let file = url.pathname === '/' ? 'index.html' : url.pathname.replace(/^\/+/, '');
  file = path.normalize(file).replace(/^(\.\.[/\\])+/, '');
  const full = path.join(PUBLIC_DIR, file);
  if (!full.startsWith(PUBLIC_DIR) || !fs.existsSync(full) || fs.statSync(full).isDirectory()) {
    // SPA 兜底
    const index = path.join(PUBLIC_DIR, 'index.html');
    if (fs.existsSync(index)) {
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      return res.end(fs.readFileSync(index));
    }
    res.writeHead(404); return res.end('not found');
  }
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png' };
  res.writeHead(200, { 'content-type': (types[path.extname(full)] ?? 'application/octet-stream') + '; charset=utf-8' });
  res.end(fs.readFileSync(full));
}

export function startHttpServer() {
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host ?? 'localhost'}`);
    try {
      if (url.pathname === '/mcp' && req.method === 'POST') {
        const raw = await readBody(req);
        let body;
        try { body = JSON.parse(raw || '{}'); } catch {
          return json(res, 400, { jsonrpc: '2.0', id: null, error: { code: -32700, message: 'parse error' } });
        }
        const { status, body: rpcBody } = await handleMcpRpc(body);
        if (status === 202 || rpcBody === null) { res.writeHead(202); return res.end(); }
        const buf = Buffer.from(JSON.stringify(rpcBody));
        res.writeHead(status, {
          'content-type': 'application/json; charset=utf-8',
          'content-length': buf.length,
          'mcp-session-id': req.headers['mcp-session-id'] ?? 'default',
        });
        return res.end(buf);
      }
      if (url.pathname.startsWith('/api/')) return await handleApi(req, res, url);
      return serveStatic(res, url);
    } catch (err) {
      console.error('[http]', err);
      if (!res.headersSent) json(res, 500, { error: err.message });
    }
  });
  server.listen(config.port, () => {
    console.log(`[http] 管理页: http://localhost:${config.port} | MCP: ${config.port}/mcp`);
  });
  return server;
}

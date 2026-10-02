/**
 * 配置管理服务（端口 8081）
 * 职责：
 *  - 提供配置页面（OpenCode 服务地址 + 模型列表管理）
 *  - REST API：读取/保存配置、热重载、重启服务
 *  - 保存配置后触发 AgentRegistry 热重载（模型立即生效）
 *  - 服务地址变更需要重启进程（Docker restart:always 自动拉起）
 */

import { createServer } from 'http';
import { BotConfig } from '../config/bot-config.js';
import { LogPrefix } from '../constants.js';

/** 请求体大小上限（字节） */
const BODY_LIMIT = 1024 * 1024;

/** 管理页 HTML（内联，无外部依赖） */
const ADMIN_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentBot 配置管理</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f6f8; color: #2c3e50; padding: 24px; }
  .wrap { max-width: 860px; margin: 0 auto; }
  h1 { font-size: 20px; margin-bottom: 4px; }
  .sub { color: #7f8c9b; font-size: 13px; margin-bottom: 20px; }
  .card { background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
  .card h2 { font-size: 15px; margin-bottom: 12px; color: #1a2733; }
  label { font-size: 13px; color: #5a6b7b; display: block; margin-bottom: 6px; }
  input[type=text], select { width: 100%; padding: 9px 12px; border: 1px solid #d5dce3; border-radius: 6px; font-size: 14px; }
  input:focus, select:focus { outline: none; border-color: #4a90d9; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; color: #5a6b7b; font-weight: 500; padding: 6px 8px; border-bottom: 2px solid #eef1f4; }
  td { padding: 6px 8px; border-bottom: 1px solid #f0f3f6; }
  td input { padding: 6px 10px; }
  .btn { padding: 9px 20px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
  .btn-primary { background: #2f6fed; color: #fff; }
  .btn-primary:hover { background: #2259c9; }
  .btn-del { background: #fdecec; color: #c0392b; padding: 5px 12px; font-size: 12px; }
  .btn-add { background: #eef4ff; color: #2f6fed; padding: 6px 14px; font-size: 13px; margin-top: 10px; }
  .row { display: flex; gap: 12px; align-items: flex-end; }
  .row > div { flex: 1; }
  .msg { margin-top: 12px; padding: 10px 14px; border-radius: 6px; font-size: 13px; display: none; }
  .msg-ok { background: #e8f7ee; color: #1e7e46; display: block; }
  .msg-err { background: #fdecec; color: #c0392b; display: block; }
  .meta { font-size: 12px; color: #95a5b3; margin-top: 8px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>🤖 agentBot 配置管理</h1>
  <div class="sub">修改模型配置保存后立即生效；修改 OpenCode 服务地址需重启服务（Docker 部署时自动重启）</div>

  <div class="card">
    <h2>OpenCode 服务</h2>
    <label>服务地址（Base URL）</label>
    <input type="text" id="baseUrl" placeholder="http://127.0.0.1:4096">
    <div style="margin-top:10px">
      <button class="btn btn-add" style="margin-top:0" onclick="fetchModels()">🔄 获取可用模型</button>
    </div>
    <div class="meta" id="meta"></div>
  </div>

  <datalist id="dl-provider"></datalist>

  <div class="card">
    <h2>Agent 模型列表</h2>
    <table id="tbl">
      <thead><tr><th style="width:14%">Key</th><th style="width:20%">Provider</th><th style="width:34%">Model</th><th style="width:26%">说明</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <button class="btn btn-add" onclick="addRow()">+ 添加模型</button>
    <div style="margin-top:14px">
      <label>默认 Agent（启动时使用）</label>
      <select id="defaultKey"></select>
    </div>
  </div>

  <div class="card">
    <h2>安全设置</h2>
    <label style="display:flex;align-items:center;gap:8px;font-size:14px;color:#2c3e50">
      <input type="checkbox" id="maskSensitive" style="width:auto"> 出站内容脱敏
    </label>
    <div class="meta">开启后：AI 回复/思考流/提问卡片中的路径、内网 IP、密钥等敏感信息自动过滤，并向 AI 注入行为约束。关闭后原文直接展示，存在泄漏风险。保存后立即生效</div>
  </div>

  <div class="card">
    <h2>OpenCode 实例注册表（Agent API 用）</h2>
    <table id="tblInst">
      <thead><tr><th style="width:18%">实例 Key</th><th style="width:34%">服务地址</th><th style="width:28%">项目目录（列表选择）</th><th style="width:10%"></th><th style="width:10%"></th></tr></thead>
      <tbody></tbody>
    </table>
    <button class="btn btn-add" onclick="addInstRow()">+ 添加实例</button>
    <div class="meta">职能可引用实例 Key；未指定实例的职能使用全局服务地址。项目目录必须从实例的项目列表中选择（点"选择目录"加载，选"(默认)"则归档到服务端默认目录），配置后该实例创建的会话会归档到对应项目下，可在 opencode UI 项目列表中看到。修改后需点击下方保存。</div>
  </div>

  <div class="card">
    <h2>Agent 职能列表（MCP 调用方按职能申请会话）</h2>
    <table id="tblRole">
      <thead><tr><th style="width:12%">Key</th><th style="width:12%">名称</th><th style="width:16%">说明</th><th style="width:22%">提示词</th><th style="width:10%">实例</th><th style="width:12%">模型</th><th style="width:8%">技能</th><th style="width:4%">只读</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <button class="btn btn-add" onclick="addRoleRow()">+ 添加职能</button>
    <div style="margin-top:14px"><button class="btn btn-primary" onclick="saveRoles()">💾 保存职能与实例</button></div>
    <div class="meta">实例/模型留空则使用全局配置；模型格式 provider/model；技能为逗号分隔的技能名；只读职能的权限请求将被自动拒绝。保存后立即生效。</div>
    <div class="msg" id="roleMsg"></div>
  </div>

  <div class="card">
    <div class="row">
      <div><button class="btn btn-primary" onclick="save()">💾 保存配置</button></div>
      <div style="flex:0"><button class="btn" style="background:#fff4e5;color:#b26a00" onclick="restart()">🔄 重启服务</button></div>
    </div>
    <div class="msg" id="msg"></div>
  </div>
</div>

<script>
const $ = (s) => document.querySelector(s);
let modelSeq = 0;
let MODEL_DATA = []; // [{id, name, models:[{id, name}]}]

function rowHtml(a = {}) {
  const tr = document.createElement('tr');
  const mkInputTd = (cls, val, listId) => {
    const td = document.createElement('td');
    const inp = document.createElement('input');
    inp.type = 'text'; inp.className = cls; inp.value = val || '';
    if (listId) inp.setAttribute('list', listId);
    td.appendChild(inp);
    return td;
  };
  tr.appendChild(mkInputTd('f-key', a.key));
  tr.appendChild(mkInputTd('f-provider', a.provider, 'dl-provider'));
  const dlId = 'dl-model-' + (++modelSeq);
  const tdModel = mkInputTd('f-model', a.model, dlId);
  const dl = document.createElement('datalist'); dl.id = dlId; tdModel.appendChild(dl);
  tr.appendChild(tdModel);
  tr.appendChild(mkInputTd('f-desc', a.description));
  const tdBtn = document.createElement('td');
  const btn = document.createElement('button');
  btn.className = 'btn btn-del'; btn.textContent = '删除';
  btn.onclick = () => { tr.remove(); refreshDefaultKey(); };
  tdBtn.appendChild(btn);
  tr.appendChild(tdBtn);
  return tr;
}

function addRow(a) {
  const tr = rowHtml(a);
  $('#tbl tbody').appendChild(tr);
  fillModelDatalist(tr);
  refreshDefaultKey();
}

/** 根据行内 provider 过滤该行 model 的可选项 */
function fillModelDatalist(tr) {
  const pid = tr.querySelector('.f-provider').value.trim();
  const match = MODEL_DATA.find(p => p.id === pid);
  const list = match ? match.models : MODEL_DATA.flatMap(p => p.models);
  tr.querySelector('datalist').innerHTML =
    list.map(m => '<option value="' + m.id + '">' + (m.name && m.name !== m.id ? m.name : '') + '</option>').join('');
}

function fillProviderDatalist() {
  $('#dl-provider').innerHTML = MODEL_DATA.map(p => '<option value="' + p.id + '">' + p.name + '</option>').join('');
}

/** 拉取指定 baseUrl 的可用 provider/模型列表，并刷新所有行的下拉选项 */
async function fetchModels() {
  const baseUrl = $('#baseUrl').value.trim();
  if (!(baseUrl.startsWith('http://') || baseUrl.startsWith('https://'))) { showMsg('请先输入以 http(s):// 开头的服务地址', false); return; }
  showMsg('正在从 ' + baseUrl + ' 获取可用模型...', true);
  try {
    const r = await fetch('/api/models?baseUrl=' + encodeURIComponent(baseUrl));
    const res = await r.json();
    if (!r.ok) { showMsg(res.error || ('获取失败: ' + r.status), false); return; }
    MODEL_DATA = res.providers || [];
    fillProviderDatalist();
    document.querySelectorAll('#tbl tbody tr').forEach(fillModelDatalist);
    const total = MODEL_DATA.reduce((n, p) => n + p.models.length, 0);
    showMsg('✅ 已获取 ' + MODEL_DATA.length + ' 个 provider / ' + total + ' 个模型，可在各行下拉选择', true);
  } catch (e) { showMsg('获取模型失败: ' + e.message, false); }
}

function refreshDefaultKey() {
  const cur = $('#defaultKey').value;
  $('#defaultKey').innerHTML = [...document.querySelectorAll('.f-key')].filter(i=>i.value.trim())
    .map(i => '<option ' + (i.value===cur?'selected':'') + '>' + i.value.trim() + '</option>').join('');
}
document.addEventListener('change', (e) => {
  if (e.target.classList.contains('f-key')) refreshDefaultKey();
  if (e.target.classList.contains('f-provider')) fillModelDatalist(e.target.closest('tr'));
});

function showMsg(text, ok) {
  const m = $('#msg');
  m.textContent = text;
  m.className = 'msg ' + (ok ? 'msg-ok' : 'msg-err');
  setTimeout(() => { m.className = 'msg'; }, 6000);
}

async function load() {
  try {
    const r = await fetch('/api/config');
    const cfg = await r.json();
    $('#baseUrl').value = cfg.opencodeBaseUrl || '';
    $('#meta').textContent = '飞书 App: ' + (cfg.feishuAppId ? cfg.feishuAppId.slice(0,8)+'...' : '未配置') + ' ｜ 配置来源: ' + (cfg.source||'-');
    $('#tbl tbody').innerHTML = '';
    (cfg.agents||[]).forEach(addRow);
    $('#defaultKey').value = cfg.defaultKey || 'main';
    $('#maskSensitive').checked = cfg.security ? cfg.security.maskSensitive !== false : true;
    // 页面打开即拉取当前 baseUrl 的可用模型，供下拉选择
    fetchModels();
    // 职能表的全局实例模型下拉依赖 baseUrl，就绪后刷新一次
    refreshAllRoleModels();
  } catch (e) { showMsg('加载失败: ' + e.message, false); }
}

async function save() {
  const rows = [...document.querySelectorAll('#tbl tbody tr')];
  if (rows.length === 0) { showMsg('至少需要配置一个 Agent', false); return; }
  const agents = [];
  const badRows = [];
  rows.forEach((tr, i) => {
    const a = {
      key: tr.querySelector('.f-key').value.trim(),
      provider: tr.querySelector('.f-provider').value.trim(),
      model: tr.querySelector('.f-model').value.trim(),
      description: tr.querySelector('.f-desc').value.trim(),
    };
    if (!a.key || !a.provider || !a.model) {
      badRows.push(i + 1);
      return;
    }
    agents.push(a);
  });
  if (badRows.length) {
    showMsg('保存失败：第 ' + badRows.join('、') + ' 行的 key/provider/model 未填完整，请补全或删除该行', false);
    return;
  }
  const body = {
    opencodeBaseUrl: $('#baseUrl').value.trim(),
    defaultKey: $('#defaultKey').value || agents[0]?.key,
    agents,
    security: { maskSensitive: $('#maskSensitive').checked },
  };
  try {
    const r = await fetch('/api/config', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
    const res = await r.json();
    if (!r.ok) { showMsg('保存失败: ' + (res.error||r.status), false); return; }
    if (res.urlChanged) {
      showMsg('✅ 已保存。服务地址已变更，3 秒后自动重启服务...', true);
      setTimeout(restart, 3000);
    } else {
      showMsg('✅ 已保存，模型配置已热生效（无需重启）', true);
    }
  } catch (e) { showMsg('保存失败: ' + e.message, false); }
}

async function restart() {
  try { await fetch('/api/restart', { method:'POST' }); showMsg('服务重启中，请稍后刷新页面...', true); }
  catch (e) { showMsg('重启请求已发送，若页面无响应请稍后刷新', true); }
}

// ==================== 职能与实例管理 ====================

function addInstRow(inst = {}) {
  const tr = document.createElement('tr');
  const mk = (cls, val) => {
    const td = document.createElement('td');
    const inp = document.createElement('input');
    inp.type = 'text'; inp.className = cls; inp.value = val || '';
    td.appendChild(inp); return td;
  };
  // 兼容两种配置：字符串（旧格式）或 {baseUrl, directory} 对象
  const baseUrl = typeof inst === 'string' ? inst : (inst.baseUrl || '');
  const directory = typeof inst === 'string' ? '' : (inst.directory || '');
  tr.appendChild(mk('i-key', inst.key));
  tr.appendChild(mk('i-url', baseUrl));
  // 目录下拉：必须从实例项目列表中选择（不允许自由输入），(默认) = 服务端默认目录
  const tdDir = document.createElement('td');
  const selDir = document.createElement('select');
  selDir.className = 'i-dir';
  selDir.innerHTML = '<option value="">(默认)</option>';
  if (directory) {
    // 已保存的目录先作为选项保留（列表加载后会被合并/覆盖）
    const opt = document.createElement('option');
    opt.value = directory; opt.textContent = directory;
    selDir.appendChild(opt);
    selDir.value = directory;
  }
  tdDir.appendChild(selDir);
  tr.appendChild(tdDir);
  const tdBtn = document.createElement('td');
  const btn = document.createElement('button');
  btn.className = 'btn btn-del'; btn.textContent = '删除';
  btn.onclick = () => tr.remove();
  tdBtn.appendChild(btn); tr.appendChild(tdBtn);
  $('#tblInst tbody').appendChild(tr);
  // 连通性检测按钮
  const tdCheck = document.createElement('td');
  const checkBtn = document.createElement('button');
  checkBtn.className = 'btn btn-add'; checkBtn.style.marginTop = '0';
  checkBtn.textContent = '测试连接';
  checkBtn.onclick = () => checkInstConnectivity(checkBtn);
  tdCheck.appendChild(checkBtn); tr.appendChild(tdCheck);
  // 可选目录加载按钮
  const tdDirBtn = document.createElement('td');
  const dirBtn = document.createElement('button');
  dirBtn.className = 'btn btn-add'; dirBtn.style.marginTop = '0';
  dirBtn.textContent = '选择目录';
  dirBtn.onclick = () => loadDirOptions(tr, false);
  tdDirBtn.appendChild(dirBtn); tr.appendChild(tdDirBtn);
}

// ==================== 实例可选目录（项目列表） ====================

/** 地址 -> 可选目录缓存 */
const DIR_CACHE = {};

/** 拉取（带缓存）实例的项目列表，填充目录下拉；silent=true 时不提示 */
async function loadDirOptions(tr, silent) {
  const baseUrl = tr.querySelector('.i-url').value.trim();
  if (!baseUrl) { if (!silent) showRoleMsg('请先填写该实例的服务地址', false); return; }
  if (!DIR_CACHE[baseUrl]) {
    try {
      const r = await fetch('/api/instance/projects?baseUrl=' + encodeURIComponent(baseUrl));
      const res = await r.json();
      if (!r.ok) { if (!silent) showRoleMsg('获取可选目录失败: ' + (res.error || r.status), false); return; }
      DIR_CACHE[baseUrl] = (res.projects || []).map(p => p.worktree);
    } catch (e) { if (!silent) showRoleMsg('获取可选目录失败: ' + e.message, false); return; }
  }
  const list = DIR_CACHE[baseUrl];
  const sel = tr.querySelector('.i-dir');
  const cur = sel.value;
  sel.innerHTML = '<option value="">(默认)</option>' +
    list.map(w => '<option value="' + w + '">' + w + '</option>').join('');
  // 已保存但不在项目列表中的目录保留为独立选项，避免配置丢失
  if (cur && !list.includes(cur)) {
    const opt = document.createElement('option');
    opt.value = cur; opt.textContent = cur + '（已保存）';
    sel.appendChild(opt);
  }
  sel.value = cur || '';
  if (!silent) showRoleMsg('✅ 已获取实例的 ' + list.length + ' 个可选目录，请从下拉选择', true);
}

/** 实例行目录为空时，自动用服务端默认目录填充（用户显式配置优先，不覆盖） */
async function autofillInstDirectory(tr) {
  const selDir = tr.querySelector('.i-dir');
  const baseUrl = tr.querySelector('.i-url').value.trim();
  if (!baseUrl || selDir.value) return;
  const dir = await fetchInstancePath(baseUrl);
  if (dir && !selDir.value) {
    if (![...selDir.options].some(o => o.value === dir)) {
      const opt = document.createElement('option');
      opt.value = dir; opt.textContent = dir + '（默认）';
      selDir.appendChild(opt);
    }
    selDir.value = dir;
  }
}

function addRoleRow(r = {}) {
  const tr = document.createElement('tr');
  const mk = (cls, val) => {
    const td = document.createElement('td');
    const inp = document.createElement('input');
    inp.type = 'text'; inp.className = cls; inp.value = val || '';
    td.appendChild(inp); return td;
  };
  tr.appendChild(mk('r-key', r.key));
  tr.appendChild(mk('r-name', r.name));
  tr.appendChild(mk('r-desc', r.desc));
  tr.appendChild(mk('r-prompt', r.prompt));
  const tdInst = document.createElement('td');
  const sel = document.createElement('select');
  sel.className = 'r-instance';
  sel.innerHTML = '<option value="">(全局)</option>';
  // 记住服务端已保存的实例选择（refreshInstanceOptions 回显时依赖 dataset.cur）
  sel.dataset.cur = r.instance || '';
  tdInst.appendChild(sel); tr.appendChild(tdInst);
  // 模型输入带 datalist：按所选实例动态填充可选模型（provider/model）
  const tdModel = document.createElement('td');
  const inpModel = document.createElement('input');
  inpModel.type = 'text'; inpModel.className = 'r-model'; inpModel.value = r.model || '';
  const dlModel = document.createElement('datalist');
  inpModel.setAttribute('list', 'dl-role-model-' + (++roleSeq));
  dlModel.id = 'dl-role-model-' + roleSeq;
  tdModel.appendChild(inpModel); tdModel.appendChild(dlModel);
  tr.appendChild(tdModel);
  tr.appendChild(mk('r-skills', (r.skills || []).join(',')));
  const tdRo = document.createElement('td');
  const ro = document.createElement('input');
  ro.type = 'checkbox'; ro.className = 'r-readonly'; ro.checked = r.readOnly === true;
  tdRo.appendChild(ro); tr.appendChild(tdRo);
  const tdBtn = document.createElement('td');
  const btn = document.createElement('button');
  btn.className = 'btn btn-del'; btn.textContent = '删除';
  btn.onclick = () => tr.remove();
  tdBtn.appendChild(btn); tr.appendChild(tdBtn);
  $('#tblRole tbody').appendChild(tr);
  refreshInstanceOptions();
  fillRoleModelDatalist(tr);
}

function refreshInstanceOptions() {
  const instKeys = [...document.querySelectorAll('.i-key')].map(i => i.value.trim()).filter(Boolean);
  document.querySelectorAll('#tblRole tbody tr').forEach(tr => {
    const sel = tr.querySelector('.r-instance');
    const cur = sel.value || sel.dataset.cur || '';
    sel.innerHTML = '<option value="">(全局)</option>' +
      instKeys.map(k => '<option ' + (k === cur ? 'selected' : '') + '>' + k + '</option>').join('');
    sel.dataset.cur = cur;
  });
}

/** 获取实例服务端默认目录（GET /path） */
async function fetchInstancePath(baseUrl) {
  try {
    const r = await fetch('/api/instance/path?baseUrl=' + encodeURIComponent(baseUrl));
    const res = await r.json();
    if (r.ok) return res.directory || '';
  } catch (e) { /* 实例不可达时忽略 */ }
  return '';
}

/** 实例连通性检测：拉取该实例的可用模型并提示结果，同时回填默认目录 */
async function checkInstConnectivity(btn) {
  const tr = btn.closest('tr');
  const baseUrl = tr.querySelector('.i-url').value.trim();
  const key = tr.querySelector('.i-key').value.trim() || baseUrl;
  if (!baseUrl) { showRoleMsg('该实例未填写服务地址', false); return; }
  btn.textContent = '检测中...';
  try {
    const r = await fetch('/api/models?baseUrl=' + encodeURIComponent(baseUrl));
    const res = await r.json();
    if (!r.ok) { showRoleMsg('❌ 实例 [' + key + '] 连接失败: ' + (res.error || r.status), false); return; }
    const total = (res.providers || []).reduce((n, p) => n + (p.models || []).length, 0);
    // 连接成功时顺带获取默认目录回填 + 刷新可选目录列表
    const dir = await fetchInstancePath(baseUrl);
    if (dir && !tr.querySelector('.i-dir').value.trim()) tr.querySelector('.i-dir').value = dir;
    await loadDirOptions(tr, true);
    showRoleMsg('✅ 实例 [' + key + '] 连接正常，可用模型 ' + total + ' 个，默认目录: ' + (dir || '未知'), true);
  } catch (e) {
    showRoleMsg('❌ 实例 [' + key + '] 连接失败: ' + e.message, false);
  } finally {
    btn.textContent = '测试连接';
  }
}

// ==================== 职能模型下拉（按实例查询可选模型） ====================

let roleSeq = 0;
/** 实例地址 -> 可用模型缓存 { baseUrl: [{id, name, models:[{id,name}]}] } */
const ROLE_MODELS_CACHE = {};

/** 解析实例 key 对应的服务地址（空 = 全局地址，实时取输入框值） */
function resolveInstBaseUrl(instKey) {
  if (!instKey) return $('#baseUrl').value.trim();
  const row = [...document.querySelectorAll('#tblInst tbody tr')]
    .find(r => r.querySelector('.i-key').value.trim() === instKey);
  return row ? row.querySelector('.i-url').value.trim() : '';
}

/** 拉取（带缓存）指定实例的可用模型列表 */
async function ensureInstanceModels(baseUrl) {
  if (!baseUrl) return [];
  if (ROLE_MODELS_CACHE[baseUrl]) return ROLE_MODELS_CACHE[baseUrl];
  try {
    const r = await fetch('/api/models?baseUrl=' + encodeURIComponent(baseUrl));
    const res = await r.json();
    if (r.ok && Array.isArray(res.providers)) {
      ROLE_MODELS_CACHE[baseUrl] = res.providers;
      return res.providers;
    }
  } catch (e) { /* 实例不可达时静默降级为手动输入 */ }
  return [];
}

/** 填充职能行的模型 datalist：选项值为 provider/model 格式 */
async function fillRoleModelDatalist(tr) {
  const instKey = tr.querySelector('.r-instance').value;
  const baseUrl = resolveInstBaseUrl(instKey);
  const dl = tr.querySelector('datalist');
  dl.innerHTML = '<option value="">（加载中...）</option>';
  const providers = await ensureInstanceModels(baseUrl);
  if (!providers.length) {
    dl.innerHTML = '';
    return;
  }
  dl.innerHTML = providers.flatMap(p => (p.models || []).map(m =>
    '<option value="' + p.id + '/' + m.id + '">' + (p.name || p.id) + ' / ' + (m.name || m.id) + '</option>'
  )).join('');
}

/** 刷新所有职能行的模型下拉（实例地址/选择变化后调用） */
function refreshAllRoleModels() {
  document.querySelectorAll('#tblRole tbody tr').forEach(fillRoleModelDatalist);
}

document.addEventListener('change', (e) => {
  if (e.target.classList.contains('i-key')) refreshInstanceOptions();
  // 实例地址变化：清空模型与目录缓存并刷新所有职能行的模型下拉
  if (e.target.classList.contains('i-url')) {
    Object.keys(ROLE_MODELS_CACHE).forEach(k => delete ROLE_MODELS_CACHE[k]);
    Object.keys(DIR_CACHE).forEach(k => delete DIR_CACHE[k]);
    refreshAllRoleModels();
  }
  // 职能行切换实例：记录新选择并重查该实例的模型
  if (e.target.classList.contains('r-instance')) {
    e.target.dataset.cur = e.target.value;
    fillRoleModelDatalist(e.target.closest('tr'));
  }
});

function showRoleMsg(text, ok) {
  const m = $('#roleMsg');
  m.textContent = text;
  m.className = 'msg ' + (ok ? 'msg-ok' : 'msg-err');
  setTimeout(() => { m.className = 'msg'; }, 6000);
}

async function loadRoles() {
  try {
    const r = await fetch('/api/roles');
    const cfg = await r.json();
    $('#tblInst tbody').innerHTML = '';
    $('#tblRole tbody').innerHTML = '';
    Object.entries(cfg.instances || {}).forEach(([key, raw]) => {
      const inst = typeof raw === 'string' ? { baseUrl: raw } : raw;
      addInstRow({ key, ...inst });
    });
    (cfg.roles || []).forEach(addRoleRow);
    // 已连接实例的目录为空时，自动用服务端默认目录回填
    document.querySelectorAll('#tblInst tbody tr').forEach(autofillInstDirectory);
  } catch (e) { showRoleMsg('职能配置加载失败: ' + e.message, false); }
}

async function saveRoles() {
  const instances = {};
  let instBad = false;
  [...document.querySelectorAll('#tblInst tbody tr')].forEach(tr => {
    const key = tr.querySelector('.i-key').value.trim();
    const baseUrl = tr.querySelector('.i-url').value.trim();
    const directory = tr.querySelector('.i-dir').value.trim();
    if (key && baseUrl) instances[key] = { baseUrl, directory }; else instBad = true;
  });
  if (instBad) { showRoleMsg('保存失败：实例的 key/服务地址需填写完整', false); return; }

  const roles = [];
  const badRows = [];
  [...document.querySelectorAll('#tblRole tbody tr')].forEach((tr, i) => {
    const r = {
      key: tr.querySelector('.r-key').value.trim(),
      name: tr.querySelector('.r-name').value.trim(),
      desc: tr.querySelector('.r-desc').value.trim(),
      prompt: tr.querySelector('.r-prompt').value.trim(),
      instance: tr.querySelector('.r-instance').value,
      model: tr.querySelector('.r-model').value.trim(),
      skills: tr.querySelector('.r-skills').value.split(',').map(s => s.trim()).filter(Boolean),
      readOnly: tr.querySelector('.r-readonly').checked,
    };
    if (!r.key || !r.name) { badRows.push(i + 1); return; }
    roles.push(r);
  });
  if (badRows.length) { showRoleMsg('保存失败：第 ' + badRows.join('、') + ' 行职能的 key/名称未填完整', false); return; }
  if (roles.length === 0) { showRoleMsg('至少需要配置一个职能', false); return; }

  try {
    const r = await fetch('/api/roles', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ instances, roles }) });
    const res = await r.json();
    if (!r.ok) { showRoleMsg('保存失败: ' + (res.error || r.status), false); return; }
    showRoleMsg('✅ 已保存并热生效（' + res.summary.roleCount + ' 个职能 / ' + res.summary.instanceCount + ' 个实例）', true);
    loadRoles();
  } catch (e) { showRoleMsg('保存失败: ' + e.message, false); }
}

loadRoles();

load();
</script>
</body>
</html>`;

/**
 * 配置管理服务类
 */
export class AdminServer {
    /** @type {import('../agent/agent-registry.js').AgentRegistry} */
    #registry;
    /** @type {import('../feishu/feishu-gateway.js').FeishuGateway|null} */
    #gateway;
    /** @type {import('../agent/role-registry.js').RoleRegistry|null} */
    #roleRegistry;
    /** @type {import('../agent/instance-pool.js').InstancePool|null} */
    #instancePool;
    #port;

    /**
     * @param {{registry: AgentRegistry, gateway?: FeishuGateway, roleRegistry?: RoleRegistry, instancePool?: InstancePool, port?: number}} options
     */
    constructor({ registry, gateway = null, roleRegistry = null, instancePool = null, port = 8081 }) {
        if (!registry) throw new Error('AdminServer 初始化失败：缺少 registry');
        this.#registry = registry;
        this.#gateway = gateway;
        this.#roleRegistry = roleRegistry;
        this.#instancePool = instancePool;
        this.#port = port;
    }

    /**
     * 启动 HTTP 服务
     */
    start() {
        const server = createServer((req, res) => {
            this.#route(req, res).catch((error) => {
                console.error(`${LogPrefix.ADMIN} 请求处理异常: ${error.message}`);
                this.#json(res, 500, { error: error.message });
            });
        });
        // 端口占用等启动失败只告警，不拖垮机器人主流程
        server.on('error', (error) => {
            console.error(`${LogPrefix.ADMIN} 配置管理页启动失败（机器人继续运行）: ${error.message}`);
        });
        server.listen(this.#port, () => {
            console.log(`${LogPrefix.ADMIN} 配置管理页已启动: http://0.0.0.0:${this.#port}`);
        });
    }

    /**
     * 路由分发
     */
    async #route(req, res) {
        const url = new URL(req.url, `http://localhost:${this.#port}`);

        // 简单 Token 鉴权（配置了 ADMIN_TOKEN 时生效）
        if (process.env.ADMIN_TOKEN && url.pathname !== '/') {
            const token = req.headers['x-admin-token'] || url.searchParams.get('token');
            if (token !== process.env.ADMIN_TOKEN) {
                return this.#json(res, 401, { error: '未授权' });
            }
        }

        if (req.method === 'GET' && url.pathname === '/') {
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
            return res.end(ADMIN_HTML);
        }

        if (req.method === 'GET' && url.pathname === '/api/models') {
            // baseUrl 可选：默认用当前配置的地址，便于修改前预览可用模型
            const baseUrl = url.searchParams.get('baseUrl') || BotConfig.getOpencodeBaseUrl();
            try {
                const providers = await this.#fetchProviders(baseUrl);
                return this.#json(res, 200, { providers });
            } catch (error) {
                return this.#json(res, 502, { error: `获取可用模型失败: ${error.message}` });
            }
        }

        if (req.method === 'GET' && url.pathname === '/api/config') {
            const cfg = BotConfig.loadBotConfig();
            return this.#json(res, 200, {
                opencodeBaseUrl: cfg.opencodeBaseUrl,
                defaultKey: cfg.defaultKey,
                agents: cfg.agents,
                source: cfg.source,
                security: BotConfig.getSecurityConfig(),
                feishuAppId: process.env.FEISHU_APP_ID || '',
                feishuWs: this.#gateway?.getConnectionStatus?.() || null,
            });
        }

        if (req.method === 'POST' && url.pathname === '/api/config') {
            const body = await this.#readJson(req);
            try {
                const { urlChanged } = BotConfig.saveBotConfig(body);
                const summary = this.#registry.reload();
                console.log(`${LogPrefix.ADMIN} 配置已更新: ${summary.count} 个 Agent @ ${summary.baseUrl}`);
                return this.#json(res, 200, { saved: true, urlChanged, summary });
            } catch (error) {
                // 配置校验失败：返回 400，不触发重载
                return this.#json(res, 400, { error: error.message });
            }
        }

        if (req.method === 'POST' && url.pathname === '/api/restart') {
            this.#json(res, 200, { restarting: true });
            console.log(`${LogPrefix.ADMIN} 收到重启请求，3 秒后退出进程（等待容器自动拉起）`);
            setTimeout(() => process.exit(0), 3000);
            return;
        }

        if (req.method === 'GET' && url.pathname === '/api/instance/projects') {
            // 获取 OpenCode 实例的项目列表（worktree 即可选目录，供实例目录配置下拉选择）
            const baseUrl = url.searchParams.get('baseUrl') || '';
            if (!/^https?:\/\//.test(baseUrl)) {
                return this.#json(res, 400, { error: '服务地址必须以 http:// 或 https:// 开头' });
            }
            try {
                const resp = await fetch(`${baseUrl.replace(/\/+$/, '')}/project`, { signal: AbortSignal.timeout(8000) });
                if (!resp.ok) throw new Error(`OpenCode 返回 ${resp.status}`);
                const data = await resp.json();
                const projects = (Array.isArray(data) ? data : [])
                    .filter((p) => p?.worktree)
                    .map((p) => ({ id: p.id, worktree: p.worktree, vcs: p.vcs || '' }));
                return this.#json(res, 200, { projects });
            } catch (error) {
                return this.#json(res, 502, { error: `获取项目列表失败: ${error.message}` });
            }
        }

        if (req.method === 'GET' && url.pathname === '/api/instance/path') {
            // 获取 OpenCode 实例的服务端路径信息（directory 为默认目录，用于会话归档配置自动填充）
            const baseUrl = url.searchParams.get('baseUrl') || '';
            if (!/^https?:\/\//.test(baseUrl)) {
                return this.#json(res, 400, { error: '服务地址必须以 http:// 或 https:// 开头' });
            }
            try {
                const resp = await fetch(`${baseUrl.replace(/\/+$/, '')}/path`, { signal: AbortSignal.timeout(8000) });
                if (!resp.ok) throw new Error(`OpenCode 返回 ${resp.status}`);
                const data = await resp.json();
                return this.#json(res, 200, {
                    directory: data?.directory || '',
                    worktree: data?.worktree || '',
                    home: data?.home || '',
                });
            } catch (error) {
                return this.#json(res, 502, { error: `获取实例路径失败: ${error.message}` });
            }
        }

        // ==================== 职能与实例管理（Agent API） ====================
        if (req.method === 'GET' && url.pathname === '/api/roles') {
            if (!this.#roleRegistry) return this.#json(res, 404, { error: '职能管理未启用' });
            return this.#json(res, 200, this.#roleRegistry.getConfig());
        }

        if (req.method === 'POST' && url.pathname === '/api/roles') {
            if (!this.#roleRegistry) return this.#json(res, 404, { error: '职能管理未启用' });
            const body = await this.#readJson(req);
            try {
                const summary = this.#roleRegistry.saveConfig(body);
                // 实例地址可能变化：清空 Agent 缓存，下次使用时按新配置重建
                this.#instancePool?.invalidate();
                console.log(`${LogPrefix.ADMIN} 职能配置已更新: ${summary.roleCount} 个职能 / ${summary.instanceCount} 个实例`);
                return this.#json(res, 200, { saved: true, summary });
            } catch (error) {
                // 配置校验失败：返回 400，不触发重载
                return this.#json(res, 400, { error: error.message });
            }
        }

        this.#json(res, 404, { error: 'not found' });
    }

    /**
     * 调用 OpenCode /config/providers 获取可用 provider 与模型列表
     * 返回紧凑结构：[{id, name, models:[{id, name}]}]
     */
    async #fetchProviders(baseUrl) {
        if (!baseUrl || !/^https?:\/\//.test(baseUrl)) {
            throw new Error('服务地址必须以 http:// 或 https:// 开头');
        }
        const url = `${baseUrl.replace(/\/+$/, '')}/config/providers`;
        // 拉取超时 8s，避免配置页被无响应的上游拖死
        const resp = await fetch(url, { signal: AbortSignal.timeout(8000) });
        if (!resp.ok) {
            throw new Error(`OpenCode 返回 ${resp.status}（${url}）`);
        }
        const data = await resp.json();
        const providers = (data?.providers || [])
            .filter((p) => p?.id && p?.models && Object.keys(p.models).length > 0)
            .map((p) => ({
                id: p.id,
                name: p.name || p.id,
                models: Object.values(p.models).map((m) => ({
                    id: m.id,
                    name: m.name || m.id,
                })),
            }));
        if (providers.length === 0) {
            throw new Error('OpenCode 未返回任何可用模型');
        }
        return providers;
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

    #json(res, code, data) {
        res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify(data));
    }
}

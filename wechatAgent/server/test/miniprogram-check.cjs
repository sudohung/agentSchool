/**
 * 小程序静态检查
 *
 * 本机没有微信开发者工具，用静态检查代替一部分「打开工具才会发现」的问题：
 *  1. app.json 里登记的所有页面，四件套（js/json/wxml/wxss）是否齐全
 *  2. WXML 里使用的事件处理函数，JS 中是否真的定义
 *  3. WXML 里引用的 data 字段，JS 的 data 中是否存在（含 methods 外的顶层字段）
 *  4. scroll-into-view 的目标 id 是否存在于 WXML
 *  5. require 的相对路径是否存在
 *  6. WXSS 引用的 CSS 变量是否在 app.wxss 定义
 *
 * 运行：node test/miniprogram-check.cjs
 */

const fs = require('fs');
const path = require('path');

const MINI = path.resolve(__dirname, '../../miniprogram');
const problems = [];
const warnings = [];

/**
 * 递归收集文件
 * @param {string} dir
 * @param {RegExp} pattern
 */
function walk(dir, pattern) {
    const out = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) out.push(...walk(full, pattern));
        else if (pattern.test(entry.name)) out.push(full);
    }
    return out;
}

// ==================== 1. 页面完整性 ====================

const appJson = JSON.parse(fs.readFileSync(path.join(MINI, 'app.json'), 'utf-8'));
const pages = appJson.pages || [];

for (const page of pages) {
    for (const ext of ['js', 'json', 'wxml', 'wxss']) {
        const file = path.join(MINI, `${page}.${ext}`);
        if (!fs.existsSync(file)) {
            // json/wxss 对小程序是可选的，只提示
            if (ext === 'js' || ext === 'wxml') problems.push(`页面缺文件: ${page}.${ext}`);
            else warnings.push(`页面缺可选文件: ${page}.${ext}`);
        }
    }
}

// app 文件
for (const file of ['app.js', 'app.json', 'app.wxss', 'sitemap.json']) {
    if (!fs.existsSync(path.join(MINI, file))) problems.push(`缺少 ${file}`);
}

// ==================== 2/3/4. WXML 与 JS 交叉校验 ====================

/** 提取 JS 中 Page({...}) 的定义体 */
function extractPageObject(jsSource) {
    const index = jsSource.indexOf('Page(');
    if (index < 0) return null;
    // 找到匹配的右括号
    let depth = 0;
    let start = jsSource.indexOf('{', index);
    for (let i = start; i < jsSource.length; i += 1) {
        if (jsSource[i] === '{') depth += 1;
        else if (jsSource[i] === '}') {
            depth -= 1;
            if (depth === 0) return jsSource.slice(start, i + 1);
        }
    }
    return null;
}

for (const page of pages) {
    const wxmlPath = path.join(MINI, `${page}.wxml`);
    const jsPath = path.join(MINI, `${page}.js`);
    if (!fs.existsSync(wxmlPath) || !fs.existsSync(jsPath)) continue;

    const wxml = fs.readFileSync(wxmlPath, 'utf-8');
    const js = fs.readFileSync(jsPath, 'utf-8');
    const pageObj = extractPageObject(js);
    if (!pageObj) {
        problems.push(`${page}.js 未找到 Page({...})`);
        continue;
    }

    // --- 事件绑定 ---
    const bindings = [...wxml.matchAll(/\bbind(?:tap|input|longpress|keyboardheightchange|change|confirm)\s*=\s*"([^"{}]+)"/g)]
        .map((m) => m[1].trim())
        .filter(Boolean);

    for (const handler of new Set(bindings)) {
        // 方法需以 `name(` 或 `async name(` 形式出现在 Page 对象里
        const re = new RegExp(`(?:async\\s+)?\\b${handler}\\s*\\(`);
        if (!re.test(pageObj)) {
            problems.push(`${page}.wxml 绑定的 ${handler} 在 ${page}.js 中不存在`);
        }
    }

    // --- data 字段 ---
    const dataMatch = pageObj.match(/\bdata\s*:\s*\{/);
    let dataKeys = new Set();
    if (dataMatch) {
        const dataStart = pageObj.indexOf('{', dataMatch.index + dataMatch[0].length - 1);
        let depth = 0;
        for (let i = dataStart; i < pageObj.length; i += 1) {
            if (pageObj[i] === '{') depth += 1;
            else if (pageObj[i] === '}') {
                depth -= 1;
                if (depth === 0) {
                    const dataBody = pageObj.slice(dataStart + 1, i);
                    // 顶层 key
                    for (const m of dataBody.matchAll(/^\s{0,12}(\w+)\s*:/gm)) dataKeys.add(m[1]);
                    break;
                }
            }
        }
    }

    // 顶层非 data 字段也算（如 streamIndex 之类的自定义属性）
    const topLevelKeys = new Set([...pageObj.matchAll(/^\s{4}(\w+)\s*:/gm)].map((m) => m[1]));
    const known = new Set([...dataKeys, ...topLevelKeys]);

    // 模板里 {{ }} 中引用的标识符
    const mustaches = [...wxml.matchAll(/\{\{([^}]+)\}\}/g)].map((m) => m[1]);
    const jsGlobals = new Set(['true', 'false', 'null', 'undefined', 'Math', 'JSON', 'item', 'index']);

    // wx:for 的循环别名（默认 item/index，可自定义 wx:for-item / wx:for-index）
    const loopAliases = new Set(['item', 'index']);
    for (const m of wxml.matchAll(/wx:for-(?:item|index)\s*=\s*"([^"]+)"/g)) {
        loopAliases.add(m[1].trim());
    }

    for (const expr of mustaches) {
        // 去掉字符串字面量，避免误判
        const cleaned = expr.replace(/'[^']*'|"[^"]*"/g, '');
        for (const m of cleaned.matchAll(/(^|[^.\w$])([a-zA-Z_$][\w$]*)/g)) {
            const name = m[2];
            if (jsGlobals.has(name)) continue;
            if (loopAliases.has(name)) continue;
            if (known.has(name)) continue;
            // 方法名、wx:for 临时别名都跳过
            if (new RegExp(`(?:async\\s+)?\\b${name}\\s*\\(`).test(pageObj)) continue;
            warnings.push(`${page}.wxml 引用 ${name}，但 ${page}.js 的 data 中没有`);
        }
    }

    // --- scroll-into-view 目标 id ---
    if (/scroll-into-view/.test(wxml)) {
        const ids = new Set([...wxml.matchAll(/\bid\s*=\s*"([^"{}]+)"/g)].map((m) => m[1]));
        const dynamicIds = [...wxml.matchAll(/\bid\s*=\s*"([^"]*\{\{[^"]+)"/g)].map((m) => m[1]);

        // 收集 JS 中所有 scrollIntoView 赋值语句里的字符串常量（兼容三元/拼接）
        const assigned = new Set();
        for (const m of js.matchAll(/scrollIntoView\s*:\s*([^,\n}]+)/g)) {
            for (const s of m[1].matchAll(/'([^']+)'|"([^"]+)"/g)) {
                assigned.add(s[1] || s[2]);
            }
        }
        for (const value of assigned) {
            if (!value || /\s/.test(value)) continue; // 跳过带空格的句子常量
            if (ids.has(value)) continue;
            if (dynamicIds.some((tpl) => tpl.includes(value))) continue;
            problems.push(`${page}.js 滚动的目标 id="${value}" 在 ${page}.wxml 中不存在`);
        }
    }
}

// ==================== 5. require 路径 ====================

for (const file of walk(MINI, /\.js$/)) {
    const source = fs.readFileSync(file, 'utf-8');
    for (const m of source.matchAll(/require\(\s*['"](\.[^'"]+)['"]\s*\)/g)) {
        const target = path.resolve(path.dirname(file), m[1]);
        const exists = fs.existsSync(target) || fs.existsSync(`${target}.js`) || fs.existsSync(path.join(target, 'index.js'));
        if (!exists) problems.push(`${path.relative(MINI, file)} require 的 ${m[1]} 不存在`);
    }
}

// ==================== 6. WXSS 变量 ====================

const appWxss = fs.readFileSync(path.join(MINI, 'app.wxss'), 'utf-8');
const defined = new Set([...appWxss.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));

for (const file of walk(MINI, /\.wxss$/)) {
    const source = fs.readFileSync(file, 'utf-8');
    for (const m of source.matchAll(/var\((--[\w-]+)/g)) {
        if (!defined.has(m[1])) {
            problems.push(`${path.relative(MINI, file)} 使用了未定义的变量 ${m[1]}`);
        }
    }
}

// ==================== 输出 ====================

console.log('======== 小程序静态检查 ========');
console.log(`页面数: ${pages.length}`);
if (warnings.length) {
    console.log(`\n提示 (${warnings.length}):`);
    warnings.forEach((w) => console.log('  ·', w));
}
if (problems.length) {
    console.log(`\n问题 (${problems.length}):`);
    problems.forEach((p) => console.log('  ✗', p));
    process.exit(1);
}
console.log('\n未发现问题 ✓');
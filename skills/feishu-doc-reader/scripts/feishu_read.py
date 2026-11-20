#!/usr/bin/env python3
"""Feishu Doc Reader - 读取飞书文档(docx/wiki)并转换为 Markdown。

复用 feishu-doc-publisher 的应用凭证（~/.claude/feishu_config.json 或环境变量）。

用法:
  python feishu_read.py --url https://xxx.feishu.cn/docx/xxxx
  python feishu_read.py --url https://xxx.feishu.cn/wiki/xxxx --out doc.md
  python feishu_read.py --doc-id xxxx
  python feishu_read.py --url xxx --format json          # 原始 blocks JSON
  python feishu_read.py --url xxx --stats                # 块类型统计
  python feishu_read.py --url xxx --download-images dir  # 下载图片到目录

输出约定:
  - markdown 内容始终写到 stdout，技能执行后可直接消费（无需再 Read 文件）
  - 元信息 JSON（success/out/blocks/title/doc_id）写到 stderr，不污染 markdown
  - 指定 --out 时同时落盘文件；--format json 时 stdout 为原始 blocks JSON
  - 表格单元格多段落用 <br> 连接；代码块语言兼容数字枚举与字符串名
"""

import argparse, json, os, re, sys
import requests

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_URL = 'https://open.feishu.cn/open-apis'

# block_type 常量（与飞书 docx API 对齐）
BT_PAGE, BT_TEXT = 1, 2
BT_HEADINGS = {3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9}
BT_BULLET, BT_ORDERED, BT_CODE, BT_QUOTE = 12, 13, 14, 15
BT_TODO, BT_BITABLE, BT_CALLOUT = 17, 18, 19
BT_DIAGRAM, BT_DIVIDER, BT_FILE = 21, 22, 23
BT_GRID, BT_GRID_COL, BT_IFRAME, BT_IMAGE = 24, 25, 26, 27
BT_ISV, BT_MINDNOTE, BT_SHEET, BT_TABLE, BT_TABLE_CELL = 28, 29, 30, 31, 32
BT_VIEW, BT_QUOTE_CONTAINER = 33, 34
BT_ADD_ONS, BT_JIRA, BT_WIKI_CATALOG, BT_BOARD = 39, 40, 41, 42
BT_AGENDA, BT_AGENDA_SECTION = 43, 45

# 飞书代码块语言枚举（数字，读取 API 返回）-> markdown 语言标记
# 枚举顺序与飞书官方 CodeLanguage 一致（1=PlainText ... 75=TOML），实测验证
FEISHU_LANG_NUM_TO_MD = {
    1: '', 2: 'abap', 3: 'ada', 4: 'apache', 5: 'apex', 6: 'asm',
    7: 'bash', 8: 'csharp', 9: 'cpp', 10: 'c', 11: 'cobol', 12: 'css',
    13: 'coffeescript', 14: 'd', 15: 'dart', 16: 'delphi', 17: 'django',
    18: 'dockerfile', 19: 'erlang', 20: 'fortran', 21: 'foxpro', 22: 'go',
    23: 'groovy', 24: 'html', 25: 'hbs', 26: 'http', 27: 'haskell',
    28: 'json', 29: 'java', 30: 'javascript', 31: 'julia', 32: 'kotlin',
    33: 'latex', 34: 'lisp', 35: 'logo', 36: 'lua', 37: 'matlab',
    38: 'makefile', 39: 'markdown', 40: 'nginx', 41: 'objc', 42: 'abl',
    43: 'php', 44: 'perl', 45: 'postscript', 46: 'powershell', 47: 'prolog',
    48: 'protobuf', 49: 'python', 50: 'r', 51: 'rpg', 52: 'ruby', 53: 'rust',
    54: 'sas', 55: 'scss', 56: 'sql', 57: 'scala', 58: 'scheme', 59: 'scratch',
    60: 'bash', 61: 'swift', 62: 'thrift', 63: 'typescript', 64: 'vbscript',
    65: 'vb', 66: 'xml', 67: 'yaml', 68: 'cmake', 69: 'diff', 70: 'gherkin',
    71: 'graphql', 72: 'glsl', 73: 'properties', 74: 'solidity', 75: 'toml',
}

# 飞书语言名 -> markdown 语言标记（创建/读取返回字符串名时使用）
FEISHU_LANG_TO_MD = {
    'PlainText': '', 'Plain Text': '', 'Java': 'java', 'SQL': 'sql', 'SQL(v2)': 'sql',
    'SQLv2': 'sql', 'Python': 'python', 'Python2': 'python', 'JSON': 'json',
    'JavaScript': 'javascript', 'YAML': 'yaml', 'YAMLv2': 'yaml', 'Bash': 'bash',
    'Shell': 'bash', 'XML': 'xml', 'XMLv2': 'xml', 'HTML': 'html', 'CSS': 'css',
    'TypeScript': 'typescript', 'Go': 'go', 'Rust': 'rust', 'Rustu': 'rust',
    'C': 'c', 'Cpp': 'cpp', 'C++': 'cpp', 'C#': 'csharp', 'CSharp': 'csharp',
    'Markdown': 'markdown', 'MarkdownV2': 'markdown', 'Assembly language': 'asm',
    'ABAP': 'abap', 'Ada': 'ada', 'Apache': 'apache', 'Apex': 'apex',
    'Clojure': 'clojure', 'CoffeeScript': 'coffeescript', 'D': 'd', 'Dart': 'dart',
    'Delphi': 'delphi', 'Django': 'django', 'Dockerfile': 'dockerfile',
    'Elixir': 'elixir', 'Erlang': 'erlang', 'Fortran': 'fortran', 'FoxPro': 'foxpro',
    'Git': 'git', 'GoMod': 'gomod', 'Gradle': 'gradle', 'Groovy': 'groovy',
    'HTMLBars': 'hbs', 'HTTP': 'http', 'Haskell': 'haskell', 'JSON5': 'json5',
    'JSONP': 'jsonp', 'JavaServerPages': 'jsp', 'Julia': 'julia', 'Kotlin': 'kotlin',
    'LaTeX': 'latex', 'Less': 'less', 'Lisp': 'lisp', 'Logo': 'logo', 'Lua': 'lua',
    'MATLAB': 'matlab', 'Makefile': 'makefile', 'Nginx': 'nginx',
    'Objective-C': 'objc', 'OpenEdge ABL': 'abl', 'PHP': 'php', 'Perl': 'perl',
    'PowerShell': 'powershell', 'Prolog': 'prolog', 'Properties': 'properties',
    'Protobuf': 'protobuf', 'ProtoBuf': 'protobuf', 'Puppet': 'puppet',
    'R': 'r', 'Redis': 'redis', 'Ruby': 'ruby', 'SCALA': 'scala', 'SCSS': 'scss',
    'SWIFT': 'swift', 'SAS': 'sas', 'Scheme': 'scheme', 'Scratch': 'scratch',
    'Solidity': 'solidity', 'Thrift': 'thrift', 'TOML': 'toml', 'Twig': 'twig',
    'VBScript': 'vbscript', 'Visual Basic': 'vb', 'Vue': 'vue',
    'CMake': 'cmake', 'Diff': 'diff', 'Gherkin': 'gherkin', 'GraphQL': 'graphql',
    'OpenGL Shading Language': 'glsl',
}

PLACEHOLDER_TYPES = {
    BT_BITABLE: '多维表格', BT_DIAGRAM: '流程图/UML', BT_MINDNOTE: '思维笔记',
    BT_SHEET: '电子表格', BT_BOARD: '画板', BT_ISV: '第三方内容',
    BT_ADD_ONS: '小组件', BT_JIRA: 'Jira_issue', BT_WIKI_CATALOG: '知识库目录',
    BT_AGENDA: '会议纪要', BT_AGENDA_SECTION: '会议纪要段落', BT_VIEW: '视图',
    BT_IFRAME: '内嵌网页',
}


class Client:
    def __init__(self, app_id, app_secret):
        self.app_id, self.app_secret, self.token = app_id, app_secret, None

    def auth(self):
        r = requests.post(f'{BASE_URL}/auth/v3/tenant_access_token/internal',
                          json={'app_id': self.app_id, 'app_secret': self.app_secret}, timeout=30)
        d = r.json()
        if d['code'] != 0:
            raise Exception(f'Auth failed: {d["msg"]}')
        self.token = d['tenant_access_token']

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    def get(self, path, params=None, timeout=30):
        r = requests.get(f'{BASE_URL}{path}', headers=self.headers, params=params, timeout=timeout)
        d = r.json()
        if d['code'] != 0:
            raise Exception(f'API failed [{path}]: {d["msg"]} (code={d["code"]})')
        return d['data']

    def resolve_wiki_token(self, wiki_token):
        """wiki token -> (obj_token, obj_type)"""
        d = self.get('/wiki/v2/spaces/get_node', params={'token': wiki_token})
        node = d['node']
        return node['obj_token'], node.get('obj_type', 'docx')

    def fetch_all_blocks(self, doc_id):
        """拉取文档全部 blocks（含嵌套），返回 {block_id: block}"""
        blocks, page_token = [], None
        while True:
            params = {'page_size': 500, 'document_revision_id': -1}
            if page_token:
                params['page_token'] = page_token
            d = self.get(f'/docx/v1/documents/{doc_id}/blocks', params=params)
            items = d.get('items', [])
            blocks.extend(items)
            if not d.get('has_more'):
                break
            page_token = d.get('page_token')
        return {b['block_id']: b for b in blocks}

    def fetch_doc_title(self, doc_id):
        try:
            d = self.get(f'/docx/v1/documents/{doc_id}')
            return d['document']['title']
        except Exception:
            return None

    def fetch_doc_raw_content(self, doc_token):
        """老版 doc（obj_type=doc）纯文本"""
        r = requests.get(f'{BASE_URL}/doc/v2/{doc_token}/raw_content',
                         headers=self.headers, timeout=30)
        d = r.json()
        if d['code'] != 0:
            raise Exception(f'raw_content failed: {d["msg"]}')
        return d['data']['content']

    def download_media(self, file_token, save_path):
        """下载文档内媒体（图片等）。返回保存路径或 None。"""
        r = requests.get(f'{BASE_URL}/drive/v1/medias/{file_token}/download',
                         headers=self.headers, timeout=60)
        if r.status_code != 200:
            return None
        ct = r.headers.get('Content-Type', '')
        ext = 'png'
        if 'jpeg' in ct or 'jpg' in ct:
            ext = 'jpg'
        elif 'gif' in ct:
            ext = 'gif'
        elif 'webp' in ct:
            ext = 'webp'
        elif 'svg' in ct:
            ext = 'svg'
        out = save_path + '.' + ext
        with open(out, 'wb') as f:
            f.write(r.content)
        return out


def load_config(path=None):
    cfg = {'app_id': '', 'app_secret': ''}
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            cfg.update(json.load(f))
    if not cfg['app_id']:
        p = os.path.expanduser('~/.claude/feishu_config.json')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                cfg.update(json.load(f))
    cfg['app_id'] = cfg['app_id'] or os.environ.get('FEISHU_APP_ID', '')
    cfg['app_secret'] = cfg['app_secret'] or os.environ.get('FEISHU_APP_SECRET', '')
    return cfg


def extract_ref(url_or_token):
    """从 URL 或裸 token 提取 (kind, token)"""
    s = url_or_token.strip()
    if '/docx/' in s:
        return ('docx', re.search(r'/docx/([a-zA-Z0-9]+)', s).group(1))
    if '/wiki/' in s:
        return ('wiki', re.search(r'/wiki/([a-zA-Z0-9]+)', s).group(1))
    if re.fullmatch(r'[a-zA-Z0-9]{20,}', s):
        return ('docx', s)
    return None, None


# ---------- 元素 -> Markdown 行内文本 ----------

def _esc_md_cell(t):
    return t.replace('|', '\\|').replace('\n', '<br>')


def elements_to_md(elements):
    parts = []
    for e in elements or []:
        tr = e.get('text_run')
        if not tr:
            # 其他元素类型
            if 'mention_doc' in e:
                parts.append(f"[文档:{e['mention_doc'].get('title', '')}]")
            elif 'mention_user' in e:
                parts.append(f"@{e['mention_user'].get('key', 'user')}")
            elif 'equation' in e:
                parts.append(f"${e['equation'].get('content', '')}$")
            continue
        content = tr.get('content', '')
        if not content:
            continue
        style = tr.get('text_element_style') or {}
        link = (style.get('link') or {}).get('url')
        if style.get('inline_code'):
            content = f'`{content}`'
        else:
            if style.get('bold'):
                content = f'**{content}**'
            if style.get('italic'):
                content = f'*{content}*'
            if style.get('strikethrough'):
                content = f'~~{content}~~'
        if link:
            content = f'[{content}]({link})'
        parts.append(content)
    return ''.join(parts)


def block_text_md(block, key=None):
    d = block.get(key) or {}
    return elements_to_md(d.get('elements'))


# ---------- 树构建与渲染 ----------

def build_tree(blocks_map):
    """返回顶层 block 列表（page block 的 children），并给每个 block 挂 children_ids"""
    root_id = None
    for bid, b in blocks_map.items():
        if b.get('block_type') == BT_PAGE:
            root_id = bid
            break
    if root_id is None:
        # 兜底：parent_id 不在 map 中的视为顶层
        roots = [b for bid, b in blocks_map.items() if b.get('parent_id') not in blocks_map]
        return sorted(roots, key=lambda x: x.get('block_id'))
    page = blocks_map[root_id]
    def attach(b):
        b['_children'] = [blocks_map[c] for c in b.get('children', []) if c in blocks_map]
        for c in b['_children']:
            attach(c)
    attach(page)
    return page['_children']


def render_blocks(blocks, ctx, depth=0, in_cell=False):
    """渲染 block 列表 -> markdown 行列表"""
    out = []
    for b in blocks:
        out.extend(render_block(b, ctx, depth, in_cell))
    return out


def resolve_code_lang(code_block):
    """从 code block 解析 markdown 语言标记。

    兼容两种返回格式：
    - 读取 API: language 位于 style 内，为数字枚举（如 56=SQL）
    - 旧格式/字符串: language 位于顶层或 style 内，为字符串名（如 'SQL'）
    """
    style = code_block.get('style') or {}
    lang = code_block.get('language', style.get('language'))
    if lang is None:
        return ''
    if isinstance(lang, int):
        return FEISHU_LANG_NUM_TO_MD.get(lang, '')
    return FEISHU_LANG_TO_MD.get(str(lang).strip(), '')


def render_block(b, ctx, depth, in_cell):
    bt = b.get('block_type')
    kids = b.get('_children', [])
    indent = '    ' * depth
    lines = []

    if bt in BT_HEADINGS:
        level = min(BT_HEADINGS[bt], 6)
        text = block_text_md(b, f'heading{BT_HEADINGS[bt]}')
        if in_cell:
            if text:
                lines.append(f'**{text}**')
        elif text:
            lines.append('')
            lines.append('#' * level + ' ' + text)
            lines.append('')
        # 标题块可能承载折叠/缩进的子内容，必须继续渲染
        lines.extend(render_blocks(kids, ctx, depth, in_cell))
        return lines

    if bt == BT_TEXT:
        text = block_text_md(b, 'text')
        # 检查是否是表格 cell 内文本（无内容时跳过）
        lines.append(f'{indent}{text}' if text or not in_cell else '')
        return lines

    if bt == BT_BULLET:
        text = block_text_md(b, 'bullet')
        lines.append(f'{indent}- {text}')
        lines.extend(render_blocks(kids, ctx, depth + 1, in_cell))
        return lines

    if bt == BT_ORDERED:
        text = block_text_md(b, 'ordered')
        lines.append(f'{indent}1. {text}')
        lines.extend(render_blocks(kids, ctx, depth + 1, in_cell))
        return lines

    if bt == BT_TODO:
        text = block_text_md(b, 'todo')
        done = (b.get('todo') or {}).get('style', {}).get('done')
        mark = 'x' if done else ' '
        lines.append(f'{indent}- [{mark}] {text}')
        lines.extend(render_blocks(kids, ctx, depth + 1, in_cell))
        return lines

    if bt == BT_CODE:
        d = b.get('code') or {}
        lang_md = resolve_code_lang(d)
        code = elements_to_md(d.get('elements'))
        if in_cell:
            lines.append(f'`{code}`')
        else:
            lines.append(f'{indent}```{lang_md}')
            for cl in code.split('\n'):
                lines.append(cl)
            lines.append(f'{indent}```')
            lines.append('')
        return lines

    if bt == BT_QUOTE:
        text = block_text_md(b, 'quote')
        lines.append(f'{indent}> {text}')
        lines.extend(render_blocks(kids, ctx, depth, in_cell))
        return lines

    if bt == BT_QUOTE_CONTAINER or bt == BT_CALLOUT:
        inner = render_blocks(kids, ctx, depth, in_cell)
        for l in inner:
            lines.append(f'{indent}> {l}'.rstrip())
        lines.append('')
        return lines

    if bt == BT_DIVIDER:
        lines.append(f'{indent}---')
        lines.append('')
        return lines

    if bt == BT_IMAGE:
        d = b.get('image') or {}
        token = d.get('token', '')
        if ctx.get('img_dir'):
            path = ctx['client'].download_media(token, os.path.join(ctx['img_dir'], token))
            if path:
                rel = os.path.relpath(path, os.path.dirname(ctx.get('out_path') or '.') or '.')
                lines.append(f'{indent}![图片]({rel.replace(os.sep, "/")})')
                return lines
        lines.append(f'{indent}![图片](feishu-image://{token})')
        return lines

    if bt == BT_FILE:
        d = b.get('file') or {}
        lines.append(f'{indent}[附件:{d.get("name", "")}](feishu-file://{d.get("token", "")})')
        return lines

    if bt == BT_IFRAME:
        d = b.get('iframe') or {}
        url = (d.get('component') or {}).get('url') or d.get('url') or ''
        lines.append(f'{indent}[内嵌网页]({url})')
        return lines

    if bt == BT_TABLE:
        lines.extend(render_table(b, ctx))
        lines.append('')
        return lines

    if bt == BT_TABLE_CELL:
        # 已在 render_table 中处理，防御性兜底
        inner = render_blocks(kids, ctx, 0, True)
        lines.append('<br>'.join(x for x in inner if x is not None))
        return lines

    if bt == BT_GRID or bt == BT_GRID_COL or bt == BT_VIEW:
        # 布局容器：透传子块
        return render_blocks(kids, ctx, depth, in_cell)

    if bt in PLACEHOLDER_TYPES:
        lines.append(f'{indent}`[嵌入块:{PLACEHOLDER_TYPES[bt]}]`')
        return lines

    # 未知类型：尝试常见文本载体，否则占位
    for key in ('text', 'bullet', 'ordered', 'quote', 'todo'):
        if b.get(key):
            lines.append(f'{indent}{block_text_md(b, key)}')
            return lines
    if kids:
        return render_blocks(kids, ctx, depth, in_cell)
    lines.append(f'{indent}`[未支持块 type={bt}]`')
    return lines


def render_table(b, ctx):
    """table block -> markdown 表格。children 顺序为 row-major cell。"""
    prop = (b.get('table') or {}).get('property') or {}
    row_size = prop.get('row_size', 0)
    col_size = prop.get('column_size', 0)
    if not row_size or not col_size:
        return []
    cells = b.get('_children', [])
    grid = [['' for _ in range(col_size)] for _ in range(row_size)]
    for idx, cell in enumerate(cells):
        r, c = divmod(idx, col_size)
        if r < row_size and c < col_size:
            inner = render_blocks(cell.get('_children', []), ctx, 0, True)
            grid[r][c] = _esc_md_cell('<br>'.join(x.strip() for x in inner if x and x.strip()))
    lines = ['| ' + ' | '.join(grid[0]) + ' |',
             '|' + '---|' * col_size]
    for row in grid[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    return lines


def _line_kind(s):
    """粗略判断 markdown 行类型，用于块级间距规范化。"""
    s = s.lstrip()
    if s.startswith('>'):
        return 'quote'
    if s.startswith('|'):
        return 'table'
    if s.startswith('#'):
        return 'heading'
    if s.startswith('!['):
        return 'image'
    if s.startswith('---'):
        return 'divider'
    if re.match(r'^([-*+] |\d+\. |- \[)', s):
        return 'list'
    return 'text'


def _normalize_md(lines):
    """块级元素之间补空行，保证 Markdown 正确渲染（围栏内不改动）。"""
    out, in_fence = [], False
    for l in lines:
        s = l.lstrip()
        if s.startswith('```'):
            if not in_fence and out and out[-1].strip():
                out.append('')
            out.append(l)
            in_fence = not in_fence
            continue
        if not in_fence and out and out[-1].strip():
            k, pk = _line_kind(s), _line_kind(out[-1])
            if k in ('quote', 'table', 'image', 'divider'):
                if k != pk:
                    out.append('')
            elif k == 'list' and pk != 'list':
                out.append('')
        out.append(l)
    return out


def blocks_to_markdown(blocks_map, ctx):
    top = build_tree(blocks_map)
    lines = _normalize_md(render_blocks(top, ctx, 0, False))
    # 清理连续空行
    cleaned, prev_blank = [], False
    for l in lines:
        blank = (l.strip() == '')
        if blank and prev_blank:
            continue
        cleaned.append(l)
        prev_blank = blank
    md = '\n'.join(cleaned).strip() + '\n'
    return md


def page_title(blocks_map):
    """从 page block 提取标题（fetch_doc_title 失败时的兜底）。"""
    for b in blocks_map.values():
        if b.get('block_type') == BT_PAGE:
            return elements_to_md((b.get('page') or {}).get('elements')) or None
    return None


def stats_blocks(blocks_map):
    from collections import Counter
    cnt = Counter(b.get('block_type') for b in blocks_map.values())
    names = {BT_PAGE: 'page', BT_TEXT: 'text', BT_BULLET: 'bullet', BT_ORDERED: 'ordered',
             BT_CODE: 'code', BT_QUOTE: 'quote', BT_TODO: 'todo',
             BT_TABLE: 'table', BT_TABLE_CELL: 'table_cell', BT_IMAGE: 'image',
             BT_DIVIDER: 'divider', BT_CALLOUT: 'callout', BT_GRID: 'grid',
             BT_GRID_COL: 'grid_column', BT_QUOTE_CONTAINER: 'quote_container',
             BT_FILE: 'file', BT_IFRAME: 'iframe', BT_BITABLE: 'bitable',
             BT_VIEW: 'view', BT_DIAGRAM: 'diagram', BT_SHEET: 'sheet',
             BT_MINDNOTE: 'mindnote', BT_BOARD: 'board', BT_ADD_ONS: 'add_ons'}
    names.update({bt: f'heading{lv}' for bt, lv in BT_HEADINGS.items()})
    out = [f'total blocks: {len(blocks_map)}']
    for bt, n in cnt.most_common():
        out.append(f'  type {bt} ({names.get(bt, "unknown")}): {n}')
    return '\n'.join(out)


def main():
    p = argparse.ArgumentParser(description='Read Feishu doc/wiki to Markdown')
    p.add_argument('--url', help='Feishu docx/wiki URL or bare token')
    p.add_argument('--doc-id', help='docx document id (优先于 --url)')
    p.add_argument('--config', help='config json path')
    p.add_argument('--out', help='output markdown file path (default: stdout)')
    p.add_argument('--format', choices=['md', 'json'], default='md')
    p.add_argument('--stats', action='store_true', help='print block type stats')
    p.add_argument('--download-images', metavar='DIR', help='download images to DIR')
    args = p.parse_args()

    if not args.doc_id and not args.url:
        p.error('need --url or --doc-id')

    cfg = load_config(args.config)
    if not cfg['app_id'] or not cfg['app_secret']:
        print(json.dumps({'error': '缺少凭证：请配置 ~/.claude/feishu_config.json 或 FEISHU_APP_ID/FEISHU_APP_SECRET'}), file=sys.stderr)
        sys.exit(1)

    c = Client(cfg['app_id'], cfg['app_secret'])
    c.auth()

    doc_id, obj_type = args.doc_id, 'docx'
    if not doc_id:
        kind, token = extract_ref(args.url)
        if not token:
            print(json.dumps({'error': '无法从输入解析 docx/wiki token'}), file=sys.stderr)
            sys.exit(1)
        if kind == 'wiki':
            try:
                doc_id, obj_type = c.resolve_wiki_token(token)
            except Exception as e:
                print(json.dumps({'error': f'wiki 解析失败: {e}；'
                                   f'请确认应用对知识库节点有读取权限（知识库设置-添加应用为成员）'}), file=sys.stderr)
                sys.exit(2)
        else:
            doc_id = token

    if obj_type != 'docx':
        # 老版 doc：只能拿纯文本
        try:
            content = c.fetch_doc_raw_content(doc_id)
            sys.stdout.write(content if content.endswith('\n') else content + '\n')
            print(json.dumps({'success': True, 'obj_type': obj_type,
                              'note': '老版 doc 仅支持纯文本提取'}, ensure_ascii=False), file=sys.stderr)
        except Exception as e:
            print(json.dumps({'error': str(e)}), file=sys.stderr)
            sys.exit(2)
        return

    try:
        blocks_map = c.fetch_all_blocks(doc_id)
    except Exception as e:
        print(json.dumps({'error': f'读取文档失败: {e}；'
                           f'请确认应用对该文档有读取权限（文档分享-添加应用为协作者）'}), file=sys.stderr)
        sys.exit(2)

    if args.stats:
        print(stats_blocks(blocks_map))
        return

    if args.format == 'json':
        payload = json.dumps(list(blocks_map.values()), ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, 'w', encoding='utf-8') as f:
                f.write(payload)
            print(json.dumps({'success': True, 'out': args.out, 'blocks': len(blocks_map)}))
        else:
            print(payload)
        return

    ctx = {'client': c, 'img_dir': None, 'out_path': args.out}
    if args.download_images:
        os.makedirs(args.download_images, exist_ok=True)
        ctx['img_dir'] = args.download_images

    md = blocks_to_markdown(blocks_map, ctx)

    # 顶部补文档标题（API 拿不到时回退到 page block 内的标题）
    title = c.fetch_doc_title(doc_id) or page_title(blocks_map)
    if title and not md.startswith('# '):
        md = f'# {title}\n\n' + md

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(md)

    # markdown 直接写 stdout（技能执行后即可消费）；元信息走 stderr 避免污染内容
    sys.stdout.write(md if md.endswith('\n') else md + '\n')
    sys.stdout.flush()
    print(json.dumps({'success': True, 'out': args.out or None, 'blocks': len(blocks_map),
                      'title': title, 'doc_id': doc_id}, ensure_ascii=False), file=sys.stderr)


if __name__ == '__main__':
    main()

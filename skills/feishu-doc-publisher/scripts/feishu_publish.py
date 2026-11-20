#!/usr/bin/env python3
"""Feishu Doc Publisher - Publish Markdown to Feishu docs with optional template."""

import argparse, base64, json, os, re, sys, tempfile
import requests

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://open.feishu.cn/open-apis'
BT_TEXT, BT_BULLET, BT_ORDERED, BT_CODE, BT_QUOTE = 2, 12, 13, 14, 15
BT_UML = 21
BT_TABLE, BT_TABLE_CELL = 31, 32
LANG_MAP = {
    'java': 'Java', 'sql': 'SQL', 'python': 'Python', 'json': 'JSON',
    'javascript': 'JavaScript', 'yaml': 'YAML', 'bash': 'Bash', 'shell': 'Bash',
    'xml': 'XML', 'html': 'HTML', 'css': 'CSS', 'typescript': 'TypeScript',
    'go': 'Go', 'rust': 'Rust', 'c': 'C', 'cpp': 'Cpp', 'csharp': 'CSharp',
}

# --- Block builders ---

def te(text):
    return {'text_run': {'content': text, 'text_element_style': {}}}

def mk_heading(text, level=1):
    level = min(level, 4)
    keys = [None, 'heading1', 'heading2', 'heading3', 'heading4']
    bts = [0, 3, 4, 5, 6]
    return {'block_type': bts[level], keys[level]: {'elements': _parse_rich_elements(text), 'style': {}}}

def mk_text(text):
    return {'block_type': BT_TEXT, 'text': {'elements': _parse_rich_elements(text), 'style': {}}}

def mk_code(code, lang='PlainText'):
    return {'block_type': BT_CODE, 'code': {'language': lang, 'elements': [te(code)], 'style': {}}}

def mk_uml(mermaid_code):
    return {'block_type': 27, 'image': {}, '_mermaid_code': mermaid_code}

def mk_bullet(text):
    return {'block_type': BT_BULLET, 'bullet': {'elements': _parse_rich_elements(text), 'style': {}}}

def mk_ordered(text):
    return {'block_type': BT_ORDERED, 'ordered': {'elements': _parse_rich_elements(text), 'style': {}}}

def mk_quote(text):
    return {'block_type': BT_QUOTE, 'quote': {'elements': _parse_rich_elements(text), 'style': {}}}

def mk_table(headers, rows):
    cols = len(headers)
    all_rows = [headers] + rows
    col_width = [max(100, max(len(str(r[c] if c < len(r) else '')) for r in all_rows) * 10) for c in range(cols)]
    return {
        '_table_data': True,
        'headers': headers,
        'rows': rows,
        'cols': cols,
        'col_width': col_width,
    }

def _parse_rich_elements(text):
    elements = []
    pos = 0
    patterns = [
        (r'\*\*(.+?)\*\*', {'bold': True}),
        (r'\*(.+?)\*', {'italic': True}),
        (r'~~(.+?)~~', {'strikethrough': True}),
        (r'`(.+?)`', {'inline_code': True}),
        (r'\[(.+?)\]\((.+?)\)', {'link': True}),
    ]
    while pos < len(text):
        best_match, best_style, best_start = None, None, len(text)
        for pat, style in patterns:
            m = re.search(pat, text[pos:])
            if m and pos + m.start() < best_start:
                best_match = m
                best_style = style
                best_start = pos + m.start()
        if best_match:
            if best_start > pos:
                elements.append(te(text[pos:best_start]))
            link_url = best_match.group(2) if best_match.lastindex and best_match.lastindex >= 2 else None
            content = best_match.group(1)
            style_dict = dict(best_style)
            if link_url:
                # 飞书 text_element_style 不支持 link 字段（会导致 schema mismatch）
                # link 需要放在 text_run 顶层，但页内锚点(#xxx)飞书不支持，直接丢弃 link 样式
                style_dict.pop('link', None)
            tr = {'text_run': {'content': content, 'text_element_style': style_dict}}
            elements.append(tr)
            pos = best_start + best_match.end() - best_match.start()
        else:
            if pos < len(text):
                elements.append(te(text[pos:]))
            break
    return elements if elements else [te('')]

def _build_table_descendant(table_data, block_index):
    headers = table_data['headers']
    rows = table_data['rows']
    cols = table_data['cols']
    col_width = table_data['col_width']
    all_rows = [headers] + rows
    row_size = len(all_rows)

    table_bid = f'_tbl_{block_index}'
    cell_bids = []
    for ri in range(row_size):
        for ci in range(cols):
            cell_bids.append(f'_tc_{block_index}_{ri}_{ci}')

    table_property = {
        'row_size': row_size,
        'column_size': cols,
        'column_width': col_width,
        'header_row': True,
    }

    descendants = []
    table_block = {
        'block_id': table_bid,
        'block_type': BT_TABLE,
        'table': {'property': table_property},
        'children': cell_bids,
    }
    descendants.append(table_block)

    for ri in range(row_size):
        for ci in range(cols):
            cell_bid = f'_tc_{block_index}_{ri}_{ci}'
            text_bid = f'_tct_{block_index}_{ri}_{ci}'
            cell_text = str(all_rows[ri][ci] if ci < len(all_rows[ri]) else '')
            cell_elements = _parse_rich_elements(cell_text)
            descendants.append({
                'block_id': cell_bid,
                'block_type': BT_TABLE_CELL,
                'table_cell': {},
                'children': [text_bid],
            })
            descendants.append({
                'block_id': text_bid,
                'block_type': BT_TEXT,
                'text': {'elements': cell_elements, 'style': {}},
                'children': [],
            })

    return {
        'children_id': [table_bid],
        'descendants': descendants,
    }

# --- Markdown parsing ---

def parse_md(md):
    blocks, lines, i = [], md.split('\n'), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip() == '---':
            i += 1; continue
        if line.startswith('#'):
            lv = min(len(line.split(' ')[0]), 4)
            blocks.append(mk_heading(line.lstrip('#').strip(), lv))
            i += 1; continue
        if line.strip().startswith('```'):
            lang_raw = line.strip().lstrip('`').strip().lower()
            cl = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                cl.append(lines[i]); i += 1
            i += 1; ct = '\n'.join(cl)
            if lang_raw == 'mermaid':
                blocks.append(mk_uml(ct))
            else:
                lang = LANG_MAP.get(lang_raw, 'PlainText')
                while ct:
                    blocks.append(mk_code(ct[:60000], lang)); ct = ct[60000:]
            continue
        if line.strip().startswith('>'):
            blocks.append(mk_quote(line.strip().lstrip('>').strip())); i += 1; continue
        if line.strip().startswith('|') and '|' in line:
            tl = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tl.append(lines[i]); i += 1
            pr = []
            for t in tl:
                parts = t.strip().split('|')
                cs = [c.strip() for c in parts[1:-1]] if parts and parts[0] == '' and parts[-1] == '' else [c.strip() for c in parts if c.strip()]
                if not all(set(c) <= set('-: ') for c in cs): pr.append(cs)
            if pr:
                mc = max(len(r) for r in pr)
                for r in pr:
                    while len(r) < mc: r.append('')
                blocks.append(mk_table(pr[0], pr[1:]))
            continue
        if line.strip().startswith('- [ ]') or line.strip().startswith('- [x]'):
            blocks.append(mk_bullet(line.strip()[5:].strip())); i += 1; continue
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            blocks.append(mk_bullet(line.strip()[2:].strip())); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.+)', line.strip())
        if m:
            blocks.append(mk_ordered(m.group(2))); i += 1; continue
        blocks.append(mk_text(line.strip())); i += 1
    return blocks

# --- MD section grouping ---

def parse_md_sections(md):
    """Parse MD into sections by H1/H2 headings with their content blocks."""
    sections = []
    current = None
    content_lines = []
    for line in md.split('\n'):
        if line.startswith('#'):
            if current:
                current['blocks'] = parse_md('\n'.join(content_lines))
                sections.append(current)
            lv = min(len(line.split(' ')[0]), 4)
            current = {'heading': line.lstrip('#').strip(), 'level': lv, 'blocks': []}
            content_lines = []
        elif current is not None:
            content_lines.append(line)
    if current:
        current['blocks'] = parse_md('\n'.join(content_lines))
        sections.append(current)
    return sections

# --- Feishu client ---

class Client:
    def __init__(self, app_id, app_secret):
        self.app_id, self.app_secret, self.token = app_id, app_secret, None

    def auth(self):
        r = requests.post(f'{BASE_URL}/auth/v3/tenant_access_token/internal',
                          json={'app_id': self.app_id, 'app_secret': self.app_secret})
        d = r.json()
        if d['code'] != 0: raise Exception(f'Auth failed: {d["msg"]}')
        self.token = d['tenant_access_token']

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json; charset=utf-8'}

    def create_doc(self, title, folder_token=None):
        payload = {'title': title}
        if folder_token:
            payload['folder_token'] = folder_token
        r = requests.post(f'{BASE_URL}/docx/v1/documents', headers=self.headers, json=payload)
        d = r.json()
        if d['code'] != 0: raise Exception(f'Create failed: {d["msg"]}')
        return d['data']['document']['document_id']

    def add_blocks(self, doc_id, blocks):
        r = requests.post(f'{BASE_URL}/docx/v1/documents/{doc_id}/blocks/{doc_id}/children',
                          headers=self.headers, json={'children': blocks})
        d = r.json()
        if d['code'] != 0: raise Exception(f'Add blocks failed: {d["msg"]}')

    def add_descendant(self, doc_id, parent_block_id, descendant_data, index=-1):
        payload = {'children_id': descendant_data['children_id'], 'descendants': descendant_data['descendants']}
        if index >= 0:
            payload['index'] = index
        r = requests.post(
            f'{BASE_URL}/docx/v1/documents/{doc_id}/blocks/{parent_block_id}/descendant?document_revision_id=-1',
            headers=self.headers, json=payload)
        d = r.json()
        if d['code'] != 0:
            raise Exception(f'Add descendant failed: {d["msg"]}')

    def read_blocks(self, doc_id):
        all_blocks, page_token = [], None
        while True:
            url = f'{BASE_URL}/docx/v1/documents/{doc_id}/blocks/{doc_id}/children?page_size=50'
            if page_token: url += f'&page_token={page_token}'
            r = requests.get(url, headers=self.headers)
            d = r.json()
            if d['code'] != 0: raise Exception(f'Read blocks failed: {d["msg"]}')
            all_blocks.extend(d['data'].get('items', []))
            if not d['data'].get('has_more'): break
            page_token = d['data'].get('page_token')
        return all_blocks

    def resolve_wiki_token(self, wiki_token):
        r = requests.get(f'{BASE_URL}/wiki/v2/spaces/get_node?token={wiki_token}', headers=self.headers)
        d = r.json()
        if d['code'] != 0: raise Exception(f'Wiki resolve failed: {d["msg"]}')
        return d['data']['node']['obj_token']

    def add_members(self, doc_id, members):
        """Add members as collaborators to the document.
        
        Args:
            doc_id: Document ID
            members: List of dicts with keys: member_type (email/user_id/openid), 
                     member_id (the identifier), perm (view/edit)
        """
        r = requests.post(
            f'{BASE_URL}/drive/v1/permissions/{doc_id}/members?type=docx',
            headers=self.headers,
            json={'members': members, 'notify_lark': False}
        )
        d = r.json()
        if d['code'] != 0:
            print(f'Warning: Failed to add members: {d["msg"]}', file=sys.stderr)
        return d

    def transfer_owner(self, doc_id, member_type, member_id, stay_put=False, remove_old_owner=False, old_owner_perm='full_access'):
        """Transfer document ownership to a user.
        
        Args:
            doc_id: Document ID
            member_type: email, openid, or userid
            member_id: The user identifier
            stay_put: If true, keep document in original folder (default False, moves to new owner's space)
            remove_old_owner: If true, remove old owner's permissions (default False)
            old_owner_perm: Permission to keep for old owner: full_access, edit, view (default full_access)
        """
        r = requests.post(
            f'{BASE_URL}/drive/v1/permissions/{doc_id}/members/transfer_owner?type=docx&remove_old_owner={str(remove_old_owner).lower()}&stay_put={str(stay_put).lower()}',
            headers=self.headers,
            json={
                'member_type': member_type,
                'member_id': member_id,
                'old_owner_perm': old_owner_perm
            }
        )
        d = r.json()
        if d['code'] != 0:
            print(f'Warning: Failed to transfer owner: {d["msg"]}', file=sys.stderr)
        return d

    def set_internal_only(self, doc_id):
        """Set document to not allow sharing outside the organization."""
        r = requests.patch(
            f'{BASE_URL}/drive/v2/permissions/{doc_id}/public?type=docx',
            headers=self.headers,
            json={
                'external_access_entity': 'closed',
                'link_share_entity': 'closed',
                'share_entity': 'same_tenant',
                'manage_collaborator_entity': 'collaborator_full_access'
            }
        )
        d = r.json()
        if d['code'] != 0:
            print(f'Warning: Failed to set internal-only permission: {d["msg"]}', file=sys.stderr)

    def upload_image_for_block(self, doc_id, block_id, image_path):
        headers = {'Authorization': f'Bearer {self.token}'}
        file_size = os.path.getsize(image_path)
        with open(image_path, 'rb') as f:
            r = requests.post(
                f'{BASE_URL}/drive/v1/medias/upload_all',
                headers=headers,
                data={
                    'file_name': 'mermaid.png',
                    'parent_type': 'docx_image',
                    'parent_node': block_id,
                    'size': str(file_size),
                },
                files={'file': ('mermaid.png', f, 'image/png')})
            d = r.json()
            if d['code'] != 0:
                print(f'Warning: Image upload failed for block {block_id}: {d["msg"]}', file=sys.stderr)
                return None
            return d['data']['file_token']

    def replace_image_block(self, doc_id, block_id, image_token):
        r = requests.patch(
            f'{BASE_URL}/docx/v1/documents/{doc_id}/blocks/{block_id}?document_revision_id=-1',
            headers=self.headers,
            json={'replace_image': {'token': image_token}})
        d = r.json()
        if d['code'] != 0:
            print(f'Warning: Replace image failed for block {block_id}: {d["msg"]}', file=sys.stderr)

# --- Mermaid rendering ---

def render_mermaid_to_png(mermaid_code):
    # 优先使用 mermaid.ink（更稳定），失败后回退 kroki.io
    try:
        encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('ascii')
        url = f'https://mermaid.ink/img/{encoded}?type=png&bgColor=white&width=2400'
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 100:
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception as e:
        print(f'Warning: mermaid.ink render failed: {e}', file=sys.stderr)
    # 回退到 kroki.io
    try:
        r = requests.post('https://kroki.io/mermaid/png', json={'diagram_source': mermaid_code}, timeout=60)
        if r.status_code == 200 and len(r.content) > 100:
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception as e:
        print(f'Warning: kroki.io render failed: {e}', file=sys.stderr)
    return None

def _add_blocks_with_ids(client, doc_id, blocks):
    r = requests.post(f'{BASE_URL}/docx/v1/documents/{doc_id}/blocks/{doc_id}/children',
                      headers=client.headers, json={'children': blocks})
    d = r.json()
    if d['code'] != 0:
        raise Exception(f'Add blocks failed: {d["msg"]}')
    return d.get('data', {}).get('children', [])

# --- Template parsing from Feishu blocks ---

HEADING_BT_TO_LEVEL = {3: 1, 4: 2, 5: 3, 6: 4}
HEADING_KEYS = ['heading1', 'heading2', 'heading3', 'heading4']

def _extract_elements_text(elements):
    parts = []
    for e in elements:
        tr = e.get('text_run')
        if tr: parts.append(tr.get('content', ''))
    return ''.join(parts).strip()

def _block_heading_text(block):
    for k in HEADING_KEYS:
        h = block.get(k)
        if h: return _extract_elements_text(h.get('elements', []))
    return None

def _convert_template_block(b):
    """Convert a Feishu template block to a new block for output."""
    bt = b.get('block_type', 0)
    if bt in HEADING_BT_TO_LEVEL:
        return mk_heading(_block_heading_text(b) or '', HEADING_BT_TO_LEVEL[bt])
    if bt == BT_TEXT:
        t = b.get('text', {})
        return mk_text(_extract_elements_text(t.get('elements', [])))
    if bt == BT_BULLET:
        bl = b.get('bullet', {})
        return mk_bullet(_extract_elements_text(bl.get('elements', [])))
    if bt == BT_ORDERED:
        ol = b.get('ordered', {})
        return mk_ordered(_extract_elements_text(ol.get('elements', [])))
    if bt == BT_CODE:
        cl = b.get('code', {})
        return mk_code(_extract_elements_text(cl.get('elements', [])), cl.get('language', 'PlainText'))
    if bt == BT_QUOTE:
        ql = b.get('quote', {})
        return {'block_type': BT_QUOTE, 'quote': {'elements': [te(_extract_elements_text(ql.get('elements', [])))], 'style': {}}}
    return mk_text('')

def parse_template_from_blocks(blocks):
    """Parse Feishu blocks into sections grouped by H1 headings, with H2 sub-sections."""
    sections = []
    current_h1 = None
    current_h2 = None
    h1_content = []  # blocks under H1 but before any H2

    for b in blocks:
        bt = b.get('block_type', 0)
        heading = _block_heading_text(b)
        level = HEADING_BT_TO_LEVEL.get(bt, 0)

        if level == 1:
            if current_h1:
                current_h1['children'].extend(h1_content)
                sections.append(current_h1)
            current_h1 = {'heading': heading, 'level': 1, 'children': []}
            h1_content = []
            current_h2 = None
        elif level == 2 and current_h1 is not None:
            h1_content.append({'heading': heading, 'level': 2, 'blocks': []})
            current_h2 = h1_content[-1]
        elif level >= 3 and current_h2 is not None:
            current_h2['blocks'].append(_convert_template_block(b))
        elif current_h1 is not None and level == 0:
            # Non-heading block under current context
            if current_h2:
                current_h2['blocks'].append(_convert_template_block(b))
            else:
                h1_content.append(_convert_template_block(b))

    if current_h1:
        current_h1['children'].extend(h1_content)
        sections.append(current_h1)
    return sections

# --- Heading matching ---

def _normalize(h):
    h = re.sub(r'^[\d.]+\s*', '', h.strip().lower())
    return re.sub(r'[^a-z\u4e00-\u9fff0-9]', '', h)

def _similarity(h1, h2):
    n1, n2 = _normalize(h1), _normalize(h2)
    if n1 == n2: return 1.0
    if n1 in n2 or n2 in n1:
        return min(len(n1), len(n2)) / max(len(n1), len(n2))
    w1 = set(re.findall(r'[\u4e00-\u9fff]{2,}', n1))
    w2 = set(re.findall(r'[\u4e00-\u9fff]{2,}', n2))
    if not w1 or not w2: return 0
    return len(w1 & w2) / min(len(w1), len(w2))

def _find_best(heading, candidates, used):
    best_j, best_sc = None, 0
    for j, ch in enumerate(candidates):
        if j in used: continue
        sc = _similarity(heading, ch)
        if sc > best_sc: best_j, best_sc = j, sc
    return best_j if best_sc >= 0.3 else None

# --- Section grouping for MD ---

def _group_md_h1(md_sections):
    """Group MD sections by H1, collecting H2 children."""
    groups = []
    for s in md_sections:
        if s['level'] == 1:
            groups.append({'heading': s['heading'], 'children': []})
        if not groups: continue
        if s['level'] >= 2:
            groups[-1]['children'].append(s)
    return groups

# --- Merge ---

def _enrich_h2_with_children(md_sections):
    """Fold H3+ children's blocks into parent H2 sections so no content is lost."""
    h2_list = []
    for s in md_sections:
        if s['level'] == 2:
            h2_list.append({'heading': s['heading'], 'blocks': list(s['blocks'])})
        elif h2_list and s['level'] >= 3:
            h2_list[-1]['blocks'].append(mk_heading(s['heading'], s['level']))
            h2_list[-1]['blocks'].extend(s['blocks'])
    return h2_list

def merge_with_template(template_sections, md_text):
    """Merge MD content into template structure.

    Strategy:
    1. Collect all MD H2 sections enriched with H3+ children
    2. For each template H1, find best-matching MD H2 sections via keyword overlap
    3. For template H2 sub-sections, try exact/fuzzy match first, then keyword group
    4. Append ALL unmatched MD content at the end (never discard)
    """
    md_sections = parse_md_sections(md_text)
    all_md_h2 = _enrich_h2_with_children(md_sections)

    result = []
    used_md_h2 = set()

    # Phase 1: Assign each MD H2 to best template H1 via similarity scoring
    # Build assignment: md_h2_index -> template_h1_index
    md_to_tpl = {}
    for mi, mh2 in enumerate(all_md_h2):
        best_ti, best_sc = None, 0
        mn = _normalize(mh2['heading'])
        for ti, ts in enumerate(template_sections):
            sc = _similarity(ts['heading'], mh2['heading'])
            if sc > best_sc: best_ti, best_sc = ti, sc
        if best_ti is not None and best_sc >= 0.15:
            md_to_tpl[mi] = best_ti

    # Phase 2: For each template section, produce output
    for ti, ts in enumerate(template_sections):
        result.append(mk_heading(ts['heading'], 1))
        tpl_h2s = [c for c in ts.get('children', []) if isinstance(c, dict) and c.get('level') == 2]

        # MD H2s assigned to this template H1
        my_md_h2s = [mi for mi, t in md_to_tpl.items() if t == ti]

        if tpl_h2s:
            # Template has H2 sub-sections: try to match each
            for th2 in tpl_h2s:
                result.append(mk_heading(th2['heading'], 2))
                # Find best matching MD H2 from my assigned ones
                best_mi, best_sc = None, 0
                for mi in my_md_h2s:
                    if mi in used_md_h2: continue
                    sc = _similarity(th2['heading'], all_md_h2[mi]['heading'])
                    if sc > best_sc: best_mi, best_sc = mi, sc
                if best_mi is not None and best_sc >= 0.2:
                    used_md_h2.add(best_mi)
                    result.extend(all_md_h2[best_mi]['blocks'])
                else:
                    result.extend(th2.get('blocks', []))
            # Add remaining unmatched MD H2s for this H1 group
            for mi in my_md_h2s:
                if mi not in used_md_h2:
                    used_md_h2.add(mi)
                    result.append(mk_heading(all_md_h2[mi]['heading'], 2))
                    result.extend(all_md_h2[mi]['blocks'])
        else:
            # Template H1 has no H2 sub-sections: put all matched MD H2 content directly
            for mi in my_md_h2s:
                if mi not in used_md_h2:
                    used_md_h2.add(mi)
                    result.extend(all_md_h2[mi]['blocks'])

    # Append any unmatched MD H2 at the end
    for mi, mh2 in enumerate(all_md_h2):
        if mi not in used_md_h2:
            result.append(mk_heading(mh2['heading'], 2))
            result.extend(mh2['blocks'])

    return result

# --- URL/ID parsing ---

def extract_doc_id(template_ref):
    m = re.search(r'/docx/([a-zA-Z0-9]+)', template_ref)
    if m: return ('docx', m.group(1))
    m = re.search(r'/wiki/([a-zA-Z0-9]+)', template_ref)
    if m: return ('wiki', m.group(1))
    return None, None

# --- Config ---

def load_config(path=None):
    cfg = {'app_id': '', 'app_secret': '', 'folder_token': None}
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f: cfg.update(json.load(f))
    if not cfg['app_id']:
        p = os.path.expanduser('~/.claude/feishu_config.json')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f: cfg.update(json.load(f))
    cfg['app_id'] = cfg['app_id'] or os.environ.get('FEISHU_APP_ID', '')
    cfg['app_secret'] = cfg['app_secret'] or os.environ.get('FEISHU_APP_SECRET', '')
    return cfg

# --- Main publish ---

def _parse_owner(owner_str):
    """Parse owner from CLI argument.
    
    Format: email:user@example.com or openid:ou_xxx or userid:123456
    """
    if owner_str:
        parts = owner_str.split(':', 1)
        if len(parts) == 2:
            return (parts[0], parts[1])
    return None

def publish(title, md, app_id, app_secret, template=None, owner=None, folder_token=None):
    c = Client(app_id, app_secret)
    c.auth()
    doc_id = c.create_doc(title, folder_token=folder_token)

    if template:
        kind, ref_id = extract_doc_id(template)
        if kind and ref_id:
            actual_id = ref_id
            if kind == 'wiki':
                actual_id = c.resolve_wiki_token(ref_id)
            blocks = c.read_blocks(actual_id)
            tpl_sections = parse_template_from_blocks(blocks)
            if tpl_sections:
                blocks = merge_with_template(tpl_sections, md)
            else:
                blocks = parse_md(md)
        elif os.path.exists(template):
            tpl_md = open(template, 'r', encoding='utf-8').read()
            tpl_sections = parse_md_sections(tpl_md)
            blocks = merge_with_template(tpl_sections, md)
        else:
            blocks = parse_md(md)
    else:
        blocks = parse_md(md)

    segments = []
    current_normal = []
    mermaid_positions = {}
    for bidx, b in enumerate(blocks):
        if b.get('_table_data'):
            if current_normal:
                segments.append(('normal', current_normal))
                current_normal = []
            segments.append(('table', b))
        else:
            mc = b.pop('_mermaid_code', None)
            if mc is not None:
                mermaid_positions[bidx] = mc
            current_normal.append(b)
    if current_normal:
        segments.append(('normal', current_normal))

    next_index = 0
    table_counter = 0
    block_id_map = {}
    for seg_idx, (seg_type, seg_data) in enumerate(segments):
        if seg_type == 'normal':
            for off in range(0, len(seg_data), 50):
                batch = seg_data[off:off+50]
                try:
                    resp = _add_blocks_with_ids(c, doc_id, batch)
                except Exception as e:
                    # 打印失败批次的详细信息用于定位
                    print(f'ERROR at segment {seg_idx}, offset {off}, batch size {len(batch)}:', file=sys.stderr)
                    for bi, blk in enumerate(batch):
                        bt = blk.get('block_type', '?')
                        preview = json.dumps(blk, ensure_ascii=False)[:200]
                        print(f'  block[{bi}] type={bt}: {preview}', file=sys.stderr)
                    raise
                for bi, rb in enumerate(resp):
                    block_id_map[next_index + bi] = rb.get('block_id', '')
                next_index += len(batch)
        elif seg_type == 'table':
            desc = _build_table_descendant(seg_data, table_counter)
            c.add_descendant(doc_id, doc_id, desc, index=next_index)
            next_index += 1
            table_counter += 1

    for bidx, mermaid_code in mermaid_positions.items():
        block_id = block_id_map.get(bidx)
        if not block_id:
            continue
        png_path = render_mermaid_to_png(mermaid_code)
        if png_path:
            try:
                image_token = c.upload_image_for_block(doc_id, block_id, png_path)
                if image_token:
                    c.replace_image_block(doc_id, block_id, image_token)
            finally:
                try:
                    os.unlink(png_path)
                except OSError:
                    pass

    if owner:
        c.transfer_owner(doc_id, owner[0], owner[1])

    c.set_internal_only(doc_id)
    return f'https://bytedance.larkoffice.com/docx/{doc_id}', doc_id

def main():
    p = argparse.ArgumentParser(description='Publish Markdown to Feishu Doc')
    p.add_argument('--title', required=True)
    p.add_argument('--file')
    p.add_argument('--content')
    p.add_argument('--config')
    p.add_argument('--app-id')
    p.add_argument('--app-secret')
    p.add_argument('--template', help='Template: Feishu doc/wiki URL or local .md file')
    p.add_argument('--owner', help='Transfer ownership to user. Format: type:id (e.g., email:user@example.com, openid:ou_xxx)')
    p.add_argument('--folder', help='Folder token to create document in. Get from folder URL.')
    a = p.parse_args()
    if not a.file and not a.content: p.error('Either --file or --content required')
    md = open(a.file, 'r', encoding='utf-8').read() if a.file else a.content
    cfg = load_config(a.config)
    aid, sec = a.app_id or cfg['app_id'], a.app_secret or cfg['app_secret']
    if not aid or not sec:
        print(json.dumps({'error': 'Missing app_id/app_secret'})); sys.exit(1)
    
    owner = _parse_owner(a.owner)
    folder = a.folder or cfg.get('folder_token')
    
    try:
        url, did = publish(a.title, md, aid, sec, template=a.template, owner=owner, folder_token=folder)
        result = {'success': True, 'url': url, 'doc_id': did, 'template_used': bool(a.template)}
        if owner: result['owner'] = owner[1]
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False)); sys.exit(1)

if __name__ == '__main__':
    main()

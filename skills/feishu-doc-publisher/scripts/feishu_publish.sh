#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://open.feishu.cn/open-apis"

CONFIG_PATH=""
APP_ID=""
APP_SECRET=""
DOC_TITLE=""
MD_FILE=""
MD_CONTENT=""
TEMPLATE=""
OWNER=""
FOLDER=""
TOKEN=""
DOC_ID=""

usage() {
    cat <<'HELP'
Usage: feishu_publish.sh [OPTIONS]

Options:
  --title TITLE        Document title (required)
  --file FILE          Markdown file path
  --content TEXT       Markdown content string
  --config PATH        Config JSON file path
  --app-id ID          Feishu App ID
  --app-secret SECRET  Feishu App Secret
  --template REF       Template: Feishu doc/wiki URL or local .md file
  --owner TYPE:ID      Transfer ownership (e.g., email:user@example.com)
  --folder TOKEN       Folder token to create document in
  -h, --help           Show this help
HELP
    exit 0
}

die() { echo "ERROR: $*" >&2; exit 1; }
log_warn() { echo "Warning: $*" >&2; }

_json_val() {
    local key="$1"
    echo -n "$key" > /tmp/_feishu_json_key
    python3 << 'JEOF' 2>/dev/null
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
key = open("/tmp/_feishu_json_key", "r").read().strip()
keys = key.split(".")
v = d
for k in keys:
    if isinstance(v, dict) and k in v:
        v = v[k]
    else:
        v = None
        break
if v is not None:
    if isinstance(v, str):
        print(v)
    else:
        print(json.dumps(v, ensure_ascii=False))
JEOF
}

json_code() {
    python3 << 'JEOF2' 2>/dev/null
import sys, json
try:
    print(json.load(sys.stdin).get("code", -1))
except Exception:
    print(-1)
JEOF2
}

_json_val() {
    local key="$1"
    echo -n "$key" > /tmp/_feishu_json_key
    python3 << 'JEOF' 2>/dev/null
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
key = open("/tmp/_feishu_json_key", "r").read().strip()
keys = key.split(".")
v = d
for k in keys:
    if isinstance(v, dict) and k in v:
        v = v[k]
    else:
        v = None
        break
if v is not None:
    if isinstance(v, str):
        print(v)
    else:
        print(json.dumps(v, ensure_ascii=False))
JEOF
}

json_code() {
    python3 << 'JEOF2' 2>/dev/null
import sys, json
try:
    print(json.load(sys.stdin).get("code", -1))
except Exception:
    print(-1)
JEOF2
}

load_config() {
    local path="${CONFIG_PATH:-}"
    local default_path="$HOME/.claude/feishu_config.json"
    local cfg_path=""

    if [[ -n "$path" && -f "$path" ]]; then
        cfg_path="$path"
    elif [[ -f "$default_path" ]]; then
        cfg_path="$default_path"
    fi

    if [[ -n "$cfg_path" ]]; then
        local data
        data=$(cat "$cfg_path")
        : "${APP_ID:=$(echo "$data" | _json_val "app_id")}"
        : "${APP_SECRET:=$(echo "$data" | _json_val "app_secret")}"
        : "${FOLDER:=$(echo "$data" | _json_val "folder_token")}"
    fi

    : "${APP_ID:=${FEISHU_APP_ID:-}}"
    : "${APP_SECRET:=${FEISHU_APP_SECRET:-}}"
}

feishu_auth() {
    local payload
    payload=$(python3 << 'AEOF'
import json, sys
app_id = open("/tmp/_feishu_app_id", "r").read().strip()
app_secret = open("/tmp/_feishu_app_secret", "r").read().strip()
print(json.dumps({"app_id": app_id, "app_secret": app_secret}))
AEOF
)
    local resp
    resp=$(curl -s -X POST "${BASE_URL}/auth/v3/tenant_access_token/internal" \
        -H "Content-Type: application/json" \
        -d "$payload")
    local code
    code=$(echo "$resp" | json_code)
    if [[ "$code" != "0" ]]; then
        local msg
        msg=$(echo "$resp" | _json_val "msg")
        die "Auth failed: $msg"
    fi
    TOKEN=$(echo "$resp" | _json_val "tenant_access_token")
}

feishu_create_doc() {
    local title="$1"
    echo -n "$title" > /tmp/_feishu_title
    echo -n "${FOLDER:-}" > /tmp/_feishu_folder
    local payload
    payload=$(python3 << 'CEOF'
import json
title = open("/tmp/_feishu_title", "r").read()
folder = open("/tmp/_feishu_folder", "r").read().strip()
d = {"title": title}
if folder and folder != "None":
    d["folder_token"] = folder
print(json.dumps(d))
CEOF
)
    local resp
    resp=$(curl -s -X POST "${BASE_URL}/docx/v1/documents" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json; charset=utf-8" \
        -d "$payload")
    local code
    code=$(echo "$resp" | json_code)
    if [[ "$code" != "0" ]]; then
        local msg
        msg=$(echo "$resp" | _json_val "msg")
        die "Create failed: $msg"
    fi
    DOC_ID=$(echo "$resp" | python3 << 'DIDEOF'
import sys, json
d = json.load(sys.stdin)
print(d["data"]["document"]["document_id"])
DIDEOF
)
}

feishu_add_blocks() {
    local doc_id="$1"
    echo -n "$doc_id" > /tmp/_feishu_doc_id
    local blocks_json="$2"
    echo -n "$blocks_json" > /tmp/_feishu_blocks_json
    local payload
    payload=$(python3 << 'ABEOF'
import json
blocks = json.loads(open("/tmp/_feishu_blocks_json", "r").read())
print(json.dumps({"children": blocks}))
ABEOF
)
    local resp
    resp=$(curl -s -X POST "${BASE_URL}/docx/v1/documents/${doc_id}/blocks/${doc_id}/children" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json; charset=utf-8" \
        -d "$payload")
    local code
    code=$(echo "$resp" | json_code)
    if [[ "$code" != "0" ]]; then
        local msg
        msg=$(echo "$resp" | _json_val "msg")
        die "Add blocks failed: $msg"
    fi
}

feishu_read_blocks() {
    local doc_id="$1"
    local result=""
    local page_token=""
    while true; do
        local url="${BASE_URL}/docx/v1/documents/${doc_id}/blocks/${doc_id}/children?page_size=50"
        [[ -n "$page_token" ]] && url="${url}&page_token=${page_token}"
        local resp
        resp=$(curl -s -X GET "$url" \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "Content-Type: application/json")
        local code
        code=$(echo "$resp" | json_code)
        if [[ "$code" != "0" ]]; then
            local msg
            msg=$(echo "$resp" | _json_val "msg")
            die "Read blocks failed: $msg"
        fi
        # Save resp and result to temp files for python processing
        echo "$resp" > /tmp/_feishu_resp
        echo -n "$result" > /tmp/_feishu_result
        result=$(python3 << 'RBEOF'
import json
resp = json.loads(open("/tmp/_feishu_resp", "r").read())
prev = open("/tmp/_feishu_result", "r").read().strip()
items = resp.get("data", {}).get("items", [])
if prev:
    prev_list = json.loads(prev)
    print(json.dumps(prev_list + items))
else:
    print(json.dumps(items))
RBEOF
)
        local has_more
        has_more=$(echo "$resp" | python3 << 'HEOF'
import sys, json
print(str(json.load(sys.stdin).get("data", {}).get("has_more", False)).lower())
HEOF
)
        [[ "$has_more" != "true" ]] && break
        page_token=$(echo "$resp" | python3 << 'PEOF'
import sys, json
print(json.load(sys.stdin).get("data", {}).get("page_token", ""))
PEOF
)
    done
    echo "$result"
}

feishu_resolve_wiki() {
    local wiki_token="$1"
    local resp
    resp=$(curl -s -X GET "${BASE_URL}/wiki/v2/spaces/get_node?token=${wiki_token}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json")
    local code
    code=$(echo "$resp" | json_code)
    if [[ "$code" != "0" ]]; then
        local msg
        msg=$(echo "$resp" | _json_val "msg")
        die "Wiki resolve failed: $msg"
    fi
    echo "$resp" | python3 << 'WEOF'
import sys, json
print(json.load(sys.stdin)["data"]["node"]["obj_token"])
WEOF
}

feishu_transfer_owner() {
    local doc_id="$1" member_type="$2" member_id="$3"
    echo -n "$member_type" > /tmp/_feishu_mtype
    echo -n "$member_id" > /tmp/_feishu_mid
    local payload
    payload=$(python3 << 'TOEOF'
import json
mtype = open("/tmp/_feishu_mtype", "r").read().strip()
mid = open("/tmp/_feishu_mid", "r").read().strip()
print(json.dumps({"member_type": mtype, "member_id": mid, "old_owner_perm": "full_access"}))
TOEOF
)
    local resp
    resp=$(curl -s -X POST \
        "${BASE_URL}/drive/v1/permissions/${doc_id}/members/transfer_owner?type=docx&remove_old_owner=false&stay_put=false" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$payload")
    local code
    code=$(echo "$resp" | json_code)
    if [[ "$code" != "0" ]]; then
        local msg
        msg=$(echo "$resp" | _json_val "msg")
        log_warn "Failed to transfer owner: $msg"
    fi
}

feishu_set_internal_only() {
    local doc_id="$1"
    local payload='{"external_access_entity":"closed","link_share_entity":"closed","share_entity":"same_tenant","manage_collaborator_entity":"collaborator_full_access"}'
    local resp
    resp=$(curl -s -X PATCH \
        "${BASE_URL}/drive/v2/permissions/${doc_id}/public?type=docx" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$payload")
    local code
    code=$(echo "$resp" | json_code)
    if [[ "$code" != "0" ]]; then
        local msg
        msg=$(echo "$resp" | _json_val "msg")
        log_warn "Failed to set internal-only permission: $msg"
    fi
}

parse_md_to_blocks() {
    local md="$1"
    echo -n "$md" > /tmp/_feishu_md
    python3 << 'PARSEEOF'
import json, re, sys

BT_TEXT, BT_BULLET, BT_ORDERED, BT_CODE, BT_QUOTE = 2, 12, 13, 14, 15
LANG_MAP = {'java':'Java','sql':'SQL','python':'Python','json':'JSON','javascript':'JavaScript','yaml':'YAML','bash':'Bash','shell':'Bash','xml':'XML','html':'HTML','css':'CSS','typescript':'TypeScript','go':'Go','rust':'Rust','c':'C','cpp':'Cpp','csharp':'CSharp'}

def te(text):
    return {'text_run': {'content': text, 'text_element_style': {}}}

def mk_heading(text, level=1):
    level = min(level, 4)
    keys = [None, 'heading1', 'heading2', 'heading3', 'heading4']
    bts = [0, 3, 4, 5, 6]
    return {'block_type': bts[level], keys[level]: {'elements': [te(text)], 'style': {}}}

def mk_text(text):
    return {'block_type': BT_TEXT, 'text': {'elements': [te(text)], 'style': {}}}

def mk_code(code, lang="PlainText"):
    return {'block_type': BT_CODE, 'code': {'language': lang, 'elements': [te(code)], 'style': {}}}

def mk_bullet(text):
    return {'block_type': BT_BULLET, 'bullet': {'elements': [te(text)], 'style': {}}}

def mk_ordered(text):
    return {'block_type': BT_ORDERED, 'ordered': {'elements': [te(text)], 'style': {}}}

def mk_table(headers, rows):
    cols = len(headers)
    all_r = [headers] + rows
    ws = [max(len(str(r[c] if c < len(r) else "")) for r in all_r) for c in range(cols)]
    ws = [max(w, 6) for w in ws]
    lines = ["| " + " | ".join(str(h).ljust(ws[i]) for i, h in enumerate(headers)) + " |",
             "| " + " | ".join("-" * ws[i] for i in range(cols)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row[i] if i < len(row) else "").ljust(ws[i]) for i in range(cols)) + " |")
    return mk_code(chr(10).join(lines))

def parse_md(md):
    blocks, lines, i = [], md.split(chr(10)), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip() == '---':
            i += 1; continue
        if line.startswith('#'):
            lv = min(len(line.split(' ')[0]), 4)
            blocks.append(mk_heading(line.lstrip('#').strip(), lv))
            i += 1; continue
        if line.strip().startswith(chr(96)*3):
            lang = LANG_MAP.get(line.strip().lstrip(chr(96)).strip().lower(), 'PlainText')
            cl = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith(chr(96)*3):
                cl.append(lines[i]); i += 1
            i += 1; ct = chr(10).join(cl)
            while ct:
                blocks.append(mk_code(ct[:3000], lang)); ct = ct[3000:]
            continue
        if line.strip().startswith('|') and '|' in line:
            tl = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tl.append(lines[i]); i += 1
            pr = []
            for t in tl:
                cs = [c.strip() for c in t.strip().split('|') if c.strip()]
                if not all(set(c) <= set('-: ') for c in cs): pr.append(cs)
            if pr:
                mc = max(len(r) for r in pr)
                for r in pr:
                    while len(r) < mc: r.append('')
                blocks.append(mk_table(pr[0], pr[1:]))
            continue
        if line.strip().startswith('- [ ]') or line.strip().startswith('- [x]'):
            blocks.append(mk_bullet(line.strip()[5:].strip().replace('**', ''))); i += 1; continue
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            blocks.append(mk_bullet(line.strip()[2:].strip().replace('**', ''))); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.+)', line.strip())
        if m:
            blocks.append(mk_ordered(m.group(2).replace('**', ''))); i += 1; continue
        blocks.append(mk_text(line.strip().replace('**', ''))); i += 1
    return blocks

md = open("/tmp/_feishu_md", "r", encoding="utf-8").read()
blocks = parse_md(md)
print(json.dumps(blocks, ensure_ascii=False))
PARSEEOF
}

merge_with_template() {
    local md="$1"
    local template_blocks="$2"
    echo -n "$md" > /tmp/_feishu_merge_md
    echo -n "$template_blocks" > /tmp/_feishu_merge_tpl
    python3 << 'MERGEEOF'
import json, re, sys

BT_TEXT, BT_BULLET, BT_ORDERED, BT_CODE, BT_QUOTE = 2, 12, 13, 14, 15
HEADING_BT_TO_LEVEL = {3: 1, 4: 2, 5: 3, 6: 4}
HEADING_KEYS = ['heading1', 'heading2', 'heading3', 'heading4']
LANG_MAP = {'java':'Java','sql':'SQL','python':'Python','json':'JSON','javascript':'JavaScript','yaml':'YAML','bash':'Bash','shell':'Bash','xml':'XML','html':'HTML','css':'CSS','typescript':'TypeScript','go':'Go','rust':'Rust','c':'C','cpp':'Cpp','csharp':'CSharp'}

def te(text):
    return {'text_run': {'content': text, 'text_element_style': {}}}
def mk_heading(text, level=1):
    level = min(level, 4)
    keys = [None, 'heading1', 'heading2', 'heading3', 'heading4']
    bts = [0, 3, 4, 5, 6]
    return {'block_type': bts[level], keys[level]: {'elements': [te(text)], 'style': {}}}
def mk_text(text):
    return {'block_type': BT_TEXT, 'text': {'elements': [te(text)], 'style': {}}}
def mk_code(code, lang="PlainText"):
    return {'block_type': BT_CODE, 'code': {'language': lang, 'elements': [te(code)], 'style': {}}}
def mk_bullet(text):
    return {'block_type': BT_BULLET, 'bullet': {'elements': [te(text)], 'style': {}}}
def mk_ordered(text):
    return {'block_type': BT_ORDERED, 'ordered': {'elements': [te(text)], 'style': {}}}
def mk_quote(text):
    return {'block_type': BT_QUOTE, 'quote': {'elements': [te(text)], 'style': {}}}
def mk_table(headers, rows):
    cols = len(headers)
    all_r = [headers] + rows
    ws = [max(len(str(r[c] if c < len(r) else "")) for r in all_r) for c in range(cols)]
    ws = [max(w, 6) for w in ws]
    lines = ["| " + " | ".join(str(h).ljust(ws[i]) for i, h in enumerate(headers)) + " |",
             "| " + " | ".join("-" * ws[i] for i in range(cols)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row[i] if i < len(row) else "").ljust(ws[i]) for i in range(cols)) + " |")
    return mk_code(chr(10).join(lines))

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
        return mk_quote(_extract_elements_text(ql.get('elements', [])))
    return mk_text('')

def parse_template_from_blocks(blocks):
    sections = []
    current_h1 = None
    current_h2 = None
    h1_content = []
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
            if current_h2:
                current_h2['blocks'].append(_convert_template_block(b))
            else:
                h1_content.append(_convert_template_block(b))
    if current_h1:
        current_h1['children'].extend(h1_content)
        sections.append(current_h1)
    return sections

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

def _enrich_h2_with_children(md_sections):
    h2_list = []
    for s in md_sections:
        if s['level'] == 2:
            h2_list.append({'heading': s['heading'], 'blocks': list(s['blocks'])})
        elif h2_list and s['level'] >= 3:
            h2_list[-1]['blocks'].append(mk_heading(s['heading'], s['level']))
            h2_list[-1]['blocks'].extend(s['blocks'])
    return h2_list

def parse_md_sections(md):
    sections = []
    current = None
    content_lines = []
    for line in md.split(chr(10)):
        if line.startswith('#'):
            if current:
                current['blocks'] = parse_md_inner(chr(10).join(content_lines))
                sections.append(current)
            lv = min(len(line.split(' ')[0]), 4)
            current = {'heading': line.lstrip('#').strip(), 'level': lv, 'blocks': []}
            content_lines = []
        elif current is not None:
            content_lines.append(line)
    if current:
        current['blocks'] = parse_md_inner(chr(10).join(content_lines))
        sections.append(current)
    return sections

def parse_md_inner(md):
    blocks, lines, i = [], md.split(chr(10)), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip() == '---':
            i += 1; continue
        if line.startswith('#'):
            lv = min(len(line.split(' ')[0]), 4)
            blocks.append(mk_heading(line.lstrip('#').strip(), lv))
            i += 1; continue
        if line.strip().startswith(chr(96)*3):
            lang = LANG_MAP.get(line.strip().lstrip(chr(96)).strip().lower(), 'PlainText')
            cl = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith(chr(96)*3):
                cl.append(lines[i]); i += 1
            i += 1; ct = chr(10).join(cl)
            while ct:
                blocks.append(mk_code(ct[:3000], lang)); ct = ct[3000:]
            continue
        if line.strip().startswith('|') and '|' in line:
            tl = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tl.append(lines[i]); i += 1
            pr = []
            for t in tl:
                cs = [c.strip() for c in t.strip().split('|') if c.strip()]
                if not all(set(c) <= set('-: ') for c in cs): pr.append(cs)
            if pr:
                mc = max(len(r) for r in pr)
                for r in pr:
                    while len(r) < mc: r.append('')
                blocks.append(mk_table(pr[0], pr[1:]))
            continue
        if line.strip().startswith('- [ ]') or line.strip().startswith('- [x]'):
            blocks.append(mk_bullet(line.strip()[5:].strip().replace('**', ''))); i += 1; continue
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            blocks.append(mk_bullet(line.strip()[2:].strip().replace('**', ''))); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.+)', line.strip())
        if m:
            blocks.append(mk_ordered(m.group(2).replace('**', ''))); i += 1; continue
        blocks.append(mk_text(line.strip().replace('**', ''))); i += 1
    return blocks

def merge_with_template_inner(template_sections, md_text):
    md_sections = parse_md_sections(md_text)
    all_md_h2 = _enrich_h2_with_children(md_sections)
    result = []
    used_md_h2 = set()
    md_to_tpl = {}
    for mi, mh2 in enumerate(all_md_h2):
        best_ti, best_sc = None, 0
        for ti, ts in enumerate(template_sections):
            sc = _similarity(ts['heading'], mh2['heading'])
            if sc > best_sc: best_ti, best_sc = ti, sc
        if best_ti is not None and best_sc >= 0.15:
            md_to_tpl[mi] = best_ti
    for ti, ts in enumerate(template_sections):
        result.append(mk_heading(ts['heading'], 1))
        tpl_h2s = [c for c in ts.get('children', []) if isinstance(c, dict) and c.get('level') == 2]
        my_md_h2s = [mi for mi, t in md_to_tpl.items() if t == ti]
        if tpl_h2s:
            for th2 in tpl_h2s:
                result.append(mk_heading(th2['heading'], 2))
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
            for mi in my_md_h2s:
                if mi not in used_md_h2:
                    used_md_h2.add(mi)
                    result.append(mk_heading(all_md_h2[mi]['heading'], 2))
                    result.extend(all_md_h2[mi]['blocks'])
        else:
            for mi in my_md_h2s:
                if mi not in used_md_h2:
                    used_md_h2.add(mi)
                    result.extend(all_md_h2[mi]['blocks'])
    for mi, mh2 in enumerate(all_md_h2):
        if mi not in used_md_h2:
            result.append(mk_heading(mh2['heading'], 2))
            result.extend(mh2['blocks'])
    return result

md = open("/tmp/_feishu_merge_md", "r", encoding="utf-8").read()
tpl_blocks = json.loads(open("/tmp/_feishu_merge_tpl", "r", encoding="utf-8").read())
tpl_sections = parse_template_from_blocks(tpl_blocks)
if tpl_sections:
    blocks = merge_with_template_inner(tpl_sections, md)
else:
    blocks = parse_md_inner(md)
print(json.dumps(blocks, ensure_ascii=False))
MERGEEOF
}

extract_doc_id() {
    local template_ref="$1"
    if [[ "$template_ref" =~ /docx/([a-zA-Z0-9]+) ]]; then
        echo "docx:${BASH_REMATCH[1]}"
    elif [[ "$template_ref" =~ /wiki/([a-zA-Z0-9]+) ]]; then
        echo "wiki:${BASH_REMATCH[1]}"
    else
        echo ""
    fi
}

parse_owner() {
    local owner_str="$1"
    if [[ -n "$owner_str" && "$owner_str" == *":"* ]]; then
        echo "$owner_str"
    else
        echo ""
    fi
}

publish() {
    local title="$1"
    local md="$2"
    local template_ref="${3:-}"
    local owner_str="${4:-}"
    local folder_token="${5:-}"

    if [[ -n "$folder_token" && "$folder_token" != "None" ]]; then
        FOLDER="$folder_token"
    fi

    # Save credentials for python heredoc access
    echo -n "$APP_ID" > /tmp/_feishu_app_id
    echo -n "$APP_SECRET" > /tmp/_feishu_app_secret

    feishu_auth
    feishu_create_doc "$title"

    local blocks=""
    if [[ -n "$template_ref" ]]; then
        local doc_info
        doc_info=$(extract_doc_id "$template_ref")
        if [[ -n "$doc_info" ]]; then
            local kind="${doc_info%%:*}"
            local ref_id="${doc_info##*:}"
            local actual_id="$ref_id"
            if [[ "$kind" == "wiki" ]]; then
                actual_id=$(feishu_resolve_wiki "$ref_id")
            fi
            local template_blocks
            template_blocks=$(feishu_read_blocks "$actual_id")
            blocks=$(merge_with_template "$md" "$template_blocks")
        elif [[ -f "$template_ref" ]]; then
            local tpl_md
            tpl_md=$(cat "$template_ref")
            blocks=$(merge_with_template "$md" "$tpl_md")
        else
            blocks=$(parse_md_to_blocks "$md")
        fi
    else
        blocks=$(parse_md_to_blocks "$md")
    fi

    # Write blocks to temp file for batch processing
    echo -n "$blocks" > /tmp/_feishu_all_blocks
    local total
    total=$(python3 << 'TOTEOF'
import json
blocks = json.loads(open("/tmp/_feishu_all_blocks", "r").read())
print(len(blocks))
TOTEOF
)
    local off=0
    while ((off < total)); do
        echo -n "$off" > /tmp/_feishu_batch_off
        local batch
        batch=$(python3 << 'BATEOF'
import json
blocks = json.loads(open("/tmp/_feishu_all_blocks", "r").read())
off = int(open("/tmp/_feishu_batch_off", "r").read().strip())
print(json.dumps(blocks[off:off+50]))
BATEOF
)
        feishu_add_blocks "$DOC_ID" "$batch"
        ((off += 50))
    done

    if [[ -n "$owner_str" ]]; then
        local owner_parsed
        owner_parsed=$(parse_owner "$owner_str")
        if [[ -n "$owner_parsed" ]]; then
            local otype="${owner_parsed%%:*}"
            local oid="${owner_parsed##*:}"
            feishu_transfer_owner "$DOC_ID" "$otype" "$oid"
        fi
    fi

    feishu_set_internal_only "$DOC_ID"

    echo "https://bytedance.larkoffice.com/docx/${DOC_ID}"
}

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --title) DOC_TITLE="$2"; shift 2 ;;
            --file) MD_FILE="$2"; shift 2 ;;
            --content) MD_CONTENT="$2"; shift 2 ;;
            --config) CONFIG_PATH="$2"; shift 2 ;;
            --app-id) APP_ID="$2"; shift 2 ;;
            --app-secret) APP_SECRET="$2"; shift 2 ;;
            --template) TEMPLATE="$2"; shift 2 ;;
            --owner) OWNER="$2"; shift 2 ;;
            --folder) FOLDER="$2"; shift 2 ;;
            -h|--help) usage ;;
            *) die "Unknown option: $1" ;;
        esac
    done

    if [[ -z "$DOC_TITLE" ]]; then
        die "--title is required"
    fi

    if [[ -z "$MD_FILE" && -z "$MD_CONTENT" ]]; then
        die "Either --file or --content is required"
    fi

    local md
    if [[ -n "$MD_FILE" ]]; then
        md=$(cat "$MD_FILE")
    else
        md="$MD_CONTENT"
    fi

    load_config

    if [[ -z "$APP_ID" || -z "$APP_SECRET" ]]; then
        die "Missing app_id/app_secret. Set via --app-id/--app-secret, config file, or FEISHU_APP_ID/FEISHU_APP_SECRET env vars"
    fi

    # Save credentials for python heredoc access
    echo -n "$APP_ID" > /tmp/_feishu_app_id
    echo -n "$APP_SECRET" > /tmp/_feishu_app_secret

    local url
    url=$(publish "$DOC_TITLE" "$md" "$TEMPLATE" "$OWNER" "$FOLDER")

    # Build result JSON
    echo -n "$url" > /tmp/_feishu_result_url
    echo -n "$DOC_ID" > /tmp/_feishu_result_did
    echo -n "${TEMPLATE:-}" > /tmp/_feishu_result_tpl
    echo -n "${OWNER:-}" > /tmp/_feishu_result_owner
    python3 << 'RESULTEOF'
import json
url = open("/tmp/_feishu_result_url", "r").read().strip()
doc_id = open("/tmp/_feishu_result_did", "r").read().strip()
tpl = open("/tmp/_feishu_result_tpl", "r").read().strip()
owner = open("/tmp/_feishu_result_owner", "r").read().strip()
r = {'success': True, 'url': url, 'doc_id': doc_id, 'template_used': bool(tpl)}
if owner:
    r['owner'] = owner.split(':', 1)[-1] if ':' in owner else owner
print(json.dumps(r, ensure_ascii=False))
RESULTEOF

    # Cleanup temp files
    rm -f /tmp/_feishu_*
}

main "$@"


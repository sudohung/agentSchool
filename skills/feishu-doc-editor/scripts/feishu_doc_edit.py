#!/usr/bin/env python3
"""Incremental editor for existing Feishu docx documents.

Subcommands:
  info        <doc_id>
  find        <doc_id> <regex>
  dump        <doc_id> [out.json]
  patch       <doc_id> <block_id> <text>       # supports **bold** and `inline code`
  patch-batch <doc_id> <spec.json>             # [[block_id, text], ...]
  delete      <doc_id> <parent_block_id> <start_index> <end_index>
  add-row     <doc_id> <table_block_id>
  cells       <doc_id> <table_block_id>

Wiki URLs: resolve doc_id first (feishu_doc_reader prints it in meta), or pass ?wiki_token=.
"""
import json
import os
import re
import sys

import requests

BASE = 'https://open.feishu.cn/open-apis'
CFG_PATH = os.path.expanduser('~/.claude/feishu_config.json')
TYPE_KEY = {2: 'text', 3: 'heading1', 4: 'heading2', 5: 'heading3', 6: 'heading4',
            7: 'heading5', 8: 'heading6', 9: 'heading7', 10: 'heading8', 11: 'heading9',
            12: 'bullet', 13: 'ordered', 14: 'code', 15: 'quote', 17: 'todo',
            19: 'callout', 27: 'image', 31: 'table', 32: 'table_cell', 34: 'quote_container'}
MARKUP = re.compile(r'\*\*(.+?)\*\*|`([^`]+)`')


def config():
    if os.path.exists(CFG_PATH):
        cfg = json.load(open(CFG_PATH))
        return cfg['app_id'], cfg['app_secret']
    return os.environ['FEISHU_APP_ID'], os.environ['FEISHU_APP_SECRET']


class Client:
    def __init__(self):
        self.token = None

    def auth(self):
        app_id, secret = config()
        d = requests.post(f'{BASE}/auth/v3/tenant_access_token/internal',
                          json={'app_id': app_id, 'app_secret': secret}).json()
        if d.get('code') != 0:
            raise SystemExit(f'auth failed: {d}')
        self.token = d['tenant_access_token']

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json; charset=utf-8'}

    def get(self, path, **params):
        d = requests.get(BASE + path, headers=self.headers, params=params).json()
        if d.get('code') != 0:
            raise SystemExit(f'GET {path} failed: {d}')
        return d['data']

    def send(self, method, path, body):
        d = requests.request(method, BASE + path, headers=self.headers,
                             data=json.dumps(body, ensure_ascii=False).encode('utf-8')).json()
        return d

    def all_blocks(self, doc):
        items, token = [], None
        while True:
            params = {'page_size': 500, 'document_revision_id': -1}
            if token:
                params['page_token'] = token
            data = self.get(f'/docx/v1/documents/{doc}/blocks', **params)
            items.extend(data.get('items', []))
            if not data.get('has_more'):
                break
            token = data.get('page_token')
        return items


def block_text(b):
    obj = b.get(TYPE_KEY.get(b.get('block_type'), ''), {}) or {}
    return ''.join(e.get('text_run', {}).get('content', '')
                   for e in (obj.get('elements') or []))


def depth(b, by_id, root):
    d, p = 0, b.get('parent_id')
    while p and p in by_id and p != root:
        d += 1
        p = by_id[p].get('parent_id')
    return d


def style_run(text, bold=False, code=False):
    style = {}
    if bold:
        style['bold'] = True
    if code:
        style['inline_code'] = True
    return {'text_run': {'content': text, 'text_element_style': style}}


def elements(markup):
    els, pos = [], 0
    for m in MARKUP.finditer(markup):
        if m.start() > pos:
            els.append(style_run(markup[pos:m.start()]))
        if m.group(1) is not None:
            els.append(style_run(m.group(1), bold=True))
        else:
            els.append(style_run(m.group(2), code=True))
        pos = m.end()
    if pos < len(markup):
        els.append(style_run(markup[pos:]))
    return els


def patch(c, doc, block_id, text):
    d = c.send('PATCH', f'/docx/v1/documents/{doc}/blocks/{block_id}?document_revision_id=-1',
               {'update_text_elements': {'elements': elements(text)}})
    print(('OK   ' if d.get('code') == 0 else 'FAIL '), block_id, d.get('code'), d.get('msg'), text[:40])


def main():
    args = sys.argv[1:]
    cmd, doc = args[0], args[1]
    c = Client()
    c.auth()

    if cmd == 'info':
        blocks = c.all_blocks(doc)
        print(f'blocks={len(blocks)}')
    elif cmd == 'dump':
        blocks = c.all_blocks(doc)
        out = args[2] if len(args) > 2 else '/tmp/feishu_blocks.json'
        json.dump(blocks, open(out, 'w'), ensure_ascii=False, indent=1)
        print(f'blocks={len(blocks)} -> {out}')
    elif cmd == 'find':
        pat = re.compile(args[2])
        blocks = c.all_blocks(doc)
        by_id = {b['block_id']: b for b in blocks}
        for i, b in enumerate(blocks):
            t = block_text(b)
            if pat.search(t):
                parent = by_id.get(b.get('parent_id')) or {}
                children = parent.get('children') or []
                idx = children.index(b['block_id']) if b['block_id'] in children else None
                print(f'[{i}] type={b.get("block_type")} id={b["block_id"]} '
                      f'parent={b.get("parent_id")} idx={idx} d={depth(b, by_id, doc)} text={t!r}')
    elif cmd == 'patch':
        patch(c, doc, args[2], args[3])
    elif cmd == 'patch-batch':
        spec = json.load(open(args[2]))
        for block_id, text in spec:
            patch(c, doc, block_id, text)
    elif cmd == 'delete':
        parent, start, end = args[2], int(args[3]), int(args[4])
        d = c.send('DELETE',
                   f'/docx/v1/documents/{doc}/blocks/{parent}/children/batch_delete'
                   '?document_revision_id=-1',
                   {'start_index': start, 'end_index': end})
        print(d.get('code'), d.get('msg'))
    elif cmd == 'add-row':
        table = args[2]
        d = c.send('PATCH', f'/docx/v1/documents/{doc}/blocks/{table}?document_revision_id=-1',
                   {'insert_table_row': {'row_index': -1}})
        print(d.get('code'), d.get('msg'))
        if d.get('code') == 0:
            blocks = {b['block_id']: b for b in c.all_blocks(doc)}
            table_block = blocks.get(table) or c.get(f'/docx/v1/documents/{doc}/blocks/{table}')
            table_block = table_block.get('block', table_block)
            cells = (table_block.get('table') or {}).get('cells') or []
            for cell_id in cells[-5:]:
                cell = blocks.get(cell_id, {})
                print('cell', cell_id, cell.get('children'))
    elif cmd == 'cells':
        table = args[2]
        blocks = {b['block_id']: b for b in c.all_blocks(doc)}
        cells = (blocks[table].get('table') or {}).get('cells') or []
        print(f'cells={len(cells)}')
        for i, cell_id in enumerate(cells):
            cell = blocks.get(cell_id, {})
            texts = [block_text(blocks[cid]) for cid in (cell.get('children') or []) if cid in blocks]
            print(i, cell_id, texts)
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()

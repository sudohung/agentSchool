---
name: feishu-doc-editor
description: 增量编辑已存在的飞书文档（docx/wiki）——按块定位并改写文本（保留行内代码/加粗样式）、删除整段、给表格插入行并填值。当用户要求“订正/修改/更新某个飞书文档的某段描述”“删掉飞书文档里的某个接口章节”“给飞书表格新增一行”时使用。只读转换请用 feishu-doc-reader，整篇发布请用 feishu-doc-publisher。
---

# Skill: feishu-doc-editor

对**已存在**的飞书 docx/wiki 文档做外科式增量修改，避免整篇重发导致评论/图片/历史丢失。

凭证与 `feishu-doc-publisher` 共用 `~/.claude/feishu_config.json`（或 `FEISHU_APP_ID`/`FEISHU_APP_SECRET`）。应用需要 `docx:document` 写权限。

## 工作流

1. **先读再改**：用 feishu-doc-reader 转 Markdown，确认要改的段落、以及改动后整篇是否自洽（同一口径常常散落在状态机、流程步骤、接口段落、风险评估、工作量表等多处）。
2. **定位块**：`python3 feishu_doc_edit.py find <doc_id> "<正则>"` 输出 `[序号] type id parent idx 文本`。
3. **改文本**：`patch` 支持 `**加粗**` 与 `` `行内代码` `` 标记，自动转成飞书样式（直接写反引号会变成字面字符）。
4. **删整段**：`delete <parent_id> <start_index> <end_index>`（end 不含）；顺序按父块 `children` 下标，删除后下标会变化，一次删一段、删完重新 `find`。
5. **表格加行**：`add-row <table_block_id>` 会追加一行并打印新单元格内文本块 id，再用 `patch` 填值（表格 block 的 children 就是单元格，`table.cells` 是 row-major 展开）。
6. **回读校验**：用 feishu-doc-reader 重新导出 Markdown，与原稿 diff，确认没有漏改/错位/编号重复。

## 命令

```bash
# doc_id：wiki 链接先解析（reader 的 meta 里带 doc_id）
python3 feishu_doc_edit.py info  <doc_id>                 # 块总数/标题
python3 feishu_doc_edit.py find  <doc_id> "provider-retry"
python3 feishu_doc_edit.py dump  <doc_id> /tmp/blocks.json # 全量块 JSON，供脚本分析
python3 feishu_doc_edit.py patch <doc_id> <block_id> "文本，含 `code` 与 **加粗**"
python3 feishu_doc_edit.py delete <doc_id> <parent_block_id> 364 373
python3 feishu_doc_edit.py add-row <doc_id> <table_block_id>
python3 feishu_doc_edit.py cells <doc_id> <table_block_id>
```

批量改多处时，把 `[block_id, 文本]` 列表写成 JSON 文件，`patch-batch <doc_id> spec.json`，逐条打印 OK/FAIL，失败不影响其它条目。

## 坑位

- **行内代码是样式不是反引号**：`update_text_elements` 直接传反引号会渲染成字面 `` ` ``。用 `**`/`` ` `` 标记让脚本拆成多个 text_run。
- **改写整段会丢原样式**：原有加粗/代码样式需在标记里显式写回；纯文本段落无影响。
- **步骤列表按块计数**：有序列表每项是独立块，改写前先核对“原第 7 步=哪个 block_id”，差一格就会出现重复步骤或把“关键规则：”这类小标题覆盖掉。改完必须回读 diff。
- **删块用父块下标**：`children` 是扁平列表，`end_index` 不含；表格的 `children` 是单元格而非行。
- **表格插入行**：`PATCH /blocks/{table}` body `{"insert_table_row":{"row_index":-1}}`，新单元格默认为空文本块。
- **修订记录**：文档改动要补一行「日期/版本号/类别/描述/作者」，与既有表格风格一致。
- 写入成功返回 `code=0`；权限不足/只读会返回非 0，先确认应用是文档协作者。

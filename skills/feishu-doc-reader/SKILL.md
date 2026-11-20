---
name: feishu-doc-reader
description: 读取并解析飞书在线文档（docx / wiki 知识库文档），转换为 Markdown 或原始 blocks JSON。当用户提供飞书文档/wiki 链接并要求"看看这个文档"、"读取飞书文档"、"把飞书文档转成 Markdown"、"分析飞书文档内容"、"下载飞书文档图片"时使用。复用 feishu-doc-publisher 的应用凭证（~/.claude/feishu_config.json）。
---

# Feishu Doc Reader

读取飞书文档并转换为 Markdown。与 feishu-doc-publisher 共用同一套应用凭证和权限。

## 凭证

自动读取 `~/.claude/feishu_config.json`（或环境变量 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`），与 feishu-doc-publisher 相同，无需额外配置。

## 使用方式

```bash
# 读文档转 Markdown，markdown 直接输出到 stdout
python <skill_dir>/scripts/feishu_read.py --url "https://xxx.feishu.cn/docx/xxxx"

# 落盘 + 下载图片到相对目录（markdown 同样会输出到 stdout）
python <skill_dir>/scripts/feishu_read.py --url "https://xxx.feishu.cn/wiki/xxxx" \
    --out doc.md --download-images imgs

# 原始 blocks JSON（调试未知块类型时用）
python <skill_dir>/scripts/feishu_read.py --url xxx --format json --out blocks.json

# 块类型统计（排查内容缺失时用）
python <skill_dir>/scripts/feishu_read.py --url xxx --stats
```

参数说明：
- `--url`：docx/wiki 链接或裸 token；`--doc-id`：直接给 docx id
- `--out`：额外把 markdown 落盘到指定文件（stdout 仍会输出完整内容）
- `--download-images DIR`：下载文档内图片，markdown 引用相对路径；不指定则输出 `feishu-image://token` 占位
- `--format json`：输出飞书原始 blocks（含嵌套结构、merge_info 等）
- `--stats`：块类型分布统计

## 支持的块类型

标题(h1-h9→#~######，含标题下折叠/缩进的子内容)、正文、粗体/斜体/删除线/行内代码/链接、代码块(语言数字枚举/字符串名双向映射)、无序/有序列表(嵌套缩进)、待办(勾选状态)、引用(含子内容)、引用容器/高亮块(→ `>` 前缀)、分割线、表格(含合并单元格展开为 row-major 网格，多段落用 `<br>`)、图片(可下载)、附件/iframe(占位链接)、栅格布局(透传子块)。多维表格/画板/思维笔记/UML 等嵌入块输出 `[嵌入块:类型]` 占位。

## 权限与报错处理

应用必须有文档读取权限，否则报 `permission denied`。给用户的引导话术：

- **docx 文档**：文档右上角「···」→「更多」→「添加文档应用」为协作者；或文档安全设置中允许应用访问
- **wiki 知识库**：知识库「设置」→「成员管理」→ 添加文档应用并授予可阅读权限
- **老版 doc（obj_type=doc）**：仅能提取纯文本（API 限制），会返回 JSON 带 `note` 说明
- 由 feishu-doc-publisher 发布的文档：应用是 owner，可直接读取
- 文档被删除时报 `resource deleted (code=1770003)`，向用户确认文档是否还在

## 输出约定

- **markdown 内容始终写到 stdout**，执行完即可直接消费，无需再 Read 文件
- **元信息 JSON**（success/out/blocks/title/doc_id）写到 stderr，不污染 markdown；合并查看时会出现在末尾
- 指定 `--out` 时 markdown 同时落盘；`--format json` 时 stdout 为原始 blocks JSON
- 老版 doc：stdout 为纯文本，stderr 带 `note` 说明
- markdown 为 UTF-8；脚本已 `reconfigure` stdout 编码，Windows 下一般不再乱码

## 典型工作流

1. 用户提供飞书链接 → 直接运行 `feishu_read.py --url ...`，stdout 即完整 markdown
2. 若 permission denied → 引导用户授权（见上），授权后重试
3. 内容缺失/格式异常 → `--stats` 看块分布，`--format json` 查原始块定位问题
4. 需要归档或大文档 → 加 `--out <路径>` 落盘，markdown 仍会输出到 stdout

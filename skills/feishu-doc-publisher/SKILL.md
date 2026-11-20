---
name: feishu-doc-publisher
description: 将用户明确指定的 Markdown 设计文档一键发布为飞书在线文档，并设置私有权限、转移给配置的 owner。
capabilities:
  - network
  - api
  - credential
data_scopes:
  - credential
  - user_selected_file_content
allowed_domains:
  - open.feishu.cn
  - bytedance.larkoffice.com
  - my.feishu.cn
identity_scope: any_user
---

# Feishu Doc Publisher - 使用说明

## 概述

本技能用于将 Markdown 设计文档一键发布为飞书在线文档。支持标题、正文、代码块、列表、表格等内容格式，支持通过模板转换。
2026-05-08 更新，直接将文档所有者转移给配置的owner（公司飞书账号）

## 文件结构

```
~/.claude/skills/feishu-doc-publisher/
├── SKILL.md                # 技能定义（自动加载）
├── scripts/
│   └── feishu_publish.py   # 发布脚本
└── README.md               # 本文件
```

## 首次配置

### 1. 获取飞书应用凭证

1. 打开 [飞书开放平台](https://open.feishu.cn/app)
2. 点击「创建应用」→「企业自建应用」
3. 记录 **App ID** 和 **App Secret**

### 2. 开通应用权限

在应用管理页面 →「权限管理」，搜索并开通以下权限：

| 权限 | Scope | 用途 |
|------|-------|------|
| 创建/管理文档 | `docx:document` | 创建文档和写入内容块 |
| 读取知识库节点 | `wiki:wiki:readonly` | 从知识库 URL 读取模板 |
| 设置文档权限 | `docs:permission.setting:write_only` | 设置文档分享和权限 |
| 云空间访问 | `drive:drive` | 权限相关操作的备用 scope |
| 添加协作者 | `drive:permission:write` | 将 owner_email 添加为文档协作者 |
| 转移所有权 | `docs:permission.member:transfer` | 将文档所有权转移给 owner_email |

### 3. 发布应用

在「版本管理与发布」→ 创建版本并提交审核（测试阶段可使用测试企业）。

### 4. 保存凭证

凭证保存到 `~/.claude/feishu_config.json`，格式：

```json
{
    "app_id": "cli_xxx",
    "app_secret": "xxx",
    "owner_email": "user@xiaopeng.com",
    "folder_token": "xxxxxxxxxxxxxxxxxx"
}
```

## 使用方式

### 方式一：直接对话（推荐）

跟我说以下任何一种：

- "把这个文件发布到飞书" + 文件路径
- "发布到飞书" （我会找当前工作目录的 .md 文件）
- "创建飞书文档，标题xxx，内容是..."

### 方式二：带模板发布

- "用模板 https://my.feishu.cn/wiki/xxx 发布这个设计文档到飞书"
- "用本地 template.md 作为模板发布"

### 方式三：脚本直调

```bash
# 无模板 - 完整转换
python ~/.claude/skills/feishu-doc-publisher/scripts/feishu_publish.py \
--title "文档标题" --file design.md --folder "目录tokenxxxx"

# 带飞书模板
python ~/.claude/skills/feishu-doc-publisher/scripts/feishu_publish.py \
--title "文档标题" --file design.md --template "https://my.feishu.cn/wiki/xxx"

# 带本地模板
python ~/.claude/skills/feishu-doc-publisher/scripts/feishu_publish.py \
--title "文档标题" --file design.md --template template.md
```

## 支持的内容格式

| Markdown 元素 | 飞书渲染效果 |
|---------------|-------------|
| `# 一级标题` | 大标题 |
| `## 二级标题` | 中标题 |
| `### 三级标题` | 小标题 |
| `#### 四级标题` | 小小标题 |
| 普通段落 | 正文文本 |
| `` ```代码块``` `` | 代码块（自动识别语言） |
| `- 无序列表` | 无序列表 |
| `1. 有序列表` | 有序列表 |
| `- [ ] 待办` | 无序列表 |
| `> 引用` | 引用块 |
| `\| 表格 \|` | 原生表格（飞书 Table Block） |

## 支持的代码语言

Java, SQL, Python, JSON, JavaScript, YAML, Bash, XML, HTML, CSS, TypeScript, Go, Rust, C, C++, C#

## 脚本直接使用

```bash
# 从文件发布
python ~/.claude/skills/feishu-doc-publisher/scripts/feishu_publish.py \
    --title "文档标题" \
    --file path/to/design.md

# 从内容字符串发布
python ~/.claude/skills/feishu-doc-publisher/scripts/feishu_publish.py \
    --title "文档标题" \
    --content "# 标题\n正文内容"

# 指定凭证文件
python ~/.claude/skills/feishu-doc-publisher/scripts/feishu_publish.py \
    --title "文档标题" \
    --file design.md \
    --config /path/to/config.json

# 通过环境变量
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
python ~/.claude/skills/feishu-doc-publisher/scripts/feishu_publish.py \
    --title "文档标题" \
    --file design.md
```

## 输出

成功：`{"success": true, "url": "https://bytedance.larkoffice.com/docx/xxx", "doc_id": "xxx", "template_used": false}`

失败：`{"error": "错误信息"}`

文档默认创建为**私有**，自动应用以下安全设置：
- **外部访问**：关闭（不允许外部用户访问）
- **链接分享**：关闭（不允许通过链接访问）
- **所有权**：转移给配置的 `owner_email`
- **应用权限**：保留"full_access"（可管理）

仅 `owner_email` 用户和飞书应用（创建者）可以读写文档。

## 注意事项

1. **表格渲染**：Markdown 表格通过飞书「创建嵌套块」API 转为原生 Table Block，支持标题行和列宽设置。单次创建最多 9 行，超出部分以代码块形式追加显示
2. **代码块长度**：超过 3000 字符的代码块会自动拆分为多个代码块
3. **批量写入**：文档内容按每 50 个块分批写入，避免 API 限制
4. **凭证安全**：`feishu_config.json` 包含敏感信息，不要提交到版本控制
5. **应用权限**：确保应用已发布且权限已生效，否则文档会创建但可能无法访问
6. 文档密级（如 L2-内部公开）暂无公开 API，发布后需在飞书界面手动设置。脚本发布完成时会在 stderr 输出提醒信息。

## 更新凭证

如需更换 App ID / App Secret，直接编辑 `~/.claude/feishu_config.json`，或告诉 Claude：

"更新飞书凭证，新的 App ID 是 xxx，Secret 是 xxx"

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `Auth failed` | 凭证无效或过期 | 检查 App ID / Secret 是否正确 |
| `Create failed: no permission` | 应用未开通文档权限 | 在飞书开放平台添加 `docx:document` 权限 |
| `Add blocks failed` | 内容格式不支持 | 检查 Markdown 是否有异常格式 |
| 文档创建了但打不开 | 应用未发布或无查看权限 | 发布应用并确保文档协作者包含应用 |

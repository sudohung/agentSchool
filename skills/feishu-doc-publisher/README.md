# Feishu Doc Publisher

将 Markdown 文档一键发布为飞书在线文档的技能。

## 快速开始

1. 配置飞书应用凭证（见 SKILL.md）
2. 保存凭证到 `~/.claude/feishu_config.json`
3. 使用方式：
   - 直接对话："把这个文件发布到飞书"
   - 脚本调用：`python ~/.claude/skills/feishu-doc-publisher/scripts/feishu_publish.py --title "标题" --file document.md`

## 文件结构

```
feishu-doc-publisher/
├── SKILL.md                # 技能定义
├── scripts/
│   └── feishu_publish.py   # 发布脚本
└── README.md               # 本文件
```

详细使用说明请查看 [SKILL.md](SKILL.md)。

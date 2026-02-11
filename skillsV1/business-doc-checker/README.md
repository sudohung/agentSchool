# business-doc-checker 技能

业务文档完整性检查工具 - 检查业务文档是否覆盖了Java项目中的核心模块、业务流程、API接口和数据表等业务内容。

## 📋 概述

这个技能用于检查业务文档的完整性，确保文档覆盖了Java项目中的核心业务模块和流程。检查是**广度优先**的，不会深入检查模块的详细实现逻辑。

## 🎯 使用场景

当您需要：
- ✅ 检查业务文档是否覆盖了系统的核心模块
- ✅ 确认文档是否描述了所有关键业务流程
- ✅ 验证文档是否包含所有重要的API接口
- ✅ 确认数据表设计是否在文档中有所体现
- ✅ 生成文档完整性检查报告

## 🔍 检查维度

### 1. 模块划分
- 识别项目中的核心模块/包结构
- 检查文档是否提到了这些模块
- 标记未在文档中出现的模块

### 2. 业务流程
- 结合git提交记录识别关键的业务流程和处理链路
- 检查文档是否覆盖了这些流程
- 标记文档中缺失的流程

### 3. API接口
- 扫描Controller层的API接口
- 检查文档是否描述了这些接口
- 标记未在文档中记录的接口

### 4. 数据表
- 识别项目中的数据表/实体
- 检查文档是否提到了这些数据表
- 标记文档中缺失的数据表

## 🚀 快速开始

### 方式1：完整检查流程（推荐）

```bash
# 1. 扫描Java项目
cd your-project
python /path/to/scripts/java_scanner.py .

# 2. 手动检查文档覆盖情况
# 根据扫描结果，对照文档检查每个模块、API、数据表

# 3. 生成报告
python /path/to/scripts/example_usage.py
```

### 方式2：快速检查（自动化）

```bash
# 一键检查并生成报告
python /path/to/scripts/quick_check.py docs/业务文档.md .
```

报告将生成在: `docs/文档完整性检查报告.md`

## 📁 目录结构

```
business-doc-checker/
├── SKILL.md                    # 技能说明文档
├── README.md                   # 本文件
├── scripts/                    # 辅助脚本
│   ├── java_scanner.py        # Java项目扫描器
│   ├── report_generator.py    # 报告生成器
│   ├── quick_check.py         # 快速检查脚本
│   ├── example_usage.py       # 使用示例
│   └── check_helper.sh        # 辅助工具
└── references/                 # 参考文档
    ├── check-process.md       # 检查流程详细指南
    ├── report-template.md     # 报告模板
    ├── usage-examples.md      # 使用示例
    ├── QUICKSTART.md          # 快速开始指南
    └── CHECKLIST.md           # 检查清单和匹配规则
```

## 📊 输出示例

检查完成后会生成 `文档完整性检查报告.md`，包含：

```
# 业务文档完整性检查报告

## 检查概述
- 检查时间: 2026-02-07
- 文档路径: docs/README.md
- 项目路径: ./

## 统计概览
| 检查维度 | 总数 | 已覆盖 | 覆盖率 | 缺失数 |
|---------|------|--------|--------|--------|
| 模块划分 | 8 | 6 | 75% | 2 |
| 业务流程 | 5 | 3 | 60% | 2 |
| API接口 | 10 | 8 | 80% | 2 |
| 数据表 | 6 | 4 | 67% | 2 |
| **总计** | 29 | 21 | 72% | 8 |

## 详细检查结果

### 1. 模块划分 ✅覆盖率: 75%

#### 已覆盖的模块 (6/8)
- ✅ 用户管理模块 (UserService) - 文档第3章有详细的功能说明
- ✅ 订单管理模块 (OrderService) - 文档第4章有模块职责描述
- ...

#### 缺失的模块 (2/8)
- ❌ 库存管理模块 (InventoryService) - 文档未提及
- ❌ 物流模块 (LogisticsService) - 文档未提及

...

## 建议补充内容

1. **模块说明**
   - 库存管理模块的功能和职责说明
   - 物流模块的处理流程和接口说明

2. **业务流程**
   - 库存扣减流程的详细步骤和业务规则
   - 订单取消流程的状态流转和处理逻辑

...
```

## 📖 详细文档

- [检查流程详细指南](references/check-process.md) - 详细的检查步骤和方法
- [报告模板](references/report-template.md) - 报告格式和模板
- [使用示例](references/usage-examples.md) - 具体的使用示例
- [快速开始](references/QUICKSTART.md) - 快速入门指南
- [检查清单](references/CHECKLIST.md) - 详细的检查清单和匹配规则

## 🛠️ 辅助工具

### java_scanner.py
扫描Java项目并提取核心业务信息
```bash
python scripts/java_scanner.py <项目路径>
```

### report_generator.py
生成标准化的检查报告
```bash
python scripts/report_generator.py --help
```

### quick_check.py
一键检查并生成报告
```bash
python scripts/quick_check.py <文档路径> <项目路径>
```

## 💡 注意事项

1. **广度优先**：检查关注业务范围的覆盖度，不深入模块的实现细节
2. **关键元素**：优先检查核心模块、主流流程和主要接口，忽略辅助类
3. **命名识别**：通过类名、包名和注释来识别业务含义
4. **报告清晰**：输出应简洁明了，便于后续补充文档

## 🤝 示例使用

用户请求：
> 请检查我的业务文档是否覆盖了所有核心模块

技能执行：
1. 读取用户提供的文档
2. 扫描项目代码，提取核心模块列表
3. 对比文档与代码，找出缺失的模块
4. 生成完整性检查报告

## 📝 检查说明

- **检查范围**: 广度优先检查，关注业务范围覆盖度
- **检查方法**: 代码扫描 + 文档关键词匹配
- **匹配规则**: 使用精确匹配和语义匹配相结合的方式
- **覆盖标准**: 文档中有实质性描述即视为已覆盖

## 📄 输出文件

- `文档完整性检查报告.md` - 完整的检查报告（Markdown格式）

## 🔗 相关技能

结合使用以下技能可以更好地完成工作：
- [java-system-analysis](skill:java-system-analysis) - Java系统分析专家
- [git-log-and-hotspot-code-analysis](skill:git-log-and-hotspot-code-analysis) - Git日志和热点代码分析

---

**技能名称**: business-doc-checker
**版本**: 1.0
**创建日期**: 2026-02-07

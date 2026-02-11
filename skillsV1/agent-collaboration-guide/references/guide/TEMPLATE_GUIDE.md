# 项目优化模板使用指南

> **文档版本**：v1.0  
> **创建日期**：2025-01  
> **适用范围**：所有需要系统性分析和优化的大型软件项目

---

## 📁 目录结构

```
references/
├── 01-project-overview-template.md                # 项目概览报告模板
├── 02-architecture-analysis-template.md           # 技术架构分析报告模板
├── guide/                                           # 分析阶段模板
│   ├── TEMPLATE_GUIDE.md                       # 本模板使用指南
│   ├── LARGE_PROJECT_ANALYSIS_AND_OPTIMIZATION_PLAYBOOK.md  # 主战术指导手册
│   ├── AGENT_COLLABORATION_FRAMEWORK.md        # 项目分析与优化 Agent 协作框架
│   ├── 
│   ├── 
│   └── 
├── 03-business-logic-analysis-template.md         # 业务逻辑分析报告模板
├── 04-issue-list-template.md                      # 问题清单与优先级报告模板
├── execution-report-template.md                    # 优化执行报告模板
├── optimization-plan-template.md                   # 系统优化方案模板

```

## 🎯 使用流程

### 1. 阶段一：项目全貌扫描
- **使用模板**：`references/01-project-overview-template.md`
- **输出文件**：`references/01-project-overview.md`
- **关键动作**：收集项目基本信息、分析 Git 历史、识别代码热点

### 2. 阶段二：技术架构解析
- **使用模板**：`references/02-architecture-analysis-template.md`
- **输出文件**：`references/02-architecture-analysis.md`
- **关键动作**：分析依赖关系、绘制架构图、识别技术债务

### 3. 阶段三：业务逻辑梳理
- **使用模板**：`references/03-business-logic-analysis-template.md`
- **输出文件**：`references/03-business-logic-analysis.md`
- **关键动作**：追踪核心流程、分析数据模型、绘制状态机

### 4. 阶段四：问题识别与分类
- **使用模板**：`references/04-issue-list-template.md`
- **输出文件**：`references/04-issue-list.md`
- **关键动作**：识别代码异味、分类问题优先级、量化技术债务

### 5. 阶段五：优化方案设计
- **使用模板**：`plans/optimization-plan-template.md`
- **输出文件**：`plans/optimization-plan.md`
- **关键动作**：制定优化目标、设计执行步骤、评估风险影响

### 6. 阶段六：执行与验证
- **使用模板**：`reports/execution-report-template.md`
- **输出文件**：`reports/execution-report-[date].md`
- **关键动作**：执行优化任务、验证效果、总结经验

## 📝 模板使用说明

### 1. 复制模板
```bash
# 复制模板到实际文件
cp references/01-project-overview-template.md references/01-project-overview.md
cp references/02-architecture-analysis-template.md references/02-architecture-analysis.md
cp references/03-business-logic-analysis-template.md references/03-business-logic-analysis.md
cp references/04-issue-list-template.md references/04-issue-list.md
cp plans/optimization-plan-template.md plans/optimization-plan.md
cp reports/execution-report-template.md reports/execution-report-$(date +%Y-%m-%d).md
```

### 2. 填写内容
- 替换所有 `[占位符]` 为实际内容
- 删除模板中的备注说明
- 根据实际情况调整表格行数
- 补充具体的分析数据和命令结果

### 3. 版本控制
- 每个阶段完成后提交到 Git
- 使用有意义的提交信息
- 保持文档与代码同步更新

### 4. 团队协作
- 指定每个文档的负责人
- 定期进行文档评审
- 及时更新文档状态

## ⚡ 快速开始

### 创建新项目优化工作区
```bash
# 1. 复制所有模板
mkdir -p docs/references docs/plans docs/reports
cp docs/references/*-template.md docs/references/
cp docs/plans/*-template.md docs/plans/
cp docs/reports/*-template.md docs/reports/

# 2. 重命名模板文件（移除 -template 后缀）
cd docs/references
for file in *-template.md; do mv "$file" "${file%-template.md}.md"; done
cd ../plans
for file in *-template.md; do mv "$file" "${file%-template.md}.md"; done
cd ../reports
cp execution-report-template.md execution-report-$(date +%Y-%m-%d).md
```

### 填写顺序建议
1. 先完成 `01-project-overview.md`
2. 基于概览报告完成 `02-architecture-analysis.md`
3. 基于架构分析完成 `03-business-logic-analysis.md`
4. 基于前三份报告完成 `04-issue-list.md`
5. 基于问题清单完成 `optimization-plan.md`
6. 执行过程中定期更新 `execution-report-[date].md`

## 📊 质量保证

### 文档质量检查清单
- [ ] 所有占位符已替换为实际内容
- [ ] 表格数据准确无误
- [ ] 图表清晰可读
- [ ] 命令执行结果真实有效
- [ ] 优先级分类合理
- [ ] 验收标准明确可衡量
- [ ] 风险评估全面
- [ ] 回滚方案可行

### 团队评审要点
- **技术准确性**：分析是否准确，数据是否可靠
- **优先级合理性**：问题分类和优先级是否合理
- **方案可行性**：优化方案是否切实可行
- **资源充足性**：人力和时间投入是否充足
- **风险可控性**：风险识别是否全面，缓解措施是否有效

## 💡 最佳实践

### 1. 数据驱动
- 所有结论都要有数据支撑
- 使用 Git 历史、代码度量、性能基准等客观数据
- 避免主观判断和猜测

### 2. 小步快跑
- 每个阶段控制在合理时间内完成
- 优先处理高价值、低风险的问题
- 及时验证和调整方案

### 3. 持续沟通
- 定期与团队同步进展
- 及时获取业务方反馈
- 保持文档实时更新

### 4. 知识沉淀
- 将分析过程和经验记录下来
- 建立团队知识库
- 为后续项目提供参考

---

> **提示**：这些模板是活的文档，应该根据具体项目的特点进行调整和扩展。不要被模板束缚，要灵活运用其中的方法论。
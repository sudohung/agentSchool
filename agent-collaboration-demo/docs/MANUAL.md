# Agent 协作系统使用手册

## 简介

本系统是一个基于 AutoGen + DashScope 的多Agent软件开发协作平台，支持从需求分析到部署发布的完整开发流程。

## 环境准备

### 1. 安装依赖

```bash
cd agent-collaboration-demo
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置 (可选)

如需修改 API 配置，编辑 `src/multi_agent_pipeline.py`:

```python
DASHSCOPE_API_KEY = "your-api-key"      # 替换为你的API Key
DASHSCOPE_BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
MODEL = "qwen3-coder-next"
```

## 快速开始

### 方式一：交互模式（推荐）

```bash
python src/multi_agent_pipeline.py
```

系统会依次执行 5 个阶段，每个阶段结束后等待你审批：

```
请选择操作:
  [a] 批准 (approve)
  [r] 拒绝 (reject) - 需要修改后重新提交
  [s] 跳过 (skip)
  [v] 查看完整输出
  [q] 退出
```

### 方式二：自动批准

```bash
python src/multi_agent_pipeline.py -a
```

所有阶段自动通过，无需人工干预。

### 方式三：禁用审批门

```bash
python src/multi_agent_pipeline.py --no-gates
```

完全跳过审批环节，快速执行。

## 进阶用法

### 自定义需求

```bash
python src/multi_agent_pipeline.py -r "开发一个REST API服务"
```

### 查看已保存项目

```bash
python src/multi_agent_pipeline.py --list
```

### 恢复项目继续执行

```bash
python src/multi_agent_pipeline.py -l project-001
```

### 禁用状态保存

```bash
python src/multi_agent_pipeline.py --no-save
```

### 指定状态目录

```bash
python src/multi_agent_pipeline.py --state-dir ./my_states
```

## 命令行参数汇总

| 参数 | 简写 | 说明 |
|------|------|------|
| `--auto-approve` | `-a` | 自动批准所有阶段 |
| `--no-gates` | | 完全禁用审批门 |
| `--requirement` | `-r` | 自定义需求文本 |
| `--load` | `-l` | 加载项目继续执行 |
| `--no-save` | | 禁用状态保存 |
| `--state-dir` | | 指定状态保存目录 |
| `--list` | | 列出已保存的项目 |
| `--no-opencode` | | 禁用 OpenCode 代码生成 |

## 开发流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  需求分析   │───▶│  架构设计   │───▶│  代码实现   │───▶│  测试验证   │───▶│   部署发布  │
│ Requirement │    │   Design   │    │    Code     │    │  Validation │    │   Deploy   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │                  │
   [审批门]           [审批门]           [审批门]           [审批门]           [审批门]
   [状态保存]         [状态保存]         [状态保存]         [状态保存]         [状态保存]
```

## 8角色Agent说明

| Agent | 职责 |
|-------|------|
| ProjectCoordinator | 整体流程统筹、任务调度 |
| ProjectScanner | 项目扫描、代码统计、依赖分析 |
| ArchitectureAnalyzer | 架构分析、技术债务识别 |
| BusinessLogicAnalyzer | 业务逻辑分析、领域模型 |
| IssueIdentifier | 问题识别、代码异味检测 |
| RefactoringSpecialist | 代码重构、质量优化 |
| PerformanceOptimizer | 性能分析、优化实施 |
| TestingAgent | 测试设计、覆盖率分析 |

## 状态文件

项目状态保存在 `state/` 目录下，以 JSON 格式存储：

```json
{
  "project_id": "project-001",
  "requirement": "...",
  "design_doc": "...",
  "code_output": "...",
  "test_result": "...",
  "deploy_result": "...",
  "current_stage": "deploy",
  "saved_at": "2026-03-11T12:00:00"
}
```

## 故障排除

### API 调用失败
- 检查网络连接
- 确认 API Key 有效
- 确认 API 端点正确

### 导入错误
- 确保虚拟环境已激活
- 确保依赖已安装: `pip install -r requirements.txt`

### 状态文件丢失
- 检查 `state/` 目录是否存在
- 使用 `--list` 查看可用项目

## 相关文件

```
agent-collaboration-demo/
├── src/
│   ├── main_dashscope.py      # 基础Pipeline
│   ├── code_executor.py       # 代码执行模块
│   └── multi_agent_pipeline.py # 完整版 (含审批+状态)
├── state/                     # 项目状态目录
├── docs/
│   ├── PROGRESS.md           # 开发进度
│   └── MANUAL.md             # 本文档
└── README.md
```

## 联系方式

如有问题，请提交 Issue 或联系开发团队。

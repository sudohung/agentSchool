# Agent Collaboration Demo

> 使用 AutoGen + OpenCode SDK 实现软件开发Agent协作系统

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Pipeline Orchestrator                   │
│              (5阶段: 需求→设计→编码→测试→部署)                │
└─────────────────────────────────────────────────────────────┘
          │           │           │           │           │
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │需求分析  │ │ 架构设计 │ │ 代码实现 │ │ 测试验证 │ │ 部署发布 │
    │  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
                              │
                    ┌─────────┴─────────┐
                    │  OpenCode SDK    │
                    │ (底层执行引擎)     │
                    └──────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
cd agent-collaboration-demo

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 方式1: 复制示例配置
cp .env.example .env

# 方式2: 直接设置
export OPENAI_API_KEY="your-key-here"
export MODEL="gpt-4o"

# OpenCode配置 (可选)
export OPENCODE_SERVER_URL="http://localhost:54321"
export OPENCODE_MODEL="claude-sonnet-4-5"
```

### 3. 启动OpenCode服务

```bash
# 方式1: 使用Docker (推荐)
docker compose up -d opencode

# 方式2: 本地安装
# https://opencode.ai/install
opencode serve
```

### 4. 运行Demo

```bash
python src/main.py
```

## 文件结构

```
agent-collaboration-demo/
├── src/
│   ├── main.py              # 主入口 & Pipeline
│   ├── agents.py            # Agent定义
│   ├── state.py             # 状态管理
│   └── opencode_client.py  # OpenCode集成
├── requirements.txt         # Python依赖
├── .env.example            # 环境变量示例
└── README.md
```

## 进阶扩展

### 添加更多Agent角色

参考 `skillsV1/agent-collaboration-guide/` 中的8角色框架:
- 协调者 (ProjectCoordinator)
- 项目扫描器 (ProjectScanner)
- 架构分析器 (ArchitectureAnalyzer)
- 业务逻辑分析器 (BusinessLogicAnalyzer)
- 问题识别器 (IssueIdentifier)
- 重构专家 (RefactoringSpecialist)
- 性能优化专家 (PerformanceOptimizer)
- 测试代理 (TestingAgent)

### 添加人工审核门禁

在Pipeline各阶段之间添加:

```python
async def human_approval(stage: str, content: str) -> bool:
    """人工审核门禁"""
    print(f"\n=== {stage} 审核 ===")
    print(content)
    approval = input("审核通过? (y/n): ")
    return approval.lower() == 'y'
```

## 已知问题

1. **OpenCode服务**: 需要先启动 `opencode serve`
2. **API Key**: 必须配置有效的模型API Key
3. **状态管理**: 当前使用内存存储，生产环境需用Redis

## License

MIT

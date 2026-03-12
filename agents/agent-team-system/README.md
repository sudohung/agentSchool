# Agent Team System

> 基于 Ralph Loop 哲学的 AI Agent 团队协作系统

## 项目愿景

构建一个**自主驱动的 Agent 团队系统**，能够根据用户的任务描述，动态生成相关专业的 Agents 互相协作完成需求。

## 核心理念

```
用户 (甲方) ──→ 提需求 ──→ [Agent 团队] ──→ 交付产品 ──→ 用户
                              ↑
                              │
                      Ralph Loop 内部循环
                      (用户无感知)

Ralph Loop 精神："尽管遇到挫折，但依然坚持迭代"
```

## 关键特征

| 特征 | 描述 |
|------|------|
| 🏢 **公司化运作** | 团队像公司，用户是甲方 |
| 🤝 **平等协作** | Agent 间是同事关系 |
| 📄 **文档交付** | 工作成果 = 文档 |
| 💬 **诉求驱动** | 通过诉求触发协作 |
| 🔄 **Ralph Loop** | 持续迭代，挫折中前进 |
| 🙈 **用户无感知** | 内部循环用户看不到 |

## 快速开始

```bash
# 安装依赖
pip install -e .

# 运行示例
python examples/simple_team.py
```

## 项目结构

```
agent-team-system/
├── src/                    # 源代码
│   ├── document_hub/       # 文档中心
│   ├── request_board/      # 诉求看板
│   ├── agent/              # Agent 框架
│   └── ralph_loop/         # Ralph Loop 引擎
├── tests/                  # 测试
├── docs/                   # 文档
│   ├── TODO.md            # 完整待办清单
│   └── ...
├── examples/               # 示例
└── scripts/                # 脚本工具
```

## 开发状态

详见 [TODO.md](docs/TODO.md)

## 许可证

MIT

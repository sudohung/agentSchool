# 📁 项目目录结构说明

本项目采用模块化目录结构，便于不同类型用户快速找到所需资源。

## 🏗️ 整体架构

```
agentSchool/
├── 核心开发目录/          # 主要开发代码
├── 文档资源/             # 学习和使用文档  
├── 向量数据库/           # 向量搜索相关资源
├── 重排优化/             # 排序优化相关资源
└── 辅助工具/             # 安装和配置工具
```

## 📂 详细目录说明

### 🎯 核心开发目录
```
agents/          # AI代理实现代码
mcp/            # MCP协议服务器实现  
skills/         # 自定义技能定义
training/       # 训练数据和脚本
tests/          # 测试套件
```

### 📚 文档资源 (docs/)
```
guides/         # 📖 使用指南
├── BEGINNER_GUIDE.md      # 新手入门完整指南
├── CONTRIBUTING.md        # 贡献规范说明
└── VECTOR_DB_GUIDE.md     # 向量数据库基础指南

tutorials/      # 🎓 交互式教程  
└── vector_tutorial.ipynb  # Jupyter Notebook向量数据库教程
```

### 🗄️ 向量数据库 (vector_db/)
```
examples/       # 💻 实践示例
└── vector_demo.py         # 向量数据库基础演示

optimization/   # 🎯 性能优化
├── VECTOR_RELIABILITY_OPTIMIZATION.md  # 可靠性优化文档
└── retrieval_optimization_demo.py      # 优化实践代码
```

### 🚀 重排优化 (reranking/)
```
industrial/     # 🏭 工业级方案
├── INDUSTRY_RERANKING_OPTIMIZATION.md  # 大厂级技术文档
└── industry_reranking_demo.py          # 工业级演示代码

cpu_only/       # 💻 个人电脑优化
├── CPU_OPTIMIZED_RERANKING.md          # CPU环境优化指南
└── cpu_reranking_demo.py               # CPU优化演示代码

examples/       # 💡 通用重排示例
```

### 🛠️ 辅助工具
```
requirements.txt    # Python依赖包列表
setup.bat          # Windows一键安装脚本
setup.sh           # Unix/Linux一键安装脚本
.gitignore         # Git忽略文件配置
```

## 🎯 使用路径推荐

### 🎓 新手学习路径
1. 阅读 [docs/guides/BEGINNER_GUIDE.md](docs/guides/BEGINNER_GUIDE.md)
2. 运行 [vector_db/examples/vector_demo.py](vector_db/examples/vector_demo.py)
3. 学习 [docs/tutorials/vector_tutorial.ipynb](docs/tutorials/vector_tutorial.ipynb)
4. 查阅 [docs/guides/VECTOR_DB_GUIDE.md](docs/guides/VECTOR_DB_GUIDE.md)

### 💻 个人开发者路径
1. 查看 [reranking/cpu_only/CPU_OPTIMIZED_RERANKING.md](reranking/cpu_only/CPU_OPTIMIZED_RERANKING.md)
2. 运行 [reranking/cpu_only/cpu_reranking_demo.py](reranking/cpu_only/cpu_reranking_demo.py)
3. 参考 [vector_db/optimization/](vector_db/optimization/) 中的优化方案

### 🏭 企业级开发者路径
1. 研究 [reranking/industrial/INDUSTRY_RERANKING_OPTIMIZATION.md](reranking/industrial/INDUSTRY_RERANKING_OPTIMIZATION.md)
2. 实践 [reranking/industrial/industry_reranking_demo.py](reranking/industrial/industry_reranking_demo.py)
3. 深入 [vector_db/optimization/VECTOR_RELIABILITY_OPTIMIZATION.md](vector_db/optimization/VECTOR_RELIABILITY_OPTIMIZATION.md)

### 🔧 开发者贡献路径
1. 阅读 [docs/guides/CONTRIBUTING.md](docs/guides/CONTRIBUTING.md)
2. 运行 [setup.sh](setup.sh) 或 [setup.bat](setup.bat) 进行环境配置
3. 在对应模块目录中进行开发和测试

## 📝 文件命名规范

- **文档文件**: 使用大写字母和下划线分隔 (如 `BEGINNER_GUIDE.md`)
- **代码文件**: 使用小写字母和下划线分隔 (如 `vector_demo.py`)
- **配置文件**: 使用小写字母和点号分隔 (如 `requirements.txt`)

## 🔍 快速查找表

| 需求 | 推荐路径 |
|------|----------|
| 学习基础知识 | `docs/guides/` |
| 运行示例代码 | `*/examples/` |
| 查看优化方案 | `*/optimization/` |
| 了解工业实践 | `reranking/industrial/` |
| 个人电脑优化 | `reranking/cpu_only/` |
| 交互式学习 | `docs/tutorials/` |

---
*目录结构会随着项目发展持续优化和完善*
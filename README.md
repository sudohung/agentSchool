# 🤖 Agent School

一个全面的 AI 代理训练、设计和开发项目，支持 MCP (Model Context Protocol) 和自定义技能。

[![新手友好](https://img.shields.io/badge/%F0%9F%91%B6-%E6%96%B0%E6%89%8B%E5%8F%8B%E5%A5%BD-brightgreen)](docs/guides/BEGINNER_GUIDE.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🌟 项目亮点

本项目为您提供结构化的开发环境：

- 🤖 **训练智能代理** - 构建具有学习能力的 AI 代理
- 🏗️ **设计代理架构** - 创建灵活的代理行为模式
- 🔌 **实现 MCP 服务器** - 遵循标准协议的服务器开发
- ⚡ **自定义技能系统** - 扩展代理的功能和能力
- 📚 **向量数据库支持** - 集成语义搜索和相似度匹配
- 🛡️ **检索可靠性优化** - 提升搜索准确性和稳定性
- 🚀 **工业级重排优化** - 互联网大厂成熟的排序优化方案
- 💻 **CPU-only优化** - 个人电脑环境下的高效重排方案

> 🎓 **新手？** 请先阅读我们的 [新手入门指南](docs/guides/BEGINNER_GUIDE.md)

## 📁 项目结构

```
agentSchool/
├── agents/                 # 🤖 代理实现和配置文件
├── mcp/                   # 🔌 MCP 服务器实现
├── skills/                # ⚡ 自定义技能定义和实现
├── training/              # 📊 训练数据、脚本和配置
├── tests/                 # 🧪 代理、MCP 和技能的测试套件
├── docs/                  # 📚 文档资源
│   ├── guides/           # 📖 使用指南
│   │   ├── BEGINNER_GUIDE.md          # 新手入门指南
│   │   ├── CONTRIBUTING.md            # 贡献指南
│   │   └── VECTOR_DB_GUIDE.md         # 向量数据库指南
│   └── tutorials/        # 🎓 教程资源
│       └── vector_tutorial.ipynb      # 向量数据库交互教程
├── vector_db/             # 🗄️ 向量数据库相关资源
│   ├── examples/         # 💻 代码示例
│   │   └── vector_demo.py             # 向量数据库基础演示
│   └── optimization/     # 🎯 优化方案
│       ├── VECTOR_RELIABILITY_OPTIMIZATION.md  # 可靠性优化指南
│       └── retrieval_optimization_demo.py      # 优化演示代码
├── reranking/             # 🚀 重排优化相关资源
│   ├── industrial/       # 🏭 工业级方案
│   │   ├── INDUSTRY_RERANKING_OPTIMIZATION.md  # 大厂级优化方案
│   │   └── industry_reranking_demo.py          # 工业级演示代码
│   ├── cpu_only/         # 💻 CPU优化方案
│   │   ├── CPU_OPTIMIZED_RERANKING.md          # CPU环境优化指南
│   │   └── cpu_reranking_demo.py               # CPU优化演示代码
│   └── examples/         # 💡 通用示例
├── examples/              # 📋 综合示例
├── requirements.txt       # 🔧 依赖包列表
├── setup.bat             # 🪟 Windows安装脚本
└── setup.sh              # 🐧 Unix安装脚本
```

## 🚀 快速开始

### 1. 获取代码
```bash
git clone <repository-url>
cd agentSchool
```

### 2. 安装依赖
**Node.js 开发者：**
```bash
npm install
```

**Python 开发者：**
```bash
pip install -r requirements.txt
```

**CPU优化相关依赖：**
```bash
pip install sentence-transformers numpy scikit-learn psutil
```

### 3. 环境配置
- 在 `.env` 文件中配置环境变量
- 确保已安装所需的语言运行时 (Node.js ≥ v16 或 Python ≥ 3.8)

> 💡 **提示：** Windows 用户建议使用 Git Bash 作为终端

## 🛠️ 不同环境下的优化方案

### 🌐 云端/服务器环境
- 🚀 [工业级重排优化](reranking/industrial/INDUSTRY_RERANKING_OPTIMIZATION.md) - 大厂级技术方案
- 🎯 [检索可靠性优化](vector_db/optimization/VECTOR_RELIABILITY_OPTIMIZATION.md) - 高可用架构

### 💻 个人电脑CPU-only环境
- 💻 [CPU优化重排](reranking/cpu_only/CPU_OPTIMIZED_RERANKING.md) - 轻量级高效方案
- 📊 [CPU演示代码](reranking/cpu_only/cpu_reranking_demo.py) - 实际运行示例

### 📚 学习资源总览
- 🎓 [向量数据库新手指南](docs/guides/VECTOR_DB_GUIDE.md) - 基础概念入门
- 💻 [基础演示代码](vector_db/examples/vector_demo.py) - 向量数据库基础示例
- 🔧 [可靠性优化代码](vector_db/optimization/retrieval_optimization_demo.py) - 检索质量优化实践
- 🏭 [工业级重排代码](reranking/industrial/industry_reranking_demo.py) - 大厂级重排优化实现
- 📓 [交互式教程](docs/tutorials/vector_tutorial.ipynb) - Jupyter Notebook 版本

### 🚀 快速体验
```bash
# CPU-only环境优化演示
python reranking/cpu_only/cpu_reranking_demo.py

# 基础向量数据库演示
python vector_db/examples/vector_demo.py

# 检索可靠性优化演示
python vector_db/optimization/retrieval_optimization_demo.py

# 工业级重排优化演示
python reranking/industrial/industry_reranking_demo.py

# 或在 Jupyter 中运行交互教程
jupyter notebook docs/tutorials/vector_tutorial.ipynb
```

## 🛠️ 开发指南

### 🤖 代理开发
- 在 `agents/` 目录中创建新的代理
- 遵循代理模板结构
- 实现代理逻辑和功能

### 🔌 MCP 实现
- 在 `mcp/` 目录中开发 MCP 服务器
- 确保协议合规性
- 测试与代理的集成

### ⚡ 技能系统
- 在 `skills/` 目录中定义新技能
- 实现技能功能和接口
- 将技能注册到代理系统

### 🗄️ 向量数据库集成
- 使用 `sentence-transformers` 进行文本嵌入
- 集成 FAISS 进行高效向量搜索
- 实现语义相似度匹配功能
- 根据环境选择合适的优化策略

> 📖 详细开发文档请查看 [docs/development.md](docs/development.md)

## 🧪 测试

运行测试套件验证您的实现：

```bash
# Node.js 测试
npm test

# Python 测试
python -m pytest

# CPU优化测试
python reranking/cpu_only/cpu_reranking_demo.py

# 向量数据库基础测试
python vector_db/examples/vector_demo.py

# 检索可靠性优化测试
python vector_db/optimization/retrieval_optimization_demo.py

# 工业级重排优化测试
python reranking/industrial/industry_reranking_demo.py

# 运行特定测试
npm test -- --grep="agent"
```

## 📚 文档资源

### 📖 使用指南
- 🎓 [新手入门指南](docs/guides/BEGINNER_GUIDE.md) - 专为初学者设计的完整指南
- 📚 [向量数据库指南](docs/guides/VECTOR_DB_GUIDE.md) - 向量数据库和嵌入模型详解
- 🤝 [贡献指南](docs/guides/CONTRIBUTING.md) - 如何参与项目开发

### 🎯 技术文档
- 🎯 [检索可靠性优化](vector_db/optimization/VECTOR_RELIABILITY_OPTIMIZATION.md) - 提升检索质量的最佳实践
- 🚀 [工业级重排优化](reranking/industrial/INDUSTRY_RERANKING_OPTIMIZATION.md) - 互联网大厂成熟技术方案
- 💻 [CPU优化重排](reranking/cpu_only/CPU_OPTIMIZED_RERANKING.md) - 个人电脑环境高效方案

### 💻 代码示例
- 💻 [基础示例](vector_db/examples/vector_demo.py) - 向量数据库基础演示
- 🔧 [优化示例](vector_db/optimization/retrieval_optimization_demo.py) - 可靠性优化实践代码
- 🏭 [重排示例](reranking/industrial/industry_reranking_demo.py) - 工业级重排优化代码
- 🖥️ [CPU优化示例](reranking/cpu_only/cpu_reranking_demo.py) - 个人电脑优化代码

### 📓 教程资源
- 📓 [交互教程](docs/tutorials/vector_tutorial.ipynb) - Jupyter Notebook 教程

## 🛠️ 快速安装

我们提供了自动化安装脚本：

**Windows 用户：**
```cmd
setup.bat
```

**Mac/Linux 用户：**
```bash
chmod +x setup.sh
./setup.sh
```

脚本将自动：
- 检查系统环境
- 安装必要依赖
- 创建配置文件
- 运行初始测试

## 🤝 贡献指南

我们欢迎您的贡献！

1. 🍴 Fork 本仓库
2. 🌿 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 💾 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. ⬆️ 推送到分支 (`git push origin feature/AmazingFeature`)
5. 📝 开启 Pull Request

> 📋 请先阅读 [贡献指南](docs/guides/CONTRIBUTING.md) 了解详细规范

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

<p align="center">
  <strong>🌟 喜欢这个项目？给它一个 Star 吧！</strong>
</p>
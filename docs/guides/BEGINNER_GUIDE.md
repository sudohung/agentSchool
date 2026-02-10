# 🎓 新手入门指南 - Agent School

欢迎来到 Agent School！这是一个帮助您学习和开发 AI 代理的友好项目。无论您是编程新手还是经验丰富的开发者，本指南都将帮助您顺利开始。

## 🌟 项目简介

Agent School 是一个综合性的 AI 代理开发平台，让您可以：
- 🤖 训练智能代理
- 🏗️ 设计代理架构和行为
- 🔌 实现 MCP (Model Context Protocol) 服务器
- ⚡ 创建和测试自定义技能

## 🚀 快速开始

### 第一步：准备工作

**系统要求：**
- Windows 10/11 (您的系统版本：Windows 22H2 ✅)
- Git (您已安装：C:\Program Files\Git\bin\bash.exe ✅)
- Node.js (推荐 v16+) 或 Python (推荐 3.8+)

### 第二步：获取项目代码

如果您还没有克隆项目，请打开终端执行：

```bash
git clone <您的仓库地址>
cd agentSchool
```

### 第三步：安装依赖

根据您的开发偏好选择：

**Node.js 开发者：**
```bash
npm install
```

**Python 开发者：**
```bash
pip install -r requirements.txt
```

## 📁 项目结构详解

```
agentSchool/
├── agents/          # 🔧 代理实现和配置文件
├── mcp/            # 🔌 MCP 服务器实现
├── skills/         # ⚡ 自定义技能定义
├── training/       # 📊 训练数据和脚本
├── tests/          # 🧪 测试套件
└── docs/           # 📚 文档和指南
```

## 👶 新手专属学习路径

### 🥇 第一周：环境搭建
1. 确保所有开发工具正常工作
2. 成功运行第一个 "Hello World" 代理
3. 熟悉项目目录结构

### 🥈 第二周：基础知识
1. 学习代理的基本概念
2. 理解 MCP 协议的作用
3. 创建简单的自定义技能

### 🥉 第三周：实践项目
1. 开发一个实用的代理功能
2. 集成多个技能
3. 编写测试用例

## 💡 常见问题解答

### Q: 我应该选择 Node.js 还是 Python？
**A:** 
- 如果您熟悉 JavaScript/TypeScript → 选择 Node.js
- 如果您熟悉 Python 或做数据科学 → 选择 Python
- 两个都可以，项目支持双语言开发

### Q: 遇到依赖安装错误怎么办？
**A:**
1. 确保网络连接正常
2. 尝试清除缓存：`npm cache clean --force` 或 `pip cache purge`
3. 检查 Node.js/Python 版本是否符合要求

### Q: 如何测试我的代码？
**A:**
```bash
# Node.js
npm test

# Python  
python -m pytest
```

## 🛠️ 开发工具推荐

### IDE 设置
**IntelliJ IDEA 用户（您的 IDE ✅）：**
- 安装 Node.js 插件
- 配置 Git 集成
- 启用代码自动补全

### 终端使用技巧
由于您使用的是 Git Bash，这里有一些有用的命令：

```bash
# 查看当前目录
pwd

# 列出文件
ls -la

# 创建新目录
mkdir my-agent

# 进入目录
cd my-agent
```

## 🎯 学习资源

### 内部文档
- 📖 [技术文档](docs/technical.md) - 深入技术细节
- 🎨 [设计指南](docs/design.md) - 架构设计原则
- 🔧 [API 参考](docs/api.md) - 接口文档

### 外部资源
- [MCP 官方文档](https://modelcontextprotocol.io/)
- [AI 代理开发最佳实践](https://ai.google/research/pubs/pub49032)

## 🤝 寻求帮助

遇到问题时：

1. **查阅文档** - 先查看相关文档
2. **搜索 Issues** - 在 GitHub Issues 中搜索类似问题
3. **提问** - 在讨论区提出具体问题，包含：
   - 错误信息截图
   - 相关代码片段
   - 您已经尝试过的解决方案

## 🌈 下一步行动

✅ **立即行动清单：**
- [ ] 克隆项目到本地
- [ ] 安装必要的依赖
- [ ] 运行第一个示例程序
- [ ] 浏览项目目录结构
- [ ] 阅读技术文档

💡 **小贴士：**
- 保持耐心，学习新技术需要时间
- 多动手实践，理论结合实际
- 记录学习笔记，方便日后回顾
- 参与社区讨论，与其他开发者交流

---

🎉 **恭喜您开始这段精彩的 AI 开发之旅！如有任何疑问，随时寻求帮助。**

*最后更新：2026年2月10日*
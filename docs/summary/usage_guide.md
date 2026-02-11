# Agent School 项目使用指南

## 1. 环境准备

### 1.1 系统要求
- **操作系统**: Windows 10/11, macOS, Linux
- **开发工具**: Git, Node.js (≥ v16) 或 Python (≥ 3.8)
- **IDE推荐**: IntelliJ IDEA, VS Code

### 1.2 安装步骤
```bash
# 克隆项目
git clone <repository-url>
cd agentSchool

# 安装依赖（选择其一）
npm install          # Node.js 开发者
pip install -r requirements.txt  # Python 开发者

# CPU优化相关依赖
pip install sentence-transformers numpy scikit-learn psutil
```

### 1.3 环境配置
- 创建 `.env` 文件配置环境变量
- Windows 用户建议使用 Git Bash 作为终端

## 2. 新手学习路径

### 2.1 第一周：环境搭建
- [ ] 确保所有开发工具正常工作
- [ ] 成功运行第一个 "Hello World" 代理
- [ ] 熟悉项目目录结构

### 2.2 第二周：基础知识
- [ ] 学习代理的基本概念
- [ ] 理解 MCP 协议的作用
- [ ] 创建简单的自定义技能

### 2.3 第三周：实践项目
- [ ] 开发一个实用的代理功能
- [ ] 集成多个技能
- [ ] 编写测试用例

## 3. 核心功能使用

### 3.1 文档专家代理 (doc-agent)
**适用场景**:
- 撰写技术文档、设计文档、API 文档
- 创建或编辑 Word、PDF、PPT 文件
- 编写项目报告、周报、FAQ
- 绘制架构图、流程图、ER图、时序图

**使用方法**:
1. 加载相应技能（doc-coauthoring, docx, pdf, pptx）
2. 按照标准化六模块结构撰写文档
3. 使用 Mermaid 绘制所有图表（禁止 ASCII 伪图表）

**文档模板**:
```markdown
# [系统名称] 业务技术文档

## 1. 业务概述
## 2. 系统架构  
## 3. 数据设计
## 4. 接口文档
## 5. 部署运维
## 6. 变更记录
```

### 3.2 Java系统分析代理 (java-analyst-agent)
**适用场景**:
- 接手遗留 Java 项目，快速理解系统全貌
- 为新人创建项目上手文档
- 重构前梳理现有架构
- 进行技术债务评估

**分析流程**:
1. 项目全貌扫描（技术栈、代码规模、Git历史）
2. 技术架构解析（依赖、配置、入口点）
3. 模块结构梳理（包结构、核心类、接口）
4. 核心业务追踪（调用链、数据流）
5. 数据层理解（实体、表结构、SQL）
6. 文档输出（完整系统文档）

**常用命令**:
```bash
# Git分析
git shortlog -sn --all | head -10
git log --name-only | sort | uniq -c | sort -rn

# 代码分析  
find . -name "*.java" | wc -l
grep -rn "@RestController" --include="*.java"
```

### 3.3 多代理文档验证
**使用场景**: 验证技术文档是否与实际代码保持同步

**操作步骤**:
1. 提供要验证的文档路径
2. 协调器自动分析文档并生成任务文件
3. 9个专家代理并行执行验证（8-12分钟）
4. 生成中文综合验证报告

**验证维度**:
- 实体模型 vs 代码类
- ER图 vs JPA实体
- API接口 vs Controller
- 方法签名 vs Service方法
- 状态机 vs 代码逻辑
- 业务流程 vs 实现
- 数据流 vs 转换逻辑
- 文件引用 vs 实际路径
- 文档结构 vs 完整性

### 3.4 MySQL MCP Server
**使用场景**: 通过数据了解业务形态，无需编写复杂SQL

**启动步骤**:
```bash
# 配置数据库连接
cp .env.example .env
# 编辑 .env 文件设置数据库参数

# 启动服务器
python mysql_mcp_server.py --transport streamable_http --port 8000
# 或使用Windows脚本: start.bat
```

**核心功能**:
- 列出所有数据库和表
- 查看表结构和字段信息
- 抽样查看表数据
- 分析表统计信息
- 查看外键关系
- 执行自定义只读查询

### 3.5 向量数据库演示
**运行基础演示**:
```bash
python vector_db/examples/vector_demo.py
```

**功能包括**:
- 文本到向量转换
- 向量数据库创建
- 相似度搜索
- 简易问答系统
- 性能对比测试

### 3.6 重排优化演示
**CPU优化演示**:
```bash
python reranking/cpu_only/cpu_reranking_demo.py
```

**自适应配置**:
- 内存≤4GB: 入门级配置（规则重排）
- 内存4-8GB: 标准级配置（混合重排）
- 内存≥8GB: 高性能配置（ML重排）

## 4. 开发指南

### 4.1 代理开发
1. 在 `agents/` 目录中创建新的代理
2. 遵循代理模板结构
3. 实现代理逻辑和功能
4. 定义所需技能

### 4.2 MCP 实现
1. 在 `mcp/` 目录中开发 MCP 服务器
2. 确保协议合规性
3. 测试与代理的集成

### 4.3 技能系统
1. 在 `skills/` 目录中定义新技能
2. 实现技能功能和接口
3. 将技能注册到代理系统

### 4.4 向量数据库集成
1. 使用 `sentence-transformers` 进行文本嵌入
2. 集成 FAISS 进行高效向量搜索
3. 实现语义相似度匹配功能
4. 根据环境选择合适的优化策略

## 5. 测试与调试

### 5.1 运行测试
```bash
# Node.js 测试
npm test

# Python 测试  
python -m pytest

# 特定功能测试
python vector_db/examples/vector_demo.py
python reranking/cpu_only/cpu_reranking_demo.py
python vector_db/optimization/retrieval_optimization_demo.py
python reranking/industrial/industry_reranking_demo.py
```

### 5.2 调试技巧
- 查看详细日志输出
- 使用性能监控器分析执行时间
- 检查内存使用情况
- 验证配置文件正确性

## 6. 常见问题解答

### 6.1 依赖安装问题
- 确保网络连接正常
- 尝试清除缓存：`npm cache clean --force` 或 `pip cache purge`
- 检查 Node.js/Python 版本是否符合要求

### 6.2 内存不足问题
- CPU重排演示会自动检测内存并选择合适配置
- 可手动指定配置级别：入门级、标准级、高性能
- 关闭不必要的应用程序释放内存

### 6.3 文档验证失败
- 检查文档格式是否符合要求
- 确认源代码路径是否正确
- 查看验证器执行日志获取详细错误信息

### 6.4 MCP连接问题
- 检查数据库连接参数是否正确
- 确认数据库服务是否正常运行
- 验证防火墙设置是否允许连接

## 7. 贡献指南

### 7.1 贡献流程
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 7.2 开发规范
- 遵循现有代码风格
- 编写完整的测试用例
- 更新相关文档
- 确保向后兼容性

## 8. 学习资源

### 8.1 内部文档
- [新手入门指南](docs/guides/BEGINNER_GUIDE.md)
- [向量数据库指南](docs/guides/VECTOR_DB_GUIDE.md)
- [贡献指南](docs/guides/CONTRIBUTING.md)

### 8.2 技术文档
- [检索可靠性优化](vector_db/optimization/VECTOR_RELIABILITY_OPTIMIZATION.md)
- [工业级重排优化](reranking/industrial/INDUSTRY_RERANKING_OPTIMIZATION.md)
- [CPU优化重排](reranking/cpu_only/CPU_OPTIMIZED_RERANKING.md)

### 8.3 代码示例
- [基础示例](vector_db/examples/vector_demo.py)
- [优化示例](vector_db/optimization/retrieval_optimization_demo.py)
- [重排示例](reranking/industrial/industry_reranking_demo.py)
- [CPU优化示例](reranking/cpu_only/cpu_reranking_demo.py)

### 8.4 教程资源
- [交互教程](docs/tutorials/vector_tutorial.ipynb) - Jupyter Notebook 教程

## 9. 快速参考

### 9.1 目录结构
```
agentSchool/
├── agents/          # AI代理实现
├── mcp/            # MCP服务器实现
├── skillsV1/       # 自定义技能定义
├── vector_db/      # 向量数据库资源
├── reranking/      # 重排优化资源
├── my-video/       # 视频演示内容
├── docs/           # 文档资源
└── requirements.txt # 依赖管理
```

### 9.2 常用命令
```bash
# 安装依赖
npm install
pip install -r requirements.txt

# 运行演示
python vector_db/examples/vector_demo.py
python reranking/cpu_only/cpu_reranking_demo.py

# 启动MCP服务器
python mysql_mcp_server.py --transport streamable_http --port 8000

# 运行测试
npm test
python -m pytest
```

### 9.3 环境变量
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
```

---
**提示**: 本指南将持续更新，请定期查看最新版本以获取最新功能和最佳实践。

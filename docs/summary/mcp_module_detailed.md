# MCP 模块详细分析报告

## 1. 概述

MCP (Model Context Protocol) 模块是 AgentSchool 项目中的核心数据访问层，提供了一套标准化的工具接口，使 AI 助手能够安全、高效地与各种数据源进行交互。当前项目包含三个主要的 MCP 模块：

1. **MySQL MCP Server** - 用于 MySQL 数据库探索和分析
2. **Memory/Knowledge Base MCP** - 用于本地知识库的读写操作
3. **FAISS Semantic Search MCP** - 用于向量语义搜索和知识存储

这些模块共同构成了一个完整的数据访问生态系统，支持从结构化数据库到非结构化知识的全方位数据交互。

## 2. MySQL MCP Server 详细分析

### 2.1 核心功能

MySQL MCP Server 是一个专门用于 MySQL 数据库分析的工具集，提供以下 8 个核心工具：

#### 2.1.1 数据库发现工具
- `mysql_list_databases`: 列出所有可用数据库
- `mysql_database_overview`: 获取数据库概览信息（表数量、大小、字符集等）

#### 2.1.2 表结构分析工具
- `mysql_list_tables`: 列出数据库中的所有表
- `mysql_get_table_schema`: 获取表的详细结构（字段、索引、外键）
- `mysql_analyze_table_statistics`: 分析表统计信息（行数、空值、唯一值分布）

#### 2.1.3 数据探索工具
- `mysql_sample_table_data`: 抽样查看表中的实际数据
- `mysql_list_foreign_key_relationships`: 查看表之间的外键关系
- `mysql_execute_custom_query`: 执行自定义只读查询

### 2.2 架构设计

#### 2.2.1 技术栈
- **核心框架**: FastMCP (基于 Model Context Protocol)
- **数据库驱动**: PyMySQL
- **数据验证**: Pydantic
- **配置管理**: python-dotenv

#### 2.2.2 连接管理
- 使用 `DatabaseClient` 类实现连接池管理
- 支持生命周期管理（启动时初始化，关闭时清理）
- 自动重连机制
- 异步操作支持

#### 2.2.3 安全机制
- **只读保护**: 所有工具都标记为 `readOnlyHint: true`
- **查询限制**: 自定义查询工具仅允许 SELECT 语句
- **参数限制**: 对 LIMIT 等参数进行范围限制
- **SQL 注入防护**: 使用参数化查询

### 2.3 配置方式

#### 2.3.1 环境变量配置
通过 `.env` 文件配置数据库连接：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
MYSQL_CHARSET=utf8mb4
```

#### 2.3.2 命令行参数
支持运行时配置：
```bash
python mysql_mcp_server.py --transport streamable_http --port 8000
```

#### 2.3.3 OpenCode 集成配置
在 `opencode_config.json` 中配置：

```json
{
  "mcpServers": {
    "mysql": {
      "command": "python",
      "args": ["start_opencode_mcp.py"],
      "cwd": "path/to/mysqlMcp"
    }
  }
}
```

### 2.4 输出格式

所有工具支持两种输出格式：
- **Markdown**: 人类可读的格式，适合探索和理解
- **JSON**: 结构化数据，适合程序处理

### 2.5 启动方式

#### 2.5.1 HTTP 传输（推荐）
```bash
python mysql_mcp_server.py --transport streamable_http --port 8000
```
服务器在 `http://localhost:8000` 启动，支持远程访问。

#### 2.5.2 Stdio 传输（本地工具）
```bash
python mysql_mcp_server.py --transport stdio
```
适用于 Claude Desktop 等本地工具。

#### 2.5.3 Windows 批处理
提供 `start.bat` 脚本，自动处理依赖安装和启动。

### 2.6 集成方式

#### 2.6.1 Claude Desktop 集成
1. 编辑 `%APPDATA%\Claude\claude_desktop_config.json`
2. 添加 MCP 服务器配置
3. 重启 Claude Desktop

#### 2.6.2 Python 客户端集成
使用 `mcp` 包进行编程调用：

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["mysql_mcp_server.py", "--transport", "stdio"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        result = await session.call_tool("mysql_list_databases", arguments={})
```

#### 2.6.3 MCP Inspector 调试
```bash
npx @modelcontextprotocol/inspector
```

## 3. Memory/Knowledge Base MCP 详细分析

### 3.1 模块分离设计

Memory MCP 采用读写分离的架构设计：
- **kb_search_mcp_server.py**: 只读检索服务
- **kb_write_mcp_server.py**: 写入服务（未在本次分析中详细查看）

### 3.2 数据模型

#### 3.2.1 知识条目类型
- `business_knowledge`: 业务知识
- `code_snippet`: 代码片段
- `documentation`: 文档
- `faq`: 常见问题
- `best_practice`: 最佳实践

#### 3.2.2 数据结构
每个知识条目包含：
- `id`: 唯一标识符
- `title`: 标题
- `content`: 内容
- `type`: 类型
- `category`: 分类
- `tags`: 标签数组
- `language`: 编程语言（针对代码片段）
- `source`: 来源
- `confidence`: 置信度
- `created_at/updated_at`: 时间戳
- `metadata`: 额外元数据

### 3.3 功能特性

#### 3.3.1 高级搜索
- 全文搜索（支持 FTS5）
- 多维度过滤（类型、分类、标签、语言）
- 相关性排序
- 分页支持

#### 3.3.2 统计分析
- 总条目数统计
- 类型分布分析
- 分类和标签统计
- 语言分布

### 3.4 技术实现

- **数据库**: SQLite
- **全文搜索**: FTS5（可选）
- **JSON 存储**: 标签和元数据以 JSON 格式存储
- **连接管理**: 单例模式，线程安全

## 4. FAISS Semantic Search MCP 详细分析

### 4.1 核心功能

FAISS MCP 提供基于向量的语义搜索能力：

#### 4.1.1 知识存储
- `faiss_add_items`: 添加新知识条目
- `faiss_save`: 持久化索引和元数据

#### 4.1.2 语义搜索
- `faiss_search`: 基于文本或向量的语义搜索

### 4.2 多硬件支持

#### 4.2.1 CPU 支持
- 使用 `sentence-transformers` 库
- 默认模型：`all-MiniLM-L6-v2` (384维)

#### 4.2.2 NVIDIA GPU 支持
- 使用 CUDA 加速
- 支持本地模型路径
- 可配置 GPU ID

#### 4.2.3 AMD GPU 支持
- 使用 ONNX Runtime + DirectML
- 支持 ONNX 模型格式

### 4.3 配置管理

通过 `embedder_config.json` 文件配置：

```json
{
  "device": "nv_gpu",
  "nv_gpu": {
    "gpu_id": 0,
    "model_path": "C:\Users\hung\Desktop\workspace\modelscope\bge-m3",
    "dim": 1024
  },
  "faiss": {
    "nv_gpu": {
      "index_path": "./faiss/nv_gpu/faiss.index",
      "meta_path": "./faiss/nv_gpu/faiss_meta.json"
    }
  }
}
```

### 4.4 技术栈

- **向量引擎**: FAISS
- **嵌入模型**: Sentence Transformers / ONNX Runtime
- **数据序列化**: NumPy
- **配置管理**: JSON + 环境变量

## 5. 模块间集成与协作

### 5.1 数据流架构

```
AI Assistant (Claude)
       ↓
MCP Router/Dispatcher
       ↓
┌─────────────────┐
│ MySQL MCP       │ ←→ MySQL Database
├─────────────────┤
│ Memory MCP      │ ←→ SQLite Knowledge Base  
├─────────────────┤
│ FAISS MCP       │ ←→ FAISS Index + Embeddings
└─────────────────┘
```

### 5.2 使用场景示例

#### 5.2.1 数据库探索场景
1. 用户询问："帮我分析一下订单系统"
2. AI 调用 `mysql_list_databases` 找到相关数据库
3. 调用 `mysql_list_tables` 发现 orders、users 表
4. 调用 `mysql_get_table_schema` 理解表结构
5. 调用 `mysql_sample_table_data` 查看示例数据
6. 调用 `mysql_analyze_table_statistics` 分析数据质量
7. 调用 `mysql_list_foreign_key_relationships` 理解关系
8. 综合分析结果并回答用户

#### 5.2.2 知识检索场景
1. 用户询问："如何处理用户认证？"
2. AI 调用 `kb_search_knowledge` 搜索相关知识
3. 在结果中找到最佳实践文档
4. 返回详细的操作指南

#### 5.2.3 语义搜索场景
1. 用户描述需求："我需要一个能处理大量并发请求的缓存方案"
2. AI 调用 `faiss_search` 进行语义匹配
3. 返回相关的技术方案和代码示例
4. 提供具体的实现建议

### 5.3 配置协同

三个模块可以同时运行，通过不同的端口提供服务：
- MySQL MCP: 默认端口 8000
- Memory MCP: 默认端口 8326  
- FAISS MCP: 默认端口 8001

在 Claude Desktop 配置中可以同时注册多个 MCP 服务器：

```json
{
  "mcpServers": {
    "mysql": { /* MySQL 配置 */ },
    "knowledge": { /* Knowledge 配置 */ },
    "semantic": { /* FAISS 配置 */ }
  }
}
```

## 6. 安全性和性能考虑

### 6.1 安全措施

#### 6.1.1 数据库安全
- 只读操作，防止数据修改
- 查询限制，防止资源耗尽
- 参数化查询，防止 SQL 注入

#### 6.1.2 知识库安全
- 读写分离，控制权限
- 输入验证，防止恶意数据
- 文件路径安全，防止目录遍历

#### 6.1.3 向量搜索安全
- 向量维度验证
- 内存使用限制
- 模型加载安全

### 6.2 性能优化

#### 6.2.1 数据库优化
- 连接复用，减少连接开销
- 异步操作，提高并发能力
- 结果限制，控制内存使用

#### 6.2.2 知识库优化
- SQLite 索引优化
- FTS5 全文搜索加速
- 分页查询，避免大数据集

#### 6.2.3 向量搜索优化
- FAISS 索引优化
- GPU 加速（NVIDIA/AMD）
- 批量处理支持

## 7. 部署和维护

### 7.1 依赖管理

#### 7.1.1 MySQL MCP
```txt
fastmcp>=0.3.0
PyMySQL>=1.1.0
pydantic>=2.0.0
httpx>=0.25.0
```

#### 7.1.2 Memory MCP
- SQLite（Python 内置）
- FastMCP
- Pydantic

#### 7.1.3 FAISS MCP
- faiss
- numpy
- sentence-transformers
- torch（GPU 支持）
- onnxruntime-directml（AMD GPU 支持）

### 7.2 监控和日志

- 详细的日志记录（INFO 级别）
- 错误处理和异常捕获
- 连接状态监控
- 性能指标记录

### 7.3 备份和恢复

#### 7.3.1 MySQL MCP
- 无持久化数据，依赖外部数据库

#### 7.3.2 Memory MCP
- SQLite 数据库文件备份
- 定期导出知识条目

#### 7.3.3 FAISS MCP
- FAISS 索引文件备份
- 元数据 JSON 文件备份
- 模型文件版本控制

## 8. 扩展性和定制化

### 8.1 工具扩展

所有 MCP 模块都遵循相同的开发模式：
1. 创建 Pydantic Input 模型
2. 使用 `@mcp.tool()` 装饰器
3. 实现异步函数
4. 处理错误和返回格式

### 8.2 模型定制

- 支持自定义嵌入模型
- 可配置向量维度
- 支持本地模型路径

### 8.3 部署定制

- 可配置端口和主机
- 支持不同传输协议
- 环境变量覆盖配置

## 9. 总结

MCP 模块为 AgentSchool 项目提供了强大的数据访问能力，具有以下特点：

1. **标准化**: 遵循 MCP 协议标准，易于集成
2. **安全性**: 严格的只读保护和输入验证
3. **灵活性**: 支持多种数据源和部署方式
4. **高性能**: 异步操作和硬件加速支持
5. **易用性**: 丰富的文档和示例
6. **可扩展**: 模块化设计，便于功能扩展

这三个 MCP 模块共同构成了一个完整的数据访问解决方案，能够满足从传统关系型数据库到现代向量数据库的各种数据交互需求。

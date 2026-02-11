# MySQL MCP 服务器使用指南

## 什么是 MCP？

MCP (Model Context Protocol) 是一个协议标准，让 AI 助手（如 Claude）能够安全地访问外部数据和工具。

这个 MySQL MCP 服务器提供了 8 个工具，让 AI 可以探索和查询 MySQL 数据库。

---

## 使用方式

### 方式一：Claude Desktop（最简单）⭐

#### 1. 安装 Claude Desktop
从官网下载：https://claude.ai/download

#### 2. 配置服务器
编辑配置文件：`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mysql": {
      "command": "python",
      "args": [
        "E:\\workspace\\xpproject\\agent_skill_python\\mcp\\mysqlMcp\\mysql_mcp_server.py"
      ],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "your_password_here",
        "MYSQL_DATABASE": "your_database_name"
      }
    }
  }
}
```

#### 3. 重启 Claude Desktop

#### 4. 开始使用
在对话中直接说：
- "列出所有数据库"
- "显示 users 表的结构"
- "查询订单表数据，限制10条"
- "分析 products 表的统计信息"

---

### 方式二：MCP Inspector（用于测试调试）

#### 1. 安装
```bash
npm install -g @modelcontextprotocol/inspector
```

#### 2. 启动
```bash
cd E:\workspace\xpproject\agent_skill_python\mcp\mysqlMcp
mcp-inspector python mysql_mcp_server.py
```

#### 3. 在浏览器中测试
自动打开网页界面，可以：
- 查看所有工具
- 测试每个工具
- 查看请求/响应

---

### 方式三：Python 客户端（编程方式）

#### 1. 安装依赖
```bash
pip install mcp
```

#### 2. 运行测试客户端
```bash
python test_client.py
```

修改 `test_client.py` 中的数据库连接信息后运行。

---

## 可用的 8 个工具

1. **mysql_list_databases**
   - 列出所有数据库
   - 参数：format (text/json/markdown)

2. **mysql_database_overview**
   - 获取数据库概览（表数量、大小等）
   - 参数：database_name, format

3. **mysql_list_tables**
   - 列出指定数据库的所有表
   - 参数：database_name, format

4. **mysql_get_table_schema**
   - 获取表的详细结构（字段、类型、索引等）
   - 参数：database_name, table_name, format

5. **mysql_sample_table_data**
   - 查询表的示例数据
   - 参数：database_name, table_name, limit (默认10), format

6. **mysql_analyze_table_statistics**
   - 分析表统计信息（行数、大小、索引使用率等）
   - 参数：database_name, table_name, format

7. **mysql_list_foreign_key_relationships**
   - 列出外键关系
   - 参数：database_name, format

8. **mysql_execute_custom_query**
   - 执行自定义只读查询（SELECT/SHOW/DESCRIBE/EXPLAIN）
   - 参数：database_name, query, format

---

## 配置数据库连接

### 方式 1：环境变量（推荐）
编辑 `.env` 文件：
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
MYSQL_CHARSET=utf8mb4
```

### 方式 2：Claude Desktop 配置
在 `claude_desktop_config.json` 的 `env` 字段中设置

---

## 安全说明

- ✅ 所有查询都是**只读**的（使用事务并回滚）
- ✅ 只允许 SELECT、SHOW、DESCRIBE、EXPLAIN 等安全命令
- ❌ 禁止 INSERT、UPDATE、DELETE、DROP 等修改操作
- ❌ 禁止创建/删除表、用户等管理操作

---

## 故障排查

### 问题 1：服务器无法启动
```bash
# 检查 Python 版本
python --version  # 需要 3.8+

# 检查依赖
pip install -r requirements.txt

# 直接运行测试
python mysql_mcp_server.py
```

### 问题 2：无法连接数据库
- 检查 MySQL 服务是否运行
- 验证用户名/密码是否正确
- 确认数据库名称存在
- 检查防火墙设置

### 问题 3：Claude Desktop 看不到工具
- 确认配置文件路径正确
- 重启 Claude Desktop
- 检查配置文件 JSON 格式是否正确

---

## 示例对话

**用户**: "帮我分析一下 orders 表的数据"

**Claude**: 
1. 首先调用 `mysql_get_table_schema` 查看表结构
2. 然后调用 `mysql_sample_table_data` 查看示例数据
3. 最后调用 `mysql_analyze_table_statistics` 获取统计信息
4. 综合分析并给出报告

---

## 进阶使用

### 自定义查询示例
```json
{
  "database_name": "shop",
  "query": "SELECT category, COUNT(*) as count, AVG(price) as avg_price FROM products GROUP BY category",
  "format": "markdown"
}
```

### 联合多个工具
1. 先用 `list_databases` 找到目标数据库
2. 用 `list_tables` 查看有哪些表
3. 用 `get_table_schema` 理解表结构
4. 用 `sample_table_data` 查看数据
5. 用 `execute_custom_query` 执行复杂分析

---

## 更多帮助

- MCP 官方文档: https://modelcontextprotocol.io
- FastMCP 文档: https://github.com/jlowin/fastmcp
- 问题反馈: 创建 GitHub Issue

---

**享受使用 AI 探索数据库的乐趣！** 🚀

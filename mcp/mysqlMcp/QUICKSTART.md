# MySQL MCP Server - 快速开始

## 简介

MySQL MCP Server 是一个基于 Model Context Protocol (MCP) 的数据库分析工具，帮助你通过数据了解业务形态，无需编写复杂SQL即可探索数据库结构和内容。

## 主要功能

- ✅ 列出数据库和表
- ✅ 查看表结构（字段、索引、外键）
- ✅ 抽样查看数据
- ✅ 分析数据统计信息
- ✅ 查看表关系（ER图）
- ✅ 执行自定义查询

## 快速安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库连接

**方式一：环境变量（推荐）**

创建 `.env` 文件：

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database  # 可选
```

**方式二：启动时指定**

连接配置也可以在使用工具时动态提供。

## 启动服务器

### Windows

```bash
start.bat
```

### Linux/Mac

```bash
python mysql_mcp_server.py --transport streamable_http --port 8000
```

服务器将在 `http://localhost:8000` 启动。

## 使用示例

### 场景1: 探索未知数据库

**目标**: 了解一个新数据库的业务结构

```bash
# 1. 列出所有数据库
mysql_list_databases

# 2. 选择目标数据库，查看概览
mysql_database_overview database=your_db

# 3. 列出所有表
mysql_list_tables database=your_db

# 4. 查看核心表结构
mysql_get_table_schema table=users
mysql_get_table_schema table=orders

# 5. 抽样查看数据
mysql_sample_table_data table=users limit=5
mysql_sample_table_data table=orders limit=5

# 6. 查看表关系
mysql_list_foreign_key_relationships direction=both
```

### 场景2: 分析用户系统

**目标**: 理解用户表的结构和数据质量

```bash
# 1. 找出所有用户相关表
mysql_list_tables table_pattern=%user%

# 2. 查看用户表结构
mysql_get_table_schema table=users

# 3. 查看示例数据
mysql_sample_table_data table=users limit=10

# 4. 分析数据统计
mysql_analyze_table_statistics table=users

# 5. 查看用户表的关联关系
mysql_list_foreign_key_relationships table=users direction=both
```

### 场景3: 业务指标统计

**目标**: 分析订单数据

```bash
# 1. 查看订单表结构
mysql_get_table_schema table=orders

# 2. 统计不同状态的订单数量
mysql_execute_custom_query query="SELECT status, COUNT(*) as count FROM orders GROUP BY status ORDER BY count DESC"

# 3. 查看最近的订单
mysql_sample_table_data table=orders limit=10 order_by="created_at DESC"

# 4. 分析订单表数据质量
mysql_analyze_table_statistics table=orders
```

## 工具列表

### 1. `mysql_list_databases` - 列出数据库

**用途**: 查看MySQL服务器上的所有数据库

**常用参数**:
- `include_system`: 是否包含系统数据库（默认：否）
- `filter_pattern`: 使用SQL LIKE模式过滤（如 `%prod%`）

**示例**:
```yaml
mysql_list_databases:
  include_system: false
  filter_pattern: "%app%"
```

### 2. `mysql_database_overview` - 数据库概览

**用途**: 查看数据库的基本信息、表数量、大小

**常用参数**:
- `database`: 数据库名称（可选，使用默认数据库）
- `include_table_count`: 是否包含表数量（默认：是）
- `include_size`: 是否包含大小信息（默认：是）

**示例**:
```yaml
mysql_database_overview:
  database: "business_db"
```

### 3. `mysql_list_tables` - 列出表

**用途**: 查看数据库中的所有表

**常用参数**:
- `database`: 数据库名称（可选）
- `table_pattern`: 表名过滤模式（如 `%user%`）
- `include_views`: 是否包含视图（默认：否）
- `limit`: 最多返回的表数量

**示例**:
```yaml
mysql_list_tables:
  table_pattern: "%order%"
  limit: 20
```

### 4. `mysql_get_table_schema` - 表结构

**用途**: 查看表的详细结构（字段、索引、外键）

**常用参数**:
- `table`: 表名（必需）
- `include_indexes`: 是否包含索引信息（默认：是）
- `include_foreign_keys`: 是否包含外键信息（默认：是）

**示例**:
```yaml
mysql_get_table_schema:
  table: "users"
```

### 5. `mysql_sample_table_data` - 抽样数据

**用途**: 查看表中的实际数据样本

**常用参数**:
- `table`: 表名（必需）
- `limit`: 返回的行数（默认：10，最大：100）
- `columns`: 指定列（逗号分隔，如 `id,name,email`）
- `where_clause`: WHERE条件（如 `status="active"`）
- `order_by`: 排序（如 `created_at DESC`）

**示例**:
```yaml
mysql_sample_table_data:
  table: "orders"
  limit: 5
  order_by: "created_at DESC"
```

### 6. `mysql_analyze_table_statistics` - 统计分析

**用途**: 分析表的统计数据（行数、空值、唯一值）

**常用参数**:
- `table`: 表名（必需）
- `include_column_stats`: 是否包含列统计（默认：是）

**示例**:
```yaml
mysql_analyze_table_statistics:
  table: "products"
```

### 7. `mysql_list_foreign_key_relationships` - 外键关系

**用途**: 查看表之间的外键关联关系

**常用参数**:
- `table`: 指定表名（可选，不指定则显示所有关系）
- `direction`:
  - `outgoing`: 该表引用的表
  - `incoming`: 引用该表的表
  - `both`: 两个方向（默认）

**示例**:
```yaml
mysql_list_foreign_key_relationships:
  table: "orders"
  direction: "both"
```

### 8. `mysql_execute_custom_query` - 自定义查询

**用途**: 执行自定义的SELECT查询

**常用参数**:
- `query`: SQL查询语句（必需，仅支持SELECT）
- `limit`: 最多返回行数（默认：100，最大：1000）

**示例**:
```yaml
mysql_execute_custom_query:
  query: "SELECT status, COUNT(*) as count FROM orders GROUP BY status"
```

## 输出格式

所有工具支持两种输出格式：

### Markdown（默认）
人类可读的格式，适合探索和理解。

### JSON
结构化的数据，适合程序处理。

**示例**:
```yaml
mysql_list_tables:
  response_format: "json"
```

## 常见问题

### Q: 如何连接到远程MySQL？
**A**: 修改环境变量中的 `MYSQL_HOST` 为远程服务器地址。

### Q: 支持MySQL 8.0吗？
**A**: 是的，支持MySQL 5.7及以上版本。

### Q: 可以修改数据库吗？
**A**: 不可以，所有工具都是只读的，确保数据安全。

### Q: 如何处理中文乱码？
**A**: 默认使用 `utf8mb4` 字符集，如需修改，在环境变量中设置 `MYSQL_CHARSET`。

## 下一步

1. 查看 [README.md](README.md) 了解详细文档
2. 查看 [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) 了解评估指南
3. 运行 `python mysql_mcp_server.py --help` 查看所有选项

## 技术支持

遇到问题？请检查：
1. 数据库连接信息是否正确
2. MySQL服务是否运行
3. 防火墙是否允许连接
4. 用户权限是否足够

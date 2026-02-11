# MySQL MCP Server 评估指南

## 概述

本评估用于测试 MySQL MCP Server 的功能完整性，确保 Agent 能够有效使用工具来理解数据库结构和业务形态。

## 评估问题说明

### 1. 数据库发现
**问题**: 列出当前MySQL服务器上所有的业务数据库（排除系统数据库）。
**期望能力**: 数据库发现和过滤
**工具**: `mysql_list_databases(include_system=False)`

### 2. 数据库概览
**问题**: 查看名为 'business_db' 的数据库有多少张表，总占用多少存储空间。
**期望能力**: 数据库元数据获取
**工具**: `mysql_database_overview(database="business_db")`

### 3. 表搜索
**问题**: 找出数据库中所有包含 'user' 或 'customer' 字样的表。
**期望能力**: 模式匹配和表列表查询
**工具**: `mysql_list_tables(table_pattern="%user%")` + `mysql_list_tables(table_pattern="%customer%")`

### 4. 表结构分析
**问题**: 查看 'orders' 表的完整结构，包括字段类型、是否允许为空、索引和外键。
**期望能力**: 详细的 Schema 分析
**工具**: `mysql_get_table_schema(table="orders")`

### 5. 数据采样
**问题**: 抽样查看 'users' 表的前10条数据，了解用户信息的存储格式。
**期望能力**: 数据内容探索
**工具**: `mysql_sample_table_data(table="users", limit=10)`

### 6. 统计分析
**问题**: 分析 'products' 表的统计数据，找出哪些字段有空值，以及各字段有多少不同的取值。
**期望能力**: 数据质量分析
**工具**: `mysql_analyze_table_statistics(table="products")`

### 7. 关系映射
**问题**: 查看 'orders' 表与哪些表有外键关联，理解订单表在业务中的关系。
**期望能力**: 数据模型理解
**工具**: `mysql_list_foreign_key_relationships(table="orders", direction="both")`

### 8. 业务统计
**问题**: 统计订单表中不同状态的订单数量（如待支付、已支付、已完成等）。
**期望能力**: 业务指标查询
**工具**: `mysql_execute_custom_query(query="SELECT status, COUNT(*) as count FROM orders GROUP BY status ORDER BY count DESC")`

### 9. 性能分析
**问题**: 找出数据库中数据量最大的前5张表。
**期望能力**: 性能热点识别
**工具**: `mysql_execute_custom_query(query="SELECT TABLE_NAME as table_name, TABLE_ROWS as rows, ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as size_mb FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_ROWS DESC LIMIT 5")`

### 10. 时序分析
**问题**: 查询最近一个月创建的用户数量及其地域分布。
**期望能力**: 时序数据分析
**工具**: `mysql_execute_custom_query(query="SELECT DATE(created_at) as date, COUNT(*) as new_users FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH) GROUP BY DATE(created_at) ORDER BY date")`

## 评估标准

### 通过标准
- 所有工具能够正确执行并返回预期数据
- 工具描述清晰，Agent 能够准确选择合适的工具
- 返回格式（Markdown/JSON）符合预期
- 错误处理完善，提供明确的错误信息

### 预期输出示例

#### 数据库列表 (Markdown)
```markdown
# Available Databases

Found 3 database(s)

## `business_db`
- **Charset**: utf8mb4
- **Collation**: utf8mb4_general_ci

## `analytics`
- **Charset**: utf8mb4
- **Collation**: utf8mb4_unicode_ci

## `reporting`
- **Charset**: utf8mb4
- **Collation**: utf8mb4_general_ci
```

#### 表结构 (Markdown)
```markdown
# Table Schema: `business_db`.`orders`

## Basic Information
- **Engine**: InnoDB
- **Rows**: 10,500
- **Size**: 45.23 MB
- **Comment**: Customer orders

## Columns
| Column | Type | Nullable | Key | Default | Extra | Comment |
|--------|------|----------|-----|---------|-------|---------|
| id | bigint | ✗ | PRI | NULL | auto_increment | |
| user_id | bigint | ✗ | MUL | NULL | | |
| status | varchar(20) | ✗ | MUL | 'pending' | | |
| total_amount | decimal(10,2) | ✗ | | 0.00 | | |
| created_at | datetime | ✗ | | CURRENT_TIMESTAMP | | |

## Foreign Keys
| Constraint | Column | References |
|------------|--------|------------|
| fk_orders_user | `user_id` | `users`.`id` |
```

## 测试方法

### 1. 使用 MCP Inspector
```bash
npx @modelcontextprotocol/inspector
```
然后连接到 `http://localhost:8000`。

### 2. 手动测试
启动服务器后，使用支持 MCP 的客户端进行测试。

### 3. 自动化测试
创建测试脚本，按顺序执行所有评估问题，验证返回结果。

## 典型业务理解流程

### 阶段1: 数据库发现
1. 列出所有数据库
2. 选择目标业务数据库
3. 查看数据库概览

### 阶段2: 表结构理解
4. 列出所有表
5. 识别核心业务表（如 users, orders, products）
6. 查看每张表的完整结构

### 阶段3: 数据关系分析
7. 查看外键关系，绘制数据模型
8. 理解表之间的关联方式

### 阶段4: 数据内容探索
9. 抽样查看核心表的数据
10. 分析数据分布和质量

### 阶段5: 业务指标分析
11. 统计关键业务指标
12. 分析时序数据和趋势

## 工具组合示例

### 理解用户系统
```
1. mysql_list_tables(table_pattern="%user%")
2. mysql_get_table_schema(table="users")
3. mysql_sample_table_data(table="users", limit=5)
4. mysql_analyze_table_statistics(table="users")
5. mysql_list_foreign_key_relationships(table="users")
```

### 理解订单系统
```
1. mysql_list_tables(table_pattern="%order%")
2. mysql_get_table_schema(table="orders")
3. mysql_sample_table_data(table="orders", limit=5)
4. mysql_analyze_table_statistics(table="orders")
5. mysql_list_foreign_key_relationships(table="orders", direction="both")
6. mysql_execute_custom_query(query="SELECT status, COUNT(*) as count FROM orders GROUP BY status")
```

## 常见问题

### Q: 如何快速了解一个未知数据库的业务形态？
**A**:
1. 使用 `mysql_list_tables` 查看所有表，识别业务实体
2. 使用 `mysql_list_foreign_key_relationships` 查看表关系，绘制ER图
3. 对核心表使用 `mysql_sample_table_data` 查看实际数据
4. 使用 `mysql_analyze_table_statistics` 分析数据分布

### Q: 如何找出业务中的核心表？
**A**:
1. 查看表大小：`mysql_execute_custom_query` 查询最大的表
2. 查看外键引用：被多个表引用的表通常是核心表
3. 查看表名：通常包含 business, core, main 等关键词

### Q: 如何分析数据质量问题？
**A**:
使用 `mysql_analyze_table_statistics` 工具，关注：
- 空值比例高的字段
- 唯一值数量异常的字段
- 数据类型不合理的字段

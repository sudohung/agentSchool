# MySQL MCP Server - 安装和测试检查清单

## 安装检查

### 1. 环境准备
- [ ] 已安装 Python 3.8 或更高版本
- [ ] 已安装 pip 包管理器
- [ ] 已安装 MySQL 服务器或可访问远程 MySQL

### 2. 安装依赖
```bash
pip install -r requirements.txt
```
验证：
- [ ] fastmcp 安装成功
- [ ] PyMySQL 安装成功
- [ ] pydantic 安装成功
- [ ] httpx 安装成功

### 3. 配置数据库连接
创建 `.env` 文件或设置环境变量：

```bash
# 复制示例文件
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# 编辑 .env 文件，填写实际配置
```

验证：
- [ ] MYSQL_HOST 设置正确
- [ ] MYSQL_PORT 设置正确（默认 3306）
- [ ] MYSQL_USER 设置正确
- [ ] MYSQL_PASSWORD 设置正确
- [ ] （可选）MYSQL_DATABASE 设置正确

### 4. 测试数据库连接
```bash
# 使用 Python 测试连接
python -c "import pymysql; conn = pymysql.connect(host='localhost', user='your_user', password='your_pass'); print('连接成功'); conn.close()"
```

验证：
- [ ] 数据库连接成功
- [ ] 用户有足够权限（SELECT, SHOW VIEW 等）

## 启动检查

### 1. 启动服务器
```bash
# Windows
start.bat

# 或直接运行
python mysql_mcp_server.py --transport streamable_http --port 8000
```

验证：
- [ ] 服务器启动成功，无错误信息
- [ ] 控制台显示 "Connected to MySQL: ..."
- [ ] 服务器监听在 `http://localhost:8000`

### 2. 验证服务端点
```bash
# 测试 HTTP 端点
curl http://localhost:8000

# 或使用浏览器访问
# http://localhost:8000
```

验证：
- [ ] 端点可访问
- [ ] 返回 MCP 协议的正确响应

## 功能测试

### 测试 1: 列出数据库
```bash
# 使用支持 MCP 的客户端连接
# 或使用 MCP Inspector
npx @modelcontextprotocol/inspector
```

调用工具：
```json
{
  "name": "mysql_list_databases",
  "arguments": {
    "include_system": false
  }
}
```

验证：
- [ ] 返回数据库列表
- [ ] 排除了系统数据库
- [ ] 格式正确（Markdown 或 JSON）

### 测试 2: 数据库概览
```json
{
  "name": "mysql_database_overview",
  "arguments": {
    "database": "your_database_name"
  }
}
```

验证：
- [ ] 返回数据库基本信息
- [ ] 显示表数量
- [ ] 显示数据库大小

### 测试 3: 列出表
```json
{
  "name": "mysql_list_tables",
  "arguments": {
    "database": "your_database_name",
    "limit": 10
  }
}
```

验证：
- [ ] 返回表列表
- [ ] 显示表大小和行数
- [ ] 格式正确

### 测试 4: 表结构
```json
{
  "name": "mysql_get_table_schema",
  "arguments": {
    "table": "your_table_name"
  }
}
```

验证：
- [ ] 返回表字段信息
- [ ] 显示索引信息
- [ ] 显示外键信息（如果有）

### 测试 5: 抽样数据
```json
{
  "name": "mysql_sample_table_data",
  "arguments": {
    "table": "your_table_name",
    "limit": 5
  }
}
```

验证：
- [ ] 返回表数据样本
- [ ] 数据格式正确
- [ ] 可以看到实际数据内容

### 测试 6: 统计分析
```json
{
  "name": "mysql_analyze_table_statistics",
  "arguments": {
    "table": "your_table_name"
  }
}
```

验证：
- [ ] 返回表统计信息
- [ ] 显示行数
- [ ] 显示列统计（空值、唯一值）

### 测试 7: 外键关系
```json
{
  "name": "mysql_list_foreign_key_relationships",
  "arguments": {
    "table": "your_table_name",
    "direction": "both"
  }
}
```

验证：
- [ ] 返回外键关系
- [ ] 显示引用表和被引用表
- [ ] 关系方向正确

### 测试 8: 自定义查询
```json
{
  "name": "mysql_execute_custom_query",
  "arguments": {
    "query": "SELECT COUNT(*) as count FROM your_table_name"
  }
}
```

验证：
- [ ] 查询执行成功
- [ ] 返回查询结果
- [ ] 只允许 SELECT 语句

## 评估测试

运行评估问题（见 `evaluation_questions.xml`）：

- [ ] 问题 1: 列出业务数据库 - 通过
- [ ] 问题 2: 数据库概览 - 通过
- [ ] 问题 3: 表搜索 - 通过
- [ ] 问题 4: 表结构分析 - 通过
- [ ] 问题 5: 数据采样 - 通过
- [ ] 问题 6: 统计分析 - 通过
- [ ] 问题 7: 关系映射 - 通过
- [ ] 问题 8: 业务统计 - 通过
- [ ] 问题 9: 性能分析 - 通过
- [ ] 问题 10: 时序分析 - 通过

## 常见问题排查

### 问题 1: 无法连接数据库
**症状**: 启动时出现连接错误

**解决**:
1. 检查 MySQL 服务是否运行
2. 检查连接参数是否正确
3. 检查防火墙设置
4. 测试使用 MySQL 客户端能否连接

### 问题 2: 权限不足
**症状**: 工具执行失败，提示权限错误

**解决**:
1. 确保用户有以下权限：
   - SELECT
   - SHOW VIEW
   - INFORMATION_SCHEMA 访问权限
2. 联系数据库管理员授予必要权限

### 问题 3: 中文乱码
**症状**: 返回的中文显示为乱码

**解决**:
1. 确保设置 `MYSQL_CHARSET=utf8mb4`
2. 检查数据库和表的字符集设置

### 问题 4: 工具返回空结果
**症状**: 工具执行成功但返回空数据

**解决**:
1. 检查数据库中是否有数据
2. 检查过滤条件是否正确
3. 查看日志获取更多信息

### 问题 5: 服务器无法启动
**症状**: 启动脚本报错

**解决**:
1. 检查 Python 版本（需要 3.8+）
2. 重新安装依赖：`pip install -r requirements.txt --force-reinstall`
3. 检查端口 8000 是否被占用

## 性能优化建议

- [ ] 对于大型数据库，使用 `limit` 参数限制返回结果
- [ ] 使用 `table_pattern` 过滤不需要的表
- [ ] 避免在高峰期执行大量统计查询
- [ ] 考虑使用数据库只读副本进行分析

## 安全检查

- [ ] 使用专用的只读数据库用户
- [ ] 限制数据库用户的权限
- [ ] 不要在生产环境使用 root 用户
- [ ] 定期检查和更新密码
- [ ] 使用防火墙限制访问

## 完成

如果所有检查项都通过，恭喜！MySQL MCP Server 已成功安装和配置。

如有问题，请查看：
- [README.md](README.md) - 详细文档
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) - 评估指南

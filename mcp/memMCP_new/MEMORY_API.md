# Memory MCP HTTP API

独立的 HTTP 接口，用于直接查询和管理 Memory MCP Server 中存储的记忆内容，无需通过复杂的 MCP 协议。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install fastapi uvicorn python-dotenv
```

### 2. 启动 API 服务器
```bash
# 使用默认设置 (端口 8325)
python memory_api.py

# 自定义主机和端口
python memory_api.py --host 0.0.0.0 --port 8325

# 开发模式（自动重载）
python memory_api.py --reload
```

### 3. 访问 API 文档
打开浏览器访问 `http://localhost:8325/docs` 查看交互式 API 文档。

## 📋 API 端点

### 🔍 **查询记忆**

#### 列出所有记忆
```bash
# 获取前10条记忆
curl http://localhost:8325/memories

# 分页获取 (跳过前10条，获取接下来的20条)
curl "http://localhost:8325/memories?limit=20&offset=10"
```

#### 搜索记忆
```bash
# 搜索包含"用户偏好"的记忆
curl "http://localhost:8325/memories/search?query=用户偏好&limit=5"
```

#### 获取特定记忆
```bash
# 获取 ID 为 42 的记忆
curl http://localhost:8325/memories/42
```

### 🗑️ **删除记忆**

#### 删除特定记忆
```bash
# 删除 ID 为 42 的记忆
curl -X DELETE http://localhost:8325/memories/42
```

#### 删除所有记忆
```bash
# ⚠️ 警告：此操作不可逆！
curl -X DELETE http://localhost:8325/memories
```

### ➕ **存储记忆**（测试用）
```bash
# 存储新记忆（主要用于测试）
curl -X POST http://localhost:8325/memories \
  -H "Content-Type: application/json" \
  -d '{
    "content": "测试记忆内容",
    "metadata": {"category": "test", "source": "api"}
  }'
```

### 📊 **统计信息**
```bash
# 获取数据库统计信息
curl http://localhost:8325/stats

# 健康检查
curl http://localhost:8325/
```

## 🔧 配置选项

### 环境变量
在 `.env` 文件中配置：

```env
# SQLite 数据库路径（必须与 Memory MCP Server 相同）
MEMORY_DB_PATH=memory.db

# 其他 Memory MCP 配置（由主服务器使用）
MEMORY_MAX_SIZE=10000
MEMORY_ENABLE_FTS=true
```

### 命令行参数
```bash
--host          # 绑定的主机地址 (默认: 127.0.0.1)
--port          # 监听端口 (默认: 8325)
--reload        # 开发模式自动重载
```

## 💡 使用场景

### 1. **调试和监控**
- 快速查看当前存储的所有记忆
- 验证记忆存储是否正常工作
- 监控数据库大小和性能

### 2. **数据管理**
- 批量清理过时的记忆
- 导出记忆数据进行备份
- 手动修复或更新记忆内容

### 3. **集成测试**
- 在不启动完整 MCP 客户端的情况下测试记忆功能
- 自动化测试脚本集成
- CI/CD 流程中的数据验证

### 4. **管理界面**
- 为 Web 管理界面提供后端 API
- 构建记忆管理仪表板
- 实现记忆搜索和过滤功能

## 🔒 安全考虑

### 开发环境
- 默认允许所有 CORS 请求（`allow_origins=["*"]`）
- 无身份验证（假设在受信任的本地环境中运行）

### 生产环境
**重要**: 在生产环境中部署时，请修改以下安全设置：

```python
# 限制 CORS 来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 替换为实际域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# 添加身份验证中间件
# 实现 API 密钥或 JWT 认证
```

## 📈 性能特点

- **轻量级**: 单文件实现，最小依赖
- **高效**: 直接 SQLite 查询，无额外开销  
- **并发安全**: 每个请求使用独立数据库连接
- **内存友好**: 流式处理，支持大数据集分页

## 🛠️ 故障排除

### 常见问题

**Q: 无法连接到数据库？**  
A: 确保 `MEMORY_DB_PATH` 指向正确的 SQLite 文件，且文件存在。

**Q: 搜索功能不工作？**  
A: 确认 Memory MCP Server 启用了 FTS5 (`MEMORY_ENABLE_FTS=true`)。

**Q: API 返回 500 错误？**  
A: 检查服务器日志，通常是因为数据库文件权限或路径问题。

**Q: 如何重置所有记忆？**  
A: 使用 `DELETE /memories` 端点，或直接删除 `memory.db` 文件。

## 🎯 最佳实践

1. **共享数据库**: 确保 HTTP API 和 Memory MCP Server 使用相同的 `MEMORY_DB_PATH`
2. **合理分页**: 大量数据时使用 `limit` 和 `offset` 参数
3. **定期备份**: 定期备份 `memory.db` 文件
4. **监控大小**: 使用 `/stats` 端点监控数据库增长
5. **安全部署**: 生产环境务必添加身份验证和访问控制

---

这个独立的 HTTP API 为 Memory MCP Server 提供了简单、直观的数据管理能力，让您可以轻松地查询、删除和管理长期记忆内容。
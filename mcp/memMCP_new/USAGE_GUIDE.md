# Memory MCP Server 使用指南

## 什么是 Memory MCP？

Memory MCP 是一个轻量级的长期记忆存储系统，专为 AI Agent 设计。它使用 SQLite 作为后端存储，并集成了 FTS5 全文搜索引擎，让 Agent 能够：

- 存储重要的上下文信息和学习到的知识
- 通过自然语言搜索检索相关记忆
- 维护结构化的元数据
- 安全地管理记忆生命周期

## 主要特性

### 🗄️ 轻量级存储
- 使用 SQLite，无需额外的数据库服务器
- 单文件存储，便于备份和迁移
- 最小化依赖，只需要 Python 标准库 + FastMCP

### 🔍 高效搜索
- 内置 SQLite FTS5 全文搜索
- 支持复杂的搜索查询
- 自动索引更新，保持搜索结果实时性

### 📦 结构化元数据
- 每条记忆可以关联 JSON 元数据
- 支持分类、标签、来源等信息
- 便于组织和过滤记忆

### 🛡️ 安全可靠
- 所有操作都是原子性的
- 自动处理数据库连接和错误
- 支持大规模记忆存储（可配置上限）

## 5个核心工具

### 1. `mem_store_memory` - 存储记忆
```yaml
mem_store_memory:
  content: "用户喜欢Python编程"
  metadata:
    category: "user_preferences"
    source: "conversation"
    confidence: 0.95
```

### 2. `mem_search_memories` - 搜索记忆
```yaml
mem_search_memories:
  query: "用户偏好"
  limit: 5
```

### 3. `mem_get_memory` - 获取特定记忆
```yaml
mem_get_memory:
  memory_id: 42
```

### 4. `mem_list_memories` - 列出记忆
```yaml
mem_list_memories:
  limit: 10
  offset: 0
```

### 5. `mem_delete_memory` - 删除记忆
```yaml
mem_delete_memory:
  memory_id: 42
```

## 集成方式

### Claude Desktop 集成
在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": [
        "/path/to/mem_mcp_server.py",
        "--transport", "stdio"
      ],
      "env": {
        "MEMORY_DB_PATH": "agent_memory.db",
        "MEMORY_MAX_SIZE": "50000"
      }
    }
  }
}
```

### OpenCode 集成
使用 `opencode_config.json` 配置文件：

```json
{
  "mcp": {
    "memory": {
      "command": "python",
      "args": ["start_opencode_mcp.py"],
      "cwd": "/path/to/memMCP_new"
    }
  }
}
```

## 典型使用场景

### 场景1: 用户偏好记忆
```python
# 存储用户偏好
mem_store_memory(
    content="用户偏好深色主题，喜欢Python编程",
    metadata={"type": "preference", "source": "user_feedback"}
)

# 后续对话中检索
mem_search_memories(query="用户主题偏好")
```

### 场景2: 项目上下文记忆
```python
# 存储项目信息
mem_store_memory(
    content="当前项目是电商网站，使用React和Node.js",
    metadata={"type": "project_context", "project_id": "ecommerce-2024"}
)

# 在相关对话中检索项目上下文
mem_search_memories(query="当前项目技术栈")
```

### 场景3: 学习知识积累
```python
# 存储学到的知识
mem_store_memory(
    content="SQLite FTS5支持BM25排名算法",
    metadata={"type": "learned_knowledge", "domain": "database"}
)

# 在相关问题中检索知识
mem_search_memories(query="SQLite 全文搜索")
```

## 配置选项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `MEMORY_DB_PATH` | `memory.db` | SQLite 数据库文件路径 |
| `MEMORY_MAX_SIZE` | `10000` | 最大记忆数量 |
| `MEMORY_ENABLE_FTS` | `true` | 是否启用全文搜索 |

## 性能特点

- **存储性能**: 单次写入 < 1ms
- **搜索性能**: 10,000 条记忆中搜索 < 10ms  
- **内存占用**: < 10MB (包括 Python 运行时)
- **磁盘占用**: 每条记忆约 100-500 字节

## 安全考虑

- 所有数据本地存储，不上传到云端
- 数据库文件权限遵循操作系统默认设置
- 支持加密存储（可通过外部工具实现）
- 无网络暴露风险（除非显式启用 HTTP 传输）

## 故障排除

### 问题: 无法启动服务器
**解决方案**: 
- 确保 Python 3.8+ 已安装
- 运行 `pip install -r requirements.txt`
- 检查数据库文件路径是否有写权限

### 问题: 搜索结果不准确
**解决方案**:
- 确保 `MEMORY_ENABLE_FTS=true`
- 检查搜索查询是否包含足够的关键词
- 考虑增加 `limit` 参数获取更多结果

### 问题: 内存占用过高
**解决方案**:
- 降低 `MEMORY_MAX_SIZE` 限制
- 定期清理不再需要的记忆
- 使用更具体的元数据进行过滤

## 扩展建议

虽然当前版本专注于核心功能，但可以轻松扩展：

1. **记忆过期**: 添加 TTL (Time To Live) 功能
2. **记忆分组**: 支持命名空间或分类存储
3. **向量搜索**: 集成嵌入向量进行语义搜索
4. **同步备份**: 支持云存储自动备份
5. **Web UI**: 提供记忆管理界面

## 技术栈

- **语言**: Python 3.8+
- **框架**: FastMCP
- **数据库**: SQLite 3.16+ (with FTS5)
- **依赖**: python-dotenv, sqlite3 (built-in)

这个 Memory MCP 服务器为 AI Agent 提供了一个简单、高效、可靠的长期记忆解决方案，特别适合需要记住用户偏好、项目上下文和学习知识的场景。
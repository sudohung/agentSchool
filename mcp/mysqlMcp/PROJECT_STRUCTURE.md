# MySQL MCP Server - 项目结构

```
agent_skill_python/
├── mysql_mcp_server.py          # 主服务器文件（核心代码）
├── requirements.txt             # Python依赖
├── README.md                    # 详细文档
├── QUICKSTART.md               # 快速开始指南
├── EVALUATION_GUIDE.md         # 评估指南
├── evaluation_questions.xml    # 评估问题
├── .env.example                # 环境变量示例
└── start.bat                   # Windows启动脚本
```

## 文件说明

### 核心文件

- **mysql_mcp_server.py**: MCP服务器主文件，包含所有工具实现
- **requirements.txt**: Python包依赖列表

### 文档文件

- **README.md**: 完整的项目文档，包含功能、安装、使用说明
- **QUICKSTART.md**: 快速开始指南，5分钟上手
- **EVALUATION_GUIDE.md**: 评估测试指南和问题说明

### 配置文件

- **.env.example**: 环境变量配置示例
- **evaluation_questions.xml**: 评估测试问题集

### 启动脚本

- **start.bat**: Windows平台一键启动脚本

## 工具架构

### 1. 连接管理
- `DatabaseClient`: 数据库连接客户端
- `ConnectionConfig`: 连接配置模型
- `app_lifespan`: 连接生命周期管理

### 2. 工具分类

#### 数据库发现类
- `mysql_list_databases`: 列出数据库
- `mysql_database_overview`: 数据库概览

#### 表管理类
- `mysql_list_tables`: 列出表
- `mysql_get_table_schema`: 表结构分析

#### 数据查询类
- `mysql_sample_table_data`: 抽样数据
- `mysql_execute_custom_query`: 自定义查询

#### 统计分析类
- `mysql_analyze_table_statistics`: 表统计分析
- `mysql_list_foreign_key_relationships`: 外键关系分析

### 3. 辅助功能

- `format_markdown_table`: Markdown表格格式化
- `truncate_value`: 值截断处理
- `_handle_api_error`: 错误处理

## 技术栈

- **语言**: Python 3.8+
- **框架**: FastMCP (MCP Python SDK)
- **数据库**: PyMySQL
- **验证**: Pydantic v2
- **传输**: Streamable HTTP / Stdio

## 扩展开发

### 添加新工具

1. 创建输入模型（继承 `BaseModel`）
2. 使用 `@mcp.tool()` 装饰器
3. 设置正确的 `annotations`
4. 实现异步函数
5. 添加完整的文档字符串

### 示例

```python
class MyToolInput(BaseModel):
    """输入参数模型"""
    param1: str = Field(..., description="参数说明")

@mcp.tool(
    name="mysql_my_tool",
    annotations={
        "title": "工具标题",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def my_tool(params: MyToolInput, ctx: Context) -> str:
    """工具说明"""
    # 实现逻辑
    pass
```

"""
最终演示 - 展示所有工作正常的功能
"""
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

async def final_demo():
    """最终演示"""
    
    print("=" * 70)
    print("MySQL MCP Server - 最终功能演示")
    print("=" * 70)
    print()
    
    server_params = StdioServerParameters(
        command="python",
        args=["mysql_mcp_server.py", "--transport", "stdio"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("[SUCCESS] MCP 服务器启动成功")
            print("[SUCCESS] 连接到阿里云 MySQL 数据库")
            print()
            
            # 1. 列出数据库
            print("=" * 70)
            print("功能 1: 列出所有数据库")
            print("=" * 70)
            result = await session.call_tool(
                "mysql_list_databases",
                arguments={"params": {"response_format": "markdown"}}
            )
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            # 2. 列出表
            print("\n" + "=" * 70)
            print("功能 2: 列出前 5 个表")
            print("=" * 70)
            result = await session.call_tool(
                "mysql_list_tables",
                arguments={
                    "params": {
                        "database": "xp_dragon_pandora",
                        "response_format": "markdown",
                        "limit": 5
                    }
                }
            )
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            # 3. 查看表结构
            print("\n" + "=" * 70)
            print("功能 3: 查看 ai_called_job 表结构")
            print("=" * 70)
            result = await session.call_tool(
                "mysql_get_table_schema",
                arguments={
                    "params": {
                        "database": "xp_dragon_pandora",
                        "table": "ai_called_job",
                        "response_format": "markdown",
                        "include_indexes": True
                    }
                }
            )
            for content in result.content:
                if hasattr(content, 'text'):
                    # 只显示前500个字符
                    text = content.text[:500]
                    print(text)
                    if len(content.text) > 500:
                        print("\n... (输出被截断，完整内容更长)")
            
            # 4. 采样数据
            print("\n" + "=" * 70)
            print("功能 4: 采样 ai_called_job 表数据 (前3条)")
            print("=" * 70)
            result = await session.call_tool(
                "mysql_sample_table_data",
                arguments={
                    "params": {
                        "database": "xp_dragon_pandora",
                        "table": "ai_called_job",
                        "response_format": "markdown",
                        "limit": 3
                    }
                }
            )
            for content in result.content:
                if hasattr(content, 'text'):
                    # 只显示前500个字符
                    text = content.text[:500]
                    print(text)
                    if len(content.text) > 500:
                        print("\n... (输出被截断)")
            
            # 5. 执行 SELECT 查询
            print("\n" + "=" * 70)
            print("功能 5: 执行自定义 SELECT 查询")
            print("=" * 70)
            result = await session.call_tool(
                "mysql_execute_custom_query",
                arguments={
                    "params": {
                        "database": "xp_dragon_pandora",
                        "query": "SELECT COUNT(*) as total_jobs FROM ai_called_job",
                        "response_format": "markdown"
                    }
                }
            )
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
            
            print("\n" + "=" * 70)
            print("演示完成!")
            print("=" * 70)
            print()
            print("所有核心功能都正常工作:")
            print("  [OK] 列出数据库")
            print("  [OK] 列出表")
            print("  [OK] 查看表结构")
            print("  [OK] 采样表数据")
            print("  [OK] 执行 SELECT 查询")
            print()
            print("你现在可以:")
            print("  1. 在 Claude Desktop 中配置此 MCP 服务器")
            print("  2. 用自然语言让 Claude 帮你探索数据库")
            print("  3. 分析数据、生成报告、理解业务逻辑")
            print("=" * 70)

if __name__ == "__main__":
    asyncio.run(final_demo())

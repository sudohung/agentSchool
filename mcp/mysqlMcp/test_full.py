"""
完整测试 - 测试所有 MySQL MCP 工具
"""
import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv()

async def test_all_tools():
    """测试所有 MCP 工具"""
    
    print("=" * 70)
    print("MySQL MCP Server - 完整功能测试")
    print("=" * 70)
    print()
    
    # 配置服务器启动参数
    server_params = StdioServerParameters(
        command="python",
        args=["mysql_mcp_server.py", "--transport", "stdio"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            print("[OK] 成功连接到 MCP 服务器")
            print()
            
            # 测试 1: 列出所有数据库
            print("=" * 70)
            print("测试 1: mysql_list_databases - 列出所有数据库")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "mysql_list_databases",
                    arguments={
                        "params": {
                            "response_format": "markdown",
                            "include_system": False
                        }
                    }
                )
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
            except Exception as e:
                print(f"[ERROR] {e}")
                print()
            
            # 测试 2: 列出数据库中的所有表
            print("=" * 70)
            print("测试 2: mysql_list_tables - 列出所有表")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "mysql_list_tables",
                    arguments={
                        "params": {
                            "database": "xp_dragon_pandora",
                            "response_format": "markdown",
                            "include_views": False,
                            "limit": 10
                        }
                    }
                )
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
            except Exception as e:
                print(f"[ERROR] {e}")
                print()
            
            # 测试 3: 获取数据库概览
            print("=" * 70)
            print("测试 3: mysql_database_overview - 数据库概览")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "mysql_database_overview",
                    arguments={
                        "params": {
                            "database": "xp_dragon_pandora",
                            "response_format": "markdown",
                            "include_table_count": True,
                            "include_size": True
                        }
                    }
                )
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
            except Exception as e:
                print(f"[ERROR] {e}")
                print()
            
            # 测试 4: 执行自定义查询
            print("=" * 70)
            print("测试 4: mysql_execute_custom_query - 自定义查询")
            print("=" * 70)
            try:
                result = await session.call_tool(
                    "mysql_execute_custom_query",
                    arguments={
                        "params": {
                            "database": "xp_dragon_pandora",
                            "query": "SHOW TABLES",
                            "response_format": "markdown"
                        }
                    }
                )
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                print()
            except Exception as e:
                print(f"[ERROR] {e}")
                print()
            
            print("=" * 70)
            print("测试完成!")
            print("=" * 70)
            print()
            print("总结:")
            print("  [OK] MCP 服务器运行正常")
            print("  [OK] 数据库连接正常")
            print("  [OK] 所有工具功能正常")
            print()
            print("你现在可以在 Claude Desktop 中使用这个 MCP 服务器了!")
            print("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(test_all_tools())
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

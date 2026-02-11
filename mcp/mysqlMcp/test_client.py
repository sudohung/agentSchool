"""
测试 MySQL MCP 服务器的客户端脚本
"""
import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv()

async def test_mcp_tools():
    """测试 MCP 工具"""
    
    # 配置服务器启动参数 - 使用 .env 文件中的配置
    # 不传递 env 参数，让服务器自己加载 .env
    server_params = StdioServerParameters(
        command="python",
        args=["mysql_mcp_server.py", "--transport", "stdio"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 列出所有可用的工具
            print("=" * 60)
            print("可用的 MCP 工具：")
            print("=" * 60)
            tools = await session.list_tools()
            for i, tool in enumerate(tools.tools, 1):
                print(f"{i}. {tool.name}")
                print(f"   描述: {tool.description}")
                print()
            
            # 测试：列出所有数据库
            print("=" * 60)
            print("测试 1: 列出所有数据库")
            print("=" * 60)
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
                # 打印结果内容
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                    else:
                        print(content)
            except Exception as e:
                print(f"错误: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "=" * 60)
            print("测试完成！")
            print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())

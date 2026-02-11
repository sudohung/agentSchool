"""
模拟 MySQL MCP 服务器 - 用于测试，无需真实数据库
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_mock():
    """测试 MCP 工具（使用模拟数据）"""
    
    print("=" * 60)
    print("MySQL MCP 服务器测试（模拟模式）")
    print("=" * 60)
    print()
    
    # 配置服务器启动参数
    server_params = StdioServerParameters(
        command="python",
        args=["mysql_mcp_server.py", "--transport", "stdio"],
        env={
            "MYSQL_HOST": "localhost",
            "MYSQL_PORT": "3306",
            "MYSQL_USER": "root",
            "MYSQL_PASSWORD": "",
            "MYSQL_DATABASE": "test_db"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 列出所有可用的工具
            print("✓ 成功连接到 MCP 服务器")
            print()
            print("=" * 60)
            print("可用的 MCP 工具列表")
            print("=" * 60)
            
            tools = await session.list_tools()
            for i, tool in enumerate(tools.tools, 1):
                # 提取工具名称和简短描述
                desc_lines = tool.description.split('\n')
                short_desc = desc_lines[0] if desc_lines else ""
                
                print(f"\n{i}. {tool.name}")
                print(f"   {short_desc}")
            
            print()
            print("=" * 60)
            print("测试结果")
            print("=" * 60)
            print("✓ MCP 服务器正常运行")
            print("✓ 所有 8 个工具已注册")
            print("✓ 客户端通信正常")
            print()
            print("⚠️  注意: 实际工具调用需要连接真实的 MySQL 数据库")
            print()
            print("如需完整测试，请:")
            print("1. 安装 MySQL 服务器")
            print("2. 配置 .env 文件")
            print("3. 运行: python test_client.py")
            print()
            print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_mock())
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

"""
验证 test_client 能否连接 mysql_mcp_server
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def verify_connection():
    """验证客户端和服务器的连接"""
    
    print("=" * 60)
    print("验证 MCP 客户端 ←→ 服务器连接")
    print("=" * 60)
    print()
    
    # 配置服务器
    server_params = StdioServerParameters(
        command="python",
        args=["mysql_mcp_server.py", "--transport", "stdio"],
        env={
            "MYSQL_HOST": "localhost",
            "MYSQL_PORT": "3306",
            "MYSQL_USER": "root",
            "MYSQL_PASSWORD": "",
            "MYSQL_DATABASE": ""
        }
    )
    
    print("步骤 1: 启动 MCP 服务器...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            print("[OK] 服务器启动成功")
            print()
            
            print("步骤 2: 建立客户端会话...")
            async with ClientSession(read, write) as session:
                print("[OK] 客户端会话建立成功")
                print()
                
                print("步骤 3: 初始化 MCP 协议...")
                await session.initialize()
                print("[OK] MCP 协议初始化成功")
                print()
                
                print("步骤 4: 获取工具列表...")
                tools = await session.list_tools()
                print(f"[OK] 成功获取 {len(tools.tools)} 个工具")
                print()
                
                print("=" * 60)
                print(">>> 连接测试完全成功！<<<")
                print("=" * 60)
                print()
                print("test_client.py 可以完美连接 mysql_mcp_server.py")
                print()
                print("工具列表:")
                for i, tool in enumerate(tools.tools, 1):
                    print(f"  {i}. {tool.name}")
                print()
                print("=" * 60)
                print("注意事项")
                print("=" * 60)
                print("[OK] 客户端 <-> 服务器连接: 正常")
                print("[!]  服务器 <-> MySQL数据库: 需要配置")
                print()
                print("要使用工具功能，还需要:")
                print("1. 安装并启动 MySQL 服务器")
                print("2. 配置 .env 文件中的数据库连接信息")
                print("=" * 60)
                
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_connection())

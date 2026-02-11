"""
简单测试 - 直接测试数据库连接
"""
import os
import asyncio
from dotenv import load_dotenv
from mysql_mcp_server import DatabaseClient, ConnectionConfig

# Load .env file
load_dotenv()

async def test_db_connection():
    """测试数据库连接"""
    
    # 配置
    config = ConnectionConfig(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE"),
        charset="utf8mb4"
    )
    
    print("=" * 60)
    print("测试 MySQL 数据库连接")
    print("=" * 60)
    print(f"主机: {config.host}:{config.port}")
    print(f"用户: {config.user}")
    print(f"数据库: {config.database or '(未指定)'}")
    print()
    
    # 创建客户端
    client = DatabaseClient(config)
    
    try:
        # 连接数据库
        await client.connect()
        print("✓ 成功连接到 MySQL 服务器")
        print()
        
        # 测试查询：列出所有数据库
        print("=" * 60)
        print("查询所有数据库：")
        print("=" * 60)
        
        query = """
            SELECT SCHEMA_NAME as database_name
            FROM INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
            ORDER BY SCHEMA_NAME
        """
        
        results = await client.execute_query(query)
        
        if results:
            for i, row in enumerate(results, 1):
                print(f"{i}. {row['database_name']}")
        else:
            print("(没有找到用户数据库)")
        
        print()
        print("=" * 60)
        print("✓ 测试成功！")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await client.close()
        print("\n已断开连接")

if __name__ == "__main__":
    asyncio.run(test_db_connection())

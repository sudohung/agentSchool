"""简化的 SSE 真实测试."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.opencode_integration import OpenCodeIntegration


async def test_simple_sse_listen(opencode_url: str):
    """简单测试 SSE 监听"""
    
    print("="*70)
    print("SSE 简单测试")
    print("="*70)
    print(f"OpenCode Server: {opencode_url}\n")
    
    # 连接
    opencode = OpenCodeIntegration(base_url=opencode_url)
    connected = await opencode.connect()
    
    if not connected:
        print("❌ 连接失败")
        return
    
    print(f"✅ 已连接 OpenCode v{opencode.client.health_check().version}")
    
    # 创建会话
    session = await opencode.create_session("Test Session")
    print(f"✅ 会话：{session.id}")
    
    # 尝试订阅事件
    print("\n尝试订阅事件...")
    
    try:
        # 检查 event API
        if hasattr(opencode.client, 'event'):
            print(f"✅ Event API 可用")
            
            # 检查 subscribe 方法
            if hasattr(opencode.client.event, 'subscribe'):
                print(f"✅ subscribe 方法可用")
                
                # 尝试调用（同步）
                result = opencode.client.event.subscribe()
                print(f"返回类型：{type(result)}")
                
                # 尝试迭代
                print("\n开始监听事件（10 秒）...")
                import time
                start = time.time()
                
                count = 0
                while time.time() - start < 10:
                    try:
                        event = next(result)
                        count += 1
                        print(f"\n📨 事件 {count}: {type(event).__name__}")
                        if hasattr(event, 'model_dump'):
                            print(f"   数据：{event.model_dump()}")
                    except StopIteration:
                        break
                    except Exception as e:
                        print(f"迭代错误：{e}")
                        break
                
                print(f"\n共接收 {count} 个事件")
                
            else:
                print("❌ subscribe 方法不可用")
        else:
            print("❌ Event API 不可用")
    
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await opencode.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://10.184.16.105:52590")
    args = parser.parse_args()
    
    asyncio.run(test_simple_sse_listen(args.url))

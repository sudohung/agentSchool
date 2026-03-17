"""SSE 事件真实测试 - 连接真实 OpenCode.

测试流程：
1. 连接真实 OpenCode Server
2. 创建会话
3. 启动 SSE 事件监听
4. 用户在 OpenCode 中触发 question/permission 事件
5. 验证系统接收并处理事件
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from event.manager import SSEEventManager
from agent.roles.decision import DecisionAgent
from agent.opencode_integration import OpenCodeIntegration


async def test_real_sse_connection(opencode_url: str):
    """测试真实 SSE 连接和事件处理"""
    
    print("="*70)
    print("SSE 事件真实测试")
    print("="*70)
    print(f"\nOpenCode Server: {opencode_url}")
    print("\n测试步骤：")
    print("1. 连接 OpenCode Server")
    print("2. 创建会话")
    print("3. 启动 SSE 事件监听")
    print("4. 请在 OpenCode 中触发以下事件之一：")
    print("   - 执行需要权限的命令 (触发 permission_asked)")
    print("   - 提问需要回答的问题 (触发 question_asked)")
    print("\n等待事件触发...\n")
    print("-"*70)
    
    # 1. 连接 OpenCode
    opencode = OpenCodeIntegration(base_url=opencode_url)
    
    try:
        connected = await opencode.connect()
        if not connected:
            print("❌ 连接 OpenCode 失败")
            return
        
        print("✅ 已连接 OpenCode Server")
        
        # 2. 创建会话
        session = await opencode.create_session("SSE Event Test Session")
        if not session:
            print("❌ 创建会话失败")
            return
        
        print(f"✅ 已创建会话：{session.id}")
        
        # 3. 创建决策 Agent
        decision_agent = DecisionAgent(
            session=session,
            client=opencode.client,
        )
        print("✅ 决策 Agent 已创建")
        
        # 4. 创建 SSE 事件管理器
        manager = SSEEventManager(
            opencode_client=opencode.client,
            session_id=session.id,
            decision_agent=decision_agent,
        )
        print("✅ SSE 事件管理器已创建")
        
        # 5. 启动事件监听
        await manager.start()
        print("✅ SSE 事件监听已启动")
        print("\n" + "="*70)
        print("👂 正在监听事件... (按 Ctrl+C 停止)")
        print("="*70 + "\n")
        
        # 6. 持续监听（最长 5 分钟）
        try:
            start_time = asyncio.get_event_loop().time()
            timeout = 300  # 5 分钟
            
            while True:
                await asyncio.sleep(1)
                
                # 显示统计
                stats = manager.get_statistics()
                elapsed = int(asyncio.get_event_loop().time() - start_time)
                
                if stats["events_received"] > 0:
                    print(f"\n📊 事件统计 ({elapsed}s):")
                    print(f"   接收：{stats['events_received']}")
                    print(f"   处理：{stats['events_processed']}")
                    print(f"   问题：{stats['questions_answered']}")
                    print(f"   权限：{stats['permissions_handled']}")
                
                # 超时检查
                if elapsed > timeout:
                    print(f"\n⏰ 测试超时 ({timeout}s)")
                    break
        
        except KeyboardInterrupt:
            print("\n\n🛑 用户中断")
        
        # 7. 停止监听
        await manager.stop()
        print("\n✅ SSE 事件监听已停止")
        
        # 8. 最终统计
        print("\n" + "="*70)
        print("最终统计")
        print("="*70)
        stats = manager.get_statistics()
        print(f"接收事件数：{stats['events_received']}")
        print(f"处理事件数：{stats['events_processed']}")
        print(f"回答问题数：{stats['questions_answered']}")
        print(f"处理权限数：{stats['permissions_handled']}")
        
        # 决策历史
        decisions = decision_agent.get_decision_history()
        if decisions:
            print(f"\n决策历史 ({len(decisions)} 条):")
            for d in decisions[-5:]:  # 显示最后 5 条
                print(f"  - [{d['type']}] {d['output']}")
        
        print("\n" + "="*70)
        print("测试完成")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 断开连接
        await opencode.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SSE 事件真实测试")
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:4096",
        help="OpenCode Server 地址 (默认：http://localhost:4096)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(test_real_sse_connection(args.url))
    except KeyboardInterrupt:
        print("\n👋 再见")

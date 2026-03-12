"""OpenCode SDK 集成测试."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 60)
print("OpenCode SDK 集成测试")
print("=" * 60)
print()

# 1. SDK 导入
print("【1】SDK 导入测试")
from opencode_4_py import OpenCodeClient, ClientConfig
print("    ✓ OpenCodeClient")
print("    ✓ ClientConfig")
print()

# 2. 配置
BASE_URL = "http://172.22.221.176:4096"

# 3. SDK 连接测试
print("【2】SDK 连接测试")
config = ClientConfig(base_url=BASE_URL)
client = OpenCodeClient(config)
health = client.health_check()
print(f"    ✓ Server version: {health.version}")
print(f"    ✓ Server healthy: {health.healthy}")
print()

# 4. 会话管理测试
print("【3】会话管理测试")
session = client.session.create(title="集成测试会话")
print(f"    ✓ Session created: {session.id}")
print()

# 5. 消息发送测试
print("【4】消息发送测试")
try:
    result = client.message.send_text(
        session_id=session.id,
        text="用一句话介绍你的能力",
    )
    print(f"    ✓ Response received")
    print(f"    ✓ Parts count: {len(result.parts)}")
    for part in result.parts:
        if part.type == "text":
            print(f"      - text: {part.text[:60]}...")
        elif part.type == "reasoning":
            print(f"      - reasoning: {part.text[:60]}...")
except Exception as e:
    print(f"    ✗ Error: {e}")
print()

# 6. OpenCodeIntegration 集成测试
print("【5】OpenCodeIntegration 集成测试")
from agent.opencode_integration import OpenCodeIntegration

import asyncio


async def test_integration():
    opencode = OpenCodeIntegration(base_url=BASE_URL)

    # 连接
    connected = await opencode.connect()
    print(f"    ✓ Connect: {connected}")

    if connected:
        # 创建会话
        sess = await opencode.create_session("Integration Test")
        print(f"    ✓ Create session: {sess.id if sess else 'Failed'}")

        if sess:
            # 发送消息
            msg_result = await opencode.send_message("build", "你好")
            if msg_result:
                print(f"    ✓ Send message: Success")
                print(f"      Parts: {len(msg_result.parts)}")
            else:
                print(f"    ✗ Send message: Failed")

        # 断开
        await opencode.disconnect()
        print(f"    ✓ Disconnect")


asyncio.run(test_integration())

print()
print("=" * 60)
print("测试完成")
print("=" * 60)

# 关闭客户端
client.close()

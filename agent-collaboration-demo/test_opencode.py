#!/usr/bin/env python3
"""
简单测试: 验证 OpenCode SDK 连接
"""
import asyncio
import os
import sys

# 添加venv路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'venv', 'lib', 'python3.12', 'site-packages'))

from opencode_agent_sdk import SDKClient, AgentOptions

async def test_opencode():
    server_url = os.getenv("OPENCODE_SERVER_URL", "http://192.168.124.2:4096")
    model = os.getenv("OPENCODE_MODEL", "claude-sonnet-4-5")
    
    print(f"Testing OpenCode SDK...")
    print(f"  Server: {server_url}")
    print(f"  Model: {model}")
    print()
    
    client = SDKClient(options=AgentOptions(
        model=model,
        server_url=server_url,
        system_prompt="你是一个有帮助的编程助手。"
    ))
    
    try:
        print("1. Connecting to OpenCode server...")
        await client.connect()
        print("   ✓ Connected successfully!")
        print()
        
        print("2. Sending query: 'Write a hello world function in Python'")
        await client.query("Write a hello world function in Python. Keep it simple.")
        print()
        
        print("3. Receiving response...")
        response_text = []
        async for msg in client.receive_response():
            if hasattr(msg, 'content') and msg.content:
                response_text.append(msg.content)
                print(f"   > {msg.content[:100]}...")
            elif hasattr(msg, 'text') and msg.text:
                response_text.append(msg.text)
                print(f"   > {msg.text[:100]}...")
        
        print()
        full_response = "\n".join(response_text)
        print(f"✓ Test completed! Response length: {len(full_response)} chars")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nDone.")

if __name__ == "__main__":
    asyncio.run(test_opencode())

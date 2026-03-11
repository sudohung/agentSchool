#!/usr/bin/env python3
"""
Simplified Demo: 使用纯OpenCode SDK的Agent协作系统
不需要API key，直接使用你提供的OpenCode服务
"""
import asyncio
import os
import sys

async def run_demo():
    """5阶段Pipeline Demo"""
    from opencode_agent_sdk import SDKClient, AgentOptions
    
    server_url = "http://192.168.124.2:4096"
    model = "claude-sonnet-4-5"
    
    print("=" * 60)
    print("Agent Collaboration Demo - Pure OpenCode SDK")
    print("=" * 60)
    print(f"Server: {server_url}")
    print(f"Model: {model}")
    print()
    
    # 创建Client
    client = SDKClient(options=AgentOptions(
        model=model,
        server_url=server_url,
        system_prompt="你是一个专业的全栈开发工程师，擅长分析需求、设计架构、编写代码和测试。"
    ))
    
    await client.connect()
    print("✓ Connected to OpenCode\n")
    
    # Demo需求
    requirement = """
    开发一个简单的任务管理Web应用
    - 用户可以创建、编辑、删除任务
    - 任务有标题、描述、截止日期、状态
    - 使用简单的文件存储JSON
    """
    
    # ===== Stage 1: 需求分析 =====
    print("-" * 40)
    print("[Stage 1/5] 需求分析")
    print("-" * 40)
    
    await client.query(f"分析以下需求，输出清晰的需求规格说明:\n{requirement}")
    
    stage1_output = []
    async for msg in client.receive_response():
        if hasattr(msg, 'content') and msg.content:
            stage1_output.append(msg.content)
            print(f"  > {msg.content[:80]}...")
    
    print(f"\n✓ 需求分析完成 ({len(''.join(stage1_output))} chars)\n")
    
    # ===== Stage 2: 架构设计 =====
    print("-" * 40)
    print("[Stage 2/5] 架构设计")
    print("-" * 40)
    
    await client.query("基于需求设计系统架构，包括：技术选型、模块划分、API设计、数据模型")
    
    stage2_output = []
    async for msg in client.receive_response():
        if hasattr(msg, 'content') and msg.content:
            stage2_output.append(msg.content)
            print(f"  > {msg.content[:80]}...")
    
    print(f"\n✓ 架构设计完成 ({len(''.join(stage2_output))} chars)\n")
    
    # ===== Stage 3: 代码实现 =====
    print("-" * 40)
    print("[Stage 3/5] 代码实现")
    print("-" * 40)
    
    await client.query("""基于架构设计，实现一个完整的任务管理Web应用。
要求：
1. 使用Flask框架
2. 单文件实现
3. 包含CRUD功能
4. 使用JSON文件存储
5. 输出完整可运行的代码""")
    
    stage3_output = []
    async for msg in client.receive_response():
        if hasattr(msg, 'content') and msg.content:
            stage3_output.append(msg.content)
            print(f"  > {msg.content[:80]}...")
    
    print(f"\n✓ 代码实现完成 ({len(''.join(stage3_output))} chars)\n")
    
    # ===== Stage 4: 测试验证 =====
    print("-" * 40)
    print("[Stage 4/5] 测试验证")
    print("-" * 40)
    
    await client.query("为刚才实现的代码设计测试用例，说明如何验证功能正确性")
    
    stage4_output = []
    async for msg in client.receive_response():
        if hasattr(msg, 'content') and msg.content:
            stage4_output.append(msg.content)
            print(f"  > {msg.content[:80]}...")
    
    print(f"\n✓ 测试验证完成 ({len(''.join(stage4_output))} chars)\n")
    
    # ===== Stage 5: 部署发布 =====
    print("-" * 40)
    print("[Stage 5/5] 部署发布")
    print("-" * 40)
    
    await client.query("设计部署方案，说明如何将应用部署到生产环境")
    
    stage5_output = []
    async for msg in client.receive_response():
        if hasattr(msg, 'content') and msg.content:
            stage5_output.append(msg.content)
            print(f"  > {msg.content[:80]}...")
    
    print(f"\n✓ 部署发布完成 ({len(''.join(stage5_output))} chars)\n")
    
    # 完成
    print("=" * 60)
    print("✓ Pipeline Demo Completed!")
    print("=" * 60)

if __name__ == "__main__":
    print("Starting demo... (This will take several minutes)")
    asyncio.run(run_demo())

#!/usr/bin/env python3
"""
简单测试: Agent 协作系统 - 文本输入测试
"""
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

DASHSCOPE_API_KEY = "sk-sp-de6e887faf1f49acbad120766050fdd9"
DASHSCOPE_BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
MODEL = "qwen3-coder-next"

async def simple_test():
    print("=" * 50)
    print("简单文本输入测试")
    print("=" * 50)
    print(f"模型: {MODEL}\n")
    
    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=MODEL,
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
        model_info={
            "name": MODEL,
            "family": "qwen",
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
        }
    )
    
    # 创建Agent
    agent = AssistantAgent(
        name="TestAgent",
        model_client=model_client,
        system_message="你是一个友好的AI助手，请用简洁的中文回答问题。"
    )
    
    # 测试1: 简单问候
    print("[测试1] 简单问候")
    print("-" * 30)
    result = await agent.run(task="你好！请用一句话介绍自己。")
    print(f"回复: {result}\n")
    
    # 测试2: 数学问题
    print("[测试2] 数学问题")
    print("-" * 30)
    result = await agent.run(task="请问 123 + 456 = ?")
    print(f"回复: {result}\n")
    
    # 测试3: 代码生成
    print("[测试3] 代码生成")
    print("-" * 30)
    result = await agent.run(task="请用Python写一个计算阶乘的函数")
    print(f"回复: {result}\n")
    
    # 测试4: 多轮对话
    print("[测试4] 多轮对话上下文")
    print("-" * 30)
    await agent.run(task="我最喜欢的颜色是蓝色")
    result = await agent.run(task="我刚才说我喜欢什么颜色？")
    print(f"回复: {result}\n")
    
    await model_client.close()
    
    print("=" * 50)
    print("所有测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(simple_test())

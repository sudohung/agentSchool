#!/usr/bin/env python3
"""
Agent Collaboration Demo - AutoGen + DashScope (qwen3-coder-next)
使用阿里云通义千问模型
"""
import asyncio
import os
import logging
from typing import Annotated, Literal
from dataclasses import dataclass, field
from enum import Enum

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== 配置 ==============
DASHSCOPE_API_KEY = "sk-sp-de6e887faf1f49acbad120766050fdd9"
DASHSCOPE_BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
MODEL = "qwen3-coder-next"

# ============== 状态管理 ==============

class Stage(Enum):
    REQUIREMENT = "requirement"
    DESIGN = "design"
    CODE = "code"
    TEST = "test"
    DEPLOY = "deploy"


@dataclass
class ProjectState:
    project_id: str
    current_stage: Stage = Stage.REQUIREMENT
    requirement: str = ""
    design_doc: str = ""
    code_output: str = ""
    test_result: str = ""
    deploy_result: str = ""
    
    def advance(self):
        stages = list(Stage)
        idx = stages.index(self.current_stage)
        if idx < len(stages) - 1:
            self.current_stage = stages[idx + 1]


# ============== OpenCode 集成 ==============

async def execute_with_opencode(prompt: str, task_context: str = "", timeout: int = 300) -> str:
    """通过OpenCode SDK执行代码生成任务"""
    try:
        from opencode_agent_sdk import SDKClient, AgentOptions
        
        server_url = os.getenv("OPENCODE_SERVER_URL", "http://192.168.124.2:4096")
        model = os.getenv("OPENCODE_MODEL", "claude-sonnet-4-5")
        
        print(f"  [OpenCode] Connecting to {server_url}...")
        
        client = SDKClient(options=AgentOptions(
            model=model,
            server_url=server_url,
            system_prompt=f"你是一个专业的软件开发工程师。当前任务上下文: {task_context}"
        ))
        
        await client.connect()
        print(f"  [OpenCode] Connected, sending query...")
        
        await client.query(prompt)
        
        response_parts = []
        async for msg in client.receive_response():
            if hasattr(msg, 'content') and msg.content:
                response_parts.append(msg.content)
            elif hasattr(msg, 'text') and msg.text:
                response_parts.append(msg.text)
        
        response = "\n".join(response_parts) if response_parts else "[No response]"
        print(f"  [OpenCode] Received response ({len(response)} chars)")
        
        return response
        
    except ImportError:
        return f"[MOCK] OpenCode not available"
    except Exception as e:
        return f"[ERROR] {str(e)}"


# ============== Agent 工厂 ==============

def create_model_client():
    """创建DashScope模型客户端"""
    return OpenAIChatCompletionClient(
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


def create_requirement_agent(model_client) -> AssistantAgent:
    return AssistantAgent(
        name="RequirementAgent",
        model_client=model_client,
        system_message="""你是一个需求分析师。
将用户的需求描述转化为清晰、完整的需求规格说明。
输出格式:
1. 项目概述
2. 功能需求列表
3. 非功能需求
4. 约束条件
5. 验收标准

请用中文回复。"""
    )


def create_design_agent(model_client) -> AssistantAgent:
    return AssistantAgent(
        name="DesignAgent", 
        model_client=model_client,
        system_message="""你是系统架构师。
基于需求规格，设计系统架构。
输出格式:
1. 系统架构图(文字描述)
2. 技术选型
3. 模块划分
4. 数据模型
5. API设计

请用中文回复。"""
    )


def create_coder_agent(model_client) -> AssistantAgent:
    return AssistantAgent(
        name="CoderAgent",
        model_client=model_client,
        system_message="""你是全栈开发工程师。
根据设计文档，实现完整的代码。
代码要求:
- 完整可运行
- 遵循最佳实践
- 包含必要的注释

请用中文回复。"""
    )


def create_tester_agent(model_client) -> AssistantAgent:
    return AssistantAgent(
        name="TesterAgent",
        model_client=model_client,
        system_message="""你是QA工程师。
为代码编写测试用例并执行验证。
输出:
1. 测试计划
2. 测试用例
3. 测试结果
4. 问题报告

请用中文回复。"""
    )


def create_deploy_agent(model_client) -> AssistantAgent:
    return AssistantAgent(
        name="DeployAgent",
        model_client=model_client,
        system_message="""你是DevOps工程师。
制定部署方案并执行部署。
输出:
1. 部署计划
2. 环境配置
3. 部署步骤
4. 验证结果

请用中文回复。"""
    )


# ============== Pipeline ==============

async def run_pipeline(user_requirement: str, model_client):
    state = ProjectState(project_id="demo-001")
    
    # 导入代码执行器
    from code_executor import CodeExecutor, Language, ValidationReport
    
    print(f"\n{'='*60}")
    print(f"开始执行软件开发Pipeline")
    print(f"模型: {MODEL}")
    print(f"需求: {user_requirement[:80]}...")
    print(f"{'='*60}\n")
    
    # Stage 1: 需求分析
    print("\n[阶段1/5] 需求分析...")
    requirement_agent = create_requirement_agent(model_client)
    req_result = await requirement_agent.run(task=f"分析以下需求:\n{user_requirement}")
    print(f"需求分析完成\n")
    
    # Stage 2: 架构设计
    print("[阶段2/5] 架构设计...")
    design_agent = create_design_agent(model_client)
    design_result = await design_agent.run(task=f"基于需求设计系统架构:\n{req_result}")
    state.design_doc = str(design_result)
    print(f"架构设计完成\n")
    
    # Stage 3: 代码实现 + 执行验证
    print("[阶段3/5] 代码实现与执行验证...")
    coder_agent = create_coder_agent(model_client)
    code_result = await coder_agent.run(
        task=f"""基于架构设计实现完整代码。

要求:
1. 必须是完整可运行的代码
2. 如果是Python，写一个完整的.py文件，包含main函数测试
3. 如果是JavaScript，写一个完整的.js文件，可以直接node运行
4. 代码要简洁但功能完整

架构设计:
{state.design_doc}

请直接输出代码，不要解释。"""
    )
    state.code_output = str(code_result)
    print(f"代码生成完成\n")
    
    # 执行生成的代码
    print("-" * 40)
    print("[代码执行验证]")
    print("-" * 40)
    
    executor = CodeExecutor()
    
    # 检测语言并创建项目
    if "python" in state.code_output.lower() or "def " in state.code_output:
        language = Language.PYTHON
        main_file = "src/main.py"
    elif "javascript" in state.code_output.lower() or "function" in state.code_output:
        language = Language.JAVASCRIPT
        main_file = "src/main.js"
    else:
        # 默认Python
        language = Language.PYTHON
        main_file = "src/main.py"
    
    executor.create_project("generated_code", language)
    executor.write_code(main_file, state.code_output)
    
    # 执行代码
    exec_result = executor.execute_code(main_file, language)
    print(f"执行结果: {'✅ 成功' if exec_result.success else '❌ 失败'}")
    print(f"耗时: {exec_result.duration:.2f}s")
    print(f"退出码: {exec_result.exit_code}")
    if exec_result.stdout:
        print(f"输出:\n{exec_result.stdout[:500]}")
    if exec_result.stderr:
        print(f"错误:\n{exec_result.stderr[:500]}")
    
    # 运行测试（如果有测试文件）
    test_report = executor.run_tests(language)
    print(f"\n测试结果: {test_report.summary}")
    executor.cleanup()
    
    state.code_output += f"\n\n--- 执行验证结果 ---\n"
    state.code_output += f"执行: {'成功' if exec_result.success else '失败'}\n"
    state.code_output += f"输出: {exec_result.stdout}\n"
    state.code_output += f"测试: {test_report.summary}\n"
    
    print(f"\n✅ 代码执行验证完成\n")
    
    # Stage 4: 测试验证
    print("[阶段4/5] 测试验证...")
    tester_agent = create_tester_agent(model_client)
    test_result = await tester_agent.run(task=f"为代码设计更完整的测试用例:\n{state.code_output}")
    state.test_result = str(test_result)
    print(f"测试验证完成\n")
    
    # Stage 5: 部署发布
    print("[阶段5/5] 部署发布...")
    deploy_agent = create_deploy_agent(model_client)
    deploy_result = await deploy_agent.run(task=f"设计部署方案:\n{state.code_output}")
    state.deploy_result = str(deploy_result)
    print(f"部署发布完成\n")
    
    state.advance()
    print(f"\n{'='*60}")
    print(f"Pipeline执行完成! 当前阶段: {state.current_stage.value}")
    print(f"{'='*60}\n")
    
    return state


# ============== 主入口 ==============

async def main():
    model_client = create_model_client()
    
    demo_requirement = """
    开发一个简单的任务管理Web应用
    - 用户可以创建、编辑、删除任务
    - 任务有标题、描述、截止日期、状态
    - 支持任务分类/标签
    - 使用简单的文件存储
    """
    
    await run_pipeline(demo_requirement, model_client)
    
    await model_client.close()
    print("\n===== 执行完成 =====")


if __name__ == "__main__":
    print(f"使用模型: {MODEL}")
    print(f"API端点: {DASHSCOPE_BASE_URL}")
    print()
    asyncio.run(main())

"""
MVP Demo: Agent Collaboration System
使用 AutoGen + OpenCode SDK 实现软件开发Agent协作系统

架构: 5阶段Pipeline (需求→设计→编码→测试→部署)
"""

import asyncio
import os
from typing import Annotated, Literal
from dataclasses import dataclass, field
from enum import Enum

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


# ============== 状态管理 ==============

class Stage(Enum):
    REQUIREMENT = "requirement"
    DESIGN = "design"
    CODE = "code"
    TEST = "test"
    DEPLOY = "deploy"


@dataclass
class ProjectState:
    """全局项目状态"""
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
    """
    通过OpenCode SDK执行代码生成任务
    使用流式响应收集完整结果
    """
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
        
        # 发送查询
        await client.query(prompt)
        
        # 收集流式响应
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
        return f"[MOCK] OpenCode not available - {prompt}"
    except asyncio.TimeoutError:
        return f"[TIMEOUT] OpenCode execution timed out after {timeout}s"
    except Exception as e:
        return f"[ERROR] OpenCode execution failed: {str(e)}"


# ============== Agent 定义 ==============

def create_requirement_agent(model_client) -> AssistantAgent:
    """需求分析Agent"""
    return AssistantAgent(
        name="RequirementAgent",
        model_client=model_client,
        system_message="""你是一个需求分析师。
你的任务是将用户的需求描述转化为清晰、完整的需求规格说明。
输出格式:
1. 项目概述
2. 功能需求列表
3. 非功能需求
4. 约束条件
5. 验收标准"""
    )


def create_design_agent(model_client) -> AssistantAgent:
    """架构设计Agent"""
    return AssistantAgent(
        name="DesignAgent",
        model_client=model_client,
        system_message="""你是一个系统架构师。
基于需求规格，设计系统架构。
输出格式:
1. 系统架构图(文字描述)
2. 技术选型
3. 模块划分
4. 数据模型
5. API设计"""
    )


def create_coder_agent(model_client) -> AssistantAgent:
    """代码实现Agent"""
    return AssistantAgent(
        name="CoderAgent",
        model_client=model_client,
        system_message="""你是一个全栈开发工程师。
根据设计文档，实现完整的代码。
你有两个工具:
1. generate_code - 生成代码
2. execute_code - 执行代码验证

代码要求:
- 完整可运行
- 遵循最佳实践
- 包含必要的注释"""
    )


def create_tester_agent(model_client) -> AssistantAgent:
    """测试验证Agent"""
    return AssistantAgent(
        name="TesterAgent",
        model_client=model_client,
        system_message="""你是一个QA工程师。
为代码编写测试用例并执行验证。
输出:
1. 测试计划
2. 测试用例
3. 测试结果
4. 问题报告"""
    )


def create_deploy_agent(model_client) -> AssistantAgent:
    """部署发布Agent"""
    return AssistantAgent(
        name="DeployAgent",
        model_client=model_client,
        system_message="""你是一个DevOps工程师。
制定部署方案并执行部署。
输出:
1. 部署计划
2. 环境配置
3. 部署步骤
4. 验证结果"""
    )


# ============== Pipeline 编排 ==============

async def run_pipeline(
    user_requirement: str,
    model_client,
    state: ProjectState
):
    """
    5阶段Pipeline执行
    """
    print(f"\n{'='*60}")
    print(f"开始执行软件开发Pipeline")
    print(f"项目ID: {state.project_id}")
    print(f"需求: {user_requirement[:100]}...")
    print(f"{'='*60}\n")
    
    # Stage 1: 需求分析
    print("\n[阶段1/5] 需求分析...")
    state.requirement = user_requirement
    requirement_agent = create_requirement_agent(model_client)
    req_result = await requirement_agent.run(
        task=f"分析以下需求:\n{user_requirement}"
    )
    print(f"需求分析完成\n")
    
    # Stage 2: 架构设计
    print("[阶段2/5] 架构设计...")
    design_agent = create_design_agent(model_client)
    design_result = await design_agent.run(
        task=f"基于以下需求设计系统架构:\n{req_result}"
    )
    state.design_doc = str(design_result)
    print(f"架构设计完成\n")
    
    # Stage 3: 代码实现 (使用OpenCode)
    print("[阶段3/5] 代码实现 (使用OpenCode)...")
    code_prompt = f"""
基于以下设计文档，实现完整代码:

{state.design_doc}

请生成:
1. 项目结构
2. 核心代码文件
3. 配置文件
"""
    state.code_output = await execute_with_opencode(
        code_prompt, 
        task_context="代码实现阶段"
    )
    print(f"代码实现完成\n")
    
    # Stage 4: 测试验证
    print("[阶段4/5] 测试验证...")
    tester_agent = create_tester_agent(model_client)
    test_result = await tester_agent.run(
        task=f"为以下代码编写测试:\n{state.code_output}"
    )
    state.test_result = str(test_result)
    print(f"测试验证完成\n")
    
    # Stage 5: 部署发布
    print("[阶段5/5] 部署发布...")
    deploy_agent = create_deploy_agent(model_client)
    deploy_result = await deploy_agent.run(
        task=f"制定以下系统的部署方案:\n{state.code_output}"
    )
    state.deploy_result = str(deploy_result)
    print(f"部署发布完成\n")
    
    state.advance()
    print(f"\n{'='*60}")
    print(f"Pipeline执行完成! 当前阶段: {state.current_stage.value}")
    print(f"{'='*60}\n")
    
    return state


# ============== 主入口 ==============

async def main():
    """
    演示入口
    """
    # 配置Model Client
    model_client = OpenAIChatCompletionClient(
        model=os.getenv("MODEL", "gpt-4o"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # 初始化项目状态
    state = ProjectState(project_id="demo-001")
    
    # 示例需求
    demo_requirement = """
    开发一个简单的任务管理Web应用
    - 用户可以创建、编辑、删除任务
    - 任务有标题、描述、截止日期、状态
    - 支持任务分类/标签
    - 使用简单的文件存储
    """
    
    # 执行Pipeline
    await run_pipeline(demo_requirement, model_client, state)
    
    # 输出最终状态
    print("\n===== 最终项目状态 =====")
    print(f"阶段: {state.current_stage.value}")
    print(f"代码输出预览:\n{state.code_output[:500]}...")
    
    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())

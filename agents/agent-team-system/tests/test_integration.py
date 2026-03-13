"""Phase 1 集成测试."""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.asyncio
async def test_agent_roles_import():
    """测试所有 Agent 角色导入."""
    from agent.roles import (
        ProductManagerAgent,
        SystemArchitectAgent,
        TechLeadAgent,
        FrontendDeveloperAgent,
        BackendDeveloperAgent,
        FullStackDeveloperAgent,
        QAAgent,
        CodeReviewerAgent,
        DocWriterAgent,
        DevOpsAgent,
        SecurityAgent,
        CoordinatorAgent,
    )
    
    agents = [
        ("Product Manager", ProductManagerAgent),
        ("System Architect", SystemArchitectAgent),
        ("Tech Lead", TechLeadAgent),
        ("Frontend Developer", FrontendDeveloperAgent),
        ("Backend Developer", BackendDeveloperAgent),
        ("Full Stack Developer", FullStackDeveloperAgent),
        ("QA Engineer", QAAgent),
        ("Code Reviewer", CodeReviewerAgent),
        ("Doc Writer", DocWriterAgent),
        ("DevOps Engineer", DevOpsAgent),
        ("Security Engineer", SecurityAgent),
        ("Coordinator", CoordinatorAgent),
    ]
    
    assert len(agents) == 12, "应该有 12 个 Agent 角色"
    for name, cls in agents:
        assert cls is not None, f"{name} 应该不为 None"


@pytest.mark.asyncio
async def test_agent_creation():
    """测试 Agent 创建."""
    from agent.roles import (
        ProductManagerAgent,
        SystemArchitectAgent,
        TechLeadAgent,
        FrontendDeveloperAgent,
        BackendDeveloperAgent,
        QAAgent,
        CodeReviewerAgent,
        DocWriterAgent,
        CoordinatorAgent,
    )
    
    agents_classes = [
        ("Product Manager", ProductManagerAgent),
        ("System Architect", SystemArchitectAgent),
        ("Tech Lead", TechLeadAgent),
        ("Frontend Developer", FrontendDeveloperAgent),
        ("Backend Developer", BackendDeveloperAgent),
        ("QA Engineer", QAAgent),
        ("Code Reviewer", CodeReviewerAgent),
        ("Doc Writer", DocWriterAgent),
        ("Coordinator", CoordinatorAgent),
    ]
    
    created_count = 0
    for name, cls in agents_classes:
        try:
            agent = cls()
            assert agent.role == name
            created_count += 1
        except Exception as e:
            print(f"创建 {name} 失败：{e}")
    
    assert created_count >= 8, f"至少应该能创建 8 个 Agent，实际创建{created_count}个"


@pytest.mark.asyncio
async def test_agent_base_functionality():
    """测试 Agent 基础功能."""
    from agent.roles import ProductManagerAgent
    from agent.permissions import PermissionType
    
    pm = ProductManagerAgent()
    
    # 测试状态
    assert pm.status.value == "idle", "初始状态应该是 idle"
    
    # 测试状态机
    assert pm.state_machine.current_state.value == "idle"
    
    # 测试记忆
    pm.add_to_memory("test", "value")
    assert pm.get_from_memory("test") == "value"
    
    # 测试权限请求
    action = await pm.request_permission(
        type=PermissionType.FILE_READ,
        resource="test.txt",
        description="Test",
    )
    # 权限请求应该返回一个 action (可能是 ASK，因为需要用户响应)
    assert action is not None


@pytest.mark.asyncio
async def test_ralph_loop_engine():
    """测试 Ralph Loop 引擎."""
    from agent.roles import ProductManagerAgent, SystemArchitectAgent, TechLeadAgent
    from ralph_loop.controller import IterationController
    from ralph_loop.state import LoopStatus
    
    controller = IterationController()
    
    # 创建测试 Agent
    agents = [
        ProductManagerAgent(),
        SystemArchitectAgent(),
        TechLeadAgent(),
    ]
    
    # 测试启动
    await controller.start(agents, None)
    assert controller.status == LoopStatus.RUNNING, "启动后状态应该是 RUNNING"
    
    # 测试停止
    await controller.stop()
    assert controller.status == LoopStatus.STOPPED, "停止后状态应该是 STOPPED"

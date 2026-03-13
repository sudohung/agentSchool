"""Phase 2 Agent 角色库完整测试.

测试范围:
- L1: 角色导入和实例化
- L2: Ralph Loop 方法测试
- L3: 基类继承验证
- L4: 依赖模块集成测试
- L5: 多角色协作测试
- L6: Ralph Loop 引擎集成
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.config import (
    Document, DocumentType, DocumentMetadata, DocumentContent,
    Request, RequestType, RequestPriority, RequestStatus
)
from agent.base import Agent
from agent.permissions import PermissionType, PermissionAction


# ============================================================================
# L1: 角色导入测试
# ============================================================================

class TestAgentRolesImport:
    """测试所有 Agent 角色导入"""
    
    def test_import_all_roles(self):
        """测试导入所有 12 个角色"""
        from agent.roles import (
            ProductManagerAgent,
            SystemArchitectAgent,
            TechLeadAgent,
            CoordinatorAgent,
            FrontendDeveloperAgent,
            BackendDeveloperAgent,
            FullStackDeveloperAgent,
            QAAgent,
            CodeReviewerAgent,
            DocWriterAgent,
            DevOpsAgent,
            SecurityAgent,
        )
        
        # 验证所有类都被正确导入
        assert ProductManagerAgent is not None
        assert SystemArchitectAgent is not None
        assert TechLeadAgent is not None
        assert CoordinatorAgent is not None
        assert FrontendDeveloperAgent is not None
        assert BackendDeveloperAgent is not None
        assert FullStackDeveloperAgent is not None
        assert QAAgent is not None
        assert CodeReviewerAgent is not None
        assert DocWriterAgent is not None
        assert DevOpsAgent is not None
        assert SecurityAgent is not None
    
    def test_import_count(self):
        """测试导入的角色数量"""
        from agent.roles import __all__
        
        # 应该有 12 个角色类 + 4 个工具函数/类
        assert len(__all__) >= 12
    
    def test_import_loader_functions(self):
        """测试导入加载器函数"""
        from agent.roles import (
            get_agent_definition,
            list_all_agent_roles,
            AgentDefinitionLoader,
            initialize_agents,
        )
        
        assert get_agent_definition is not None
        assert list_all_agent_roles is not None
        assert AgentDefinitionLoader is not None
        assert initialize_agents is not None


# ============================================================================
# L2: 角色实例化测试
# ============================================================================

class TestAgentInstantiation:
    """测试所有角色实例化"""
    
    @pytest.mark.asyncio
    async def test_instantiate_all_roles(self):
        """测试实例化所有 12 个角色"""
        from agent.roles import (
            ProductManagerAgent,
            SystemArchitectAgent,
            TechLeadAgent,
            CoordinatorAgent,
            FrontendDeveloperAgent,
            BackendDeveloperAgent,
            FullStackDeveloperAgent,
            QAAgent,
            CodeReviewerAgent,
            DocWriterAgent,
            DevOpsAgent,
            SecurityAgent,
        )
        
        agents = [
            ProductManagerAgent(),
            SystemArchitectAgent(),
            TechLeadAgent(),
            CoordinatorAgent(),
            FrontendDeveloperAgent(),
            BackendDeveloperAgent(),
            FullStackDeveloperAgent(),
            QAAgent(),
            CodeReviewerAgent(),
            DocWriterAgent(),
            DevOpsAgent(),
            SecurityAgent(),
        ]
        
        assert len(agents) == 12
        
        for agent in agents:
            assert agent is not None
            assert isinstance(agent, Agent)
    
    @pytest.mark.asyncio
    async def test_role_attributes(self):
        """测试角色属性"""
        from agent.roles import ProductManagerAgent, FrontendDeveloperAgent
        
        # 测试 Product Manager
        pm = ProductManagerAgent()
        assert pm.role == "Product Manager"
        assert len(pm.expertise) > 0
        assert "需求分析" in pm.expertise
        
        # 测试 Frontend Developer
        fe = FrontendDeveloperAgent()
        assert fe.role == "Frontend Developer"
        assert len(fe.expertise) > 0
        assert "HTML/CSS/JavaScript" in fe.expertise
    
    @pytest.mark.asyncio
    async def test_initial_state(self):
        """测试初始状态"""
        from agent.roles import ProductManagerAgent
        
        pm = ProductManagerAgent()
        
        # 验证状态
        assert pm.status.value == "idle"
        assert pm.state_machine.current_state.value == "idle"
        
        # 验证记忆系统
        assert pm.memory is not None
        
        # 验证权限处理器
        assert pm.handler is not None


# ============================================================================
# L3: Ralph Loop 方法测试
# ============================================================================

class TestRalphLoopMethods:
    """测试所有角色的 Ralph Loop 方法"""
    
    @pytest.mark.asyncio
    async def test_read_documents_method(self):
        """测试 read_documents 方法"""
        from agent.roles import (
            ProductManagerAgent,
            FrontendDeveloperAgent,
            BackendDeveloperAgent,
        )
        
        agents = [
            ProductManagerAgent(),
            FrontendDeveloperAgent(),
            BackendDeveloperAgent(),
        ]
        
        for agent in agents:
            # 没有注入 document_hub 时，应该返回空列表
            docs = await agent.read_documents()
            assert isinstance(docs, list)
    
    @pytest.mark.asyncio
    async def test_act_on_requests_method(self):
        """测试 act_on_requests 方法"""
        from agent.roles import (
            ProductManagerAgent,
            QAAgent,
        )
        
        agents = [
            ProductManagerAgent(),
            QAAgent(),
        ]
        
        for agent in agents:
            # 没有注入 request_board 时，应该返回空列表
            requests = await agent.act_on_requests()
            assert isinstance(requests, list)
    
    @pytest.mark.asyncio
    async def test_leverage_expertise_method(self):
        """测试 leverage_expertise 方法"""
        from agent.roles import ProductManagerAgent
        
        pm = ProductManagerAgent()
        
        # Mock send_message 方法
        pm.send_message = AsyncMock(return_value="测试结果")
        
        result = await pm.leverage_expertise()
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_produce_document_method(self):
        """测试 produce_document 方法"""
        from agent.roles import (
            ProductManagerAgent,
            FrontendDeveloperAgent,
            BackendDeveloperAgent,
        )
        
        agents = [
            ProductManagerAgent(),
            FrontendDeveloperAgent(),
            BackendDeveloperAgent(),
        ]
        
        for agent in agents:
            doc = await agent.produce_document("测试工作结果")
            assert isinstance(doc, Document)
            assert doc.metadata.author == agent.role
            assert doc.content.content is not None
    
    @pytest.mark.asyncio
    async def test_help_requests_method(self):
        """测试 help_requests 方法"""
        from agent.roles import (
            ProductManagerAgent,
            FrontendDeveloperAgent,
        )
        
        agents = [
            ProductManagerAgent(),
            FrontendDeveloperAgent(),
        ]
        
        for agent in agents:
            requests = await agent.help_requests()
            assert isinstance(requests, list)
            assert len(requests) > 0
            
            # 验证 Request 结构
            for req in requests:
                assert isinstance(req, Request)
                assert req.from_agent == agent.role
                assert req.to_agent != agent.role
                # status 可能是枚举或字符串（Pydantic use_enum_values=True）
                assert req.status in [RequestStatus.PENDING, 'pending']


# ============================================================================
# L4: 基类继承验证
# ============================================================================

class TestAgentInheritance:
    """测试所有角色继承自 Agent 基类"""
    
    def test_inheritance_chain(self):
        """测试继承链"""
        from agent.roles import (
            ProductManagerAgent,
            FrontendDeveloperAgent,
            BackendDeveloperAgent,
            QAAgent,
        )
        
        agents = [
            ProductManagerAgent(),
            FrontendDeveloperAgent(),
            BackendDeveloperAgent(),
            QAAgent(),
        ]
        
        for agent in agents:
            assert isinstance(agent, Agent)
    
    @pytest.mark.asyncio
    async def test_base_class_methods(self):
        """测试基类方法可访问"""
        from agent.roles import ProductManagerAgent
        
        pm = ProductManagerAgent()
        
        # 测试记忆方法
        pm.add_to_memory("test_key", "test_value")
        assert pm.get_from_memory("test_key") == "test_value"
        
        # 测试权限方法
        action = await pm.request_permission(
            type=PermissionType.FILE_READ,
            resource="test.txt",
            description="Test",
        )
        assert action is not None
    
    @pytest.mark.asyncio
    async def test_generate_id_method(self):
        """测试 ID 生成方法"""
        from agent.roles import ProductManagerAgent
        import time
        
        pm = ProductManagerAgent()
        
        id1 = pm._generate_id("test")
        time.sleep(0.01)  # 确保时间戳不同
        id2 = pm._generate_id("test")
        
        # ID 格式应该是 test_XXXXX
        assert id1.startswith("test_")
        assert id2.startswith("test_")


# ============================================================================
# L5: 依赖模块集成测试
# ============================================================================

class TestRoleDependencies:
    """测试角色与依赖模块的集成"""
    
    @pytest.mark.asyncio
    async def test_document_hub_integration(self):
        """测试文档中心集成"""
        from agent.roles import ProductManagerAgent
        
        pm = ProductManagerAgent()
        
        # 创建 Mock DocumentHub
        mock_hub = Mock()
        mock_hub.list_documents = AsyncMock(return_value=[
            Document(
                id="doc_001",
                path="test.md",
                metadata=DocumentMetadata(
                    title="Test",
                    doc_type=DocumentType.PRD,
                    author="Test",
                    created_at=0,
                    updated_at=0,
                    version=1,
                ),
                content=DocumentContent(content="Test content"),
            )
        ])
        
        pm.document_hub = mock_hub
        
        docs = await pm.read_documents()
        assert len(docs) == 1
        assert docs[0].id == "doc_001"
    
    @pytest.mark.asyncio
    async def test_request_board_integration(self):
        """测试诉求看板集成"""
        from agent.roles import FrontendDeveloperAgent
        
        fe = FrontendDeveloperAgent()
        
        # 创建 Mock RequestBoard
        mock_board = Mock()
        mock_board.get_requests_for_agent = AsyncMock(return_value=[
            Request(
                id="req_001",
                type=RequestType.COLLABORATION,
                priority=RequestPriority.HIGH,
                status=RequestStatus.PENDING,
                from_agent="Backend Developer",
                to_agent="Frontend Developer",
                subject="API 对接",
                content="请对接 API",
                created_at=0,
                updated_at=0,
            )
        ])
        
        fe.request_board = mock_board
        
        requests = await fe.act_on_requests()
        assert len(requests) == 1
    
    @pytest.mark.asyncio
    async def test_permission_system(self):
        """测试权限系统集成"""
        from agent.roles import BackendDeveloperAgent
        
        be = BackendDeveloperAgent()
        
        # 测试权限请求
        action = await be.request_permission(
            type=PermissionType.FILE_WRITE,
            resource="test.py",
            description="Write test file",
        )
        
        # 应该返回一个 Action (可能是 ASK，因为需要用户确认)
        assert action in [PermissionAction.ALLOW, PermissionAction.DENY, PermissionAction.ASK]


# ============================================================================
# L6: 多角色协作测试
# ============================================================================

class TestMultiAgentCollaboration:
    """测试多角色协作"""
    
    @pytest.mark.asyncio
    async def test_collaboration_flow(self):
        """测试协作流程"""
        from agent.roles import (
            ProductManagerAgent,
            SystemArchitectAgent,
            BackendDeveloperAgent,
        )
        
        # 创建团队
        pm = ProductManagerAgent()
        arch = SystemArchitectAgent()
        be = BackendDeveloperAgent()
        
        # PM 发布诉求
        pm_requests = await pm.help_requests()
        assert len(pm_requests) > 0
        
        # 验证诉求目标
        architect_request = [r for r in pm_requests if "Architect" in r.to_agent]
        assert len(architect_request) > 0
        
        # Architect 产出文档
        arch_doc = await arch.produce_document("架构设计结果")
        # doc_type 可能是枚举或字符串（Pydantic use_enum_values=True）
        assert arch_doc.metadata.doc_type in [DocumentType.ARCHITECTURE, 'architecture']
        
        # Backend 开发
        be_doc = await be.produce_document("后端开发结果")
        assert be_doc.metadata.doc_type in [DocumentType.API_DOC, 'api_doc']
    
    @pytest.mark.asyncio
    async def test_role_chain(self):
        """测试角色链"""
        from agent.roles import (
            ProductManagerAgent,
            TechLeadAgent,
            BackendDeveloperAgent,
        )
        
        pm = ProductManagerAgent()
        tl = TechLeadAgent()
        be = BackendDeveloperAgent()
        
        # 验证协作关系
        pm_requests = await pm.help_requests()
        
        # PM 应该向 Architect 和 Tech Lead 发送诉求
        target_roles = [r.to_agent for r in pm_requests]
        assert len(target_roles) > 0


# ============================================================================
# L7: Ralph Loop 引擎集成测试
# ============================================================================

class TestRalphLoopIntegration:
    """测试 Ralph Loop 引擎集成"""
    
    @pytest.mark.asyncio
    async def test_controller_with_agents(self):
        """测试控制器与 Agent 集成"""
        from agent.roles import (
            ProductManagerAgent,
            SystemArchitectAgent,
        )
        from ralph_loop.controller import IterationController
        from ralph_loop.state import LoopStatus
        
        controller = IterationController()
        
        agents = [
            ProductManagerAgent(),
            SystemArchitectAgent(),
        ]
        
        # 启动
        await controller.start(agents, None)
        assert controller.status == LoopStatus.RUNNING
        
        # 停止
        await controller.stop()
        assert controller.status == LoopStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_iteration_state_tracking(self):
        """测试迭代状态跟踪"""
        from agent.roles import (
            ProductManagerAgent,
            FrontendDeveloperAgent,
        )
        from ralph_loop.controller import IterationController
        
        controller = IterationController()
        
        agents = [
            ProductManagerAgent(),
            FrontendDeveloperAgent(),
        ]
        
        await controller.start(agents, None)
        
        # 检查当前迭代状态
        current = controller.get_current_iteration()
        assert current is not None
        assert len(current.agents_participating) == 2
        
        await controller.stop()


# ============================================================================
# L8: 特殊角色测试
# ============================================================================

class TestSpecialRoles:
    """测试特殊角色功能"""
    
    @pytest.mark.asyncio
    async def test_coordinator_role(self):
        """测试 Coordinator 角色"""
        from agent.roles import CoordinatorAgent
        
        coordinator = CoordinatorAgent()
        
        assert coordinator.role == "Coordinator"
        assert len(coordinator.expertise) > 0
    
    @pytest.mark.asyncio
    async def test_fullstack_role(self):
        """测试 Full Stack Developer 角色"""
        from agent.roles import FullStackDeveloperAgent
        
        fs = FullStackDeveloperAgent()
        
        assert fs.role == "Full Stack Developer"
        # 应该具备前后端技能
        expertise_str = " ".join(fs.expertise)
        assert "前端" in expertise_str or "后端" in expertise_str
    
    @pytest.mark.asyncio
    async def test_security_role(self):
        """测试 Security Engineer 角色"""
        from agent.roles import SecurityAgent
        
        sec = SecurityAgent()
        
        assert sec.role == "Security Engineer"
        doc = await sec.produce_document("安全审计结果")
        assert "安全" in doc.content.content


# ============================================================================
# L9: 边界情况测试
# ============================================================================

class TestEdgeCases:
    """测试边界情况"""
    
    @pytest.mark.asyncio
    async def test_agent_without_dependencies(self):
        """测试没有依赖注入的 Agent"""
        from agent.roles import ProductManagerAgent
        
        pm = ProductManagerAgent()
        
        # 没有 document_hub 和 request_board
        assert pm.document_hub is None
        assert pm.request_board is None
        
        # 方法应该仍然可以调用
        docs = await pm.read_documents()
        assert docs == []
        
        requests = await pm.act_on_requests()
        assert requests == []
    
    @pytest.mark.asyncio
    async def test_document_formatting(self):
        """测试文档格式化"""
        from agent.roles import ProductManagerAgent
        
        pm = ProductManagerAgent()
        
        # 测试不同类型的输入
        doc1 = await pm.produce_document("字符串结果")
        assert "字符串结果" in doc1.content.content
        
        doc2 = await pm.produce_document({"key": "value"})
        assert "value" in doc2.content.content
    
    @pytest.mark.asyncio
    async def test_request_priority(self):
        """测试诉求优先级"""
        from agent.roles import ProductManagerAgent
        
        pm = ProductManagerAgent()
        
        requests = await pm.help_requests()
        
        for req in requests:
            # priority 可能是枚举或字符串（Pydantic use_enum_values=True）
            priority_ok = (
                req.priority in [
                    RequestPriority.LOW,
                    RequestPriority.NORMAL,
                    RequestPriority.HIGH,
                    RequestPriority.CRITICAL,
                ]
                or req.priority in ['low', 'normal', 'high', 'critical']
            )
            assert priority_ok


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
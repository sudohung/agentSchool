"""Agent Team System - 基础框架测试."""

import sys
import asyncio
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.base import Agent
from agent.config import AgentConfig, AgentStatus
from document_hub.models import Document, DocumentMetadata, DocumentContent, DocumentType
from request_board.models import Request, RequestType, RequestPriority, RequestStatus, RequestResponse
from agent.state import AgentStateMachine, AgentState
from agent.permissions import PermissionType, PermissionAction, PermissionRequest, QuestionOption, QuestionRequest
from agent.handler import PermissionQuestionHandler
from agent.registry import AgentRegistry
from agent.memory import AgentMemory

from document_hub.store import DocumentStore
from request_board.board import RequestBoard

from ralph_loop.config import RalphLoopConfig
from ralph_loop.controller import IterationController
from ralph_loop.state import LoopStatus, IterationState
from ralph_loop.setback import SetbackHandler, SetbackType
from ralph_loop.completion import CompletionChecker, CompletionCriteria


class TestAgentConfig:
    """Agent 配置测试"""
    
    def test_create_config(self):
        """测试创建配置"""
        config = AgentConfig(role="Test Agent", expertise=["testing"])
        assert config.role == "Test Agent"
        assert config.expertise == ["testing"]
        assert config.temperature == 0.7
    
    def test_agent_status(self):
        """测试 Agent 状态"""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.WORKING.value == "working"
        assert AgentStatus.DONE.value == "done"


class TestAgentStateMachine:
    """Agent 状态机测试"""
    
    def test_initial_state(self):
        """测试初始状态"""
        sm = AgentStateMachine()
        assert sm.current_state == AgentState.IDLE
    
    def test_state_transition(self):
        """测试状态转换"""
        sm = AgentStateMachine()
        
        # IDLE → WORKING
        assert sm.can_transition_to(AgentState.WORKING)
        assert sm.transition_to(AgentState.WORKING, "test")
        assert sm.current_state == AgentState.WORKING
        
        # WORKING → DONE
        assert sm.can_transition_to(AgentState.DONE)
        assert sm.transition_to(AgentState.DONE, "test")
        assert sm.current_state == AgentState.DONE
    
    def test_invalid_transition(self):
        """测试无效状态转换"""
        sm = AgentStateMachine()
        
        # IDLE → DONE (不允许)
        assert not sm.can_transition_to(AgentState.DONE)
        assert not sm.transition_to(AgentState.DONE, "test")


class TestPermissions:
    """权限系统测试"""
    
    def test_permission_types(self):
        """测试权限类型"""
        assert PermissionType.FILE_READ.value == "file_read"
        assert PermissionType.FILE_WRITE.value == "file_write"
        assert PermissionType.COMMAND_EXECUTE.value == "command_execute"
    
    def test_permission_actions(self):
        """测试权限操作"""
        assert PermissionAction.ALLOW.value == "allow"
        assert PermissionAction.DENY.value == "deny"
        assert PermissionAction.ASK.value == "ask"
    
    def test_permission_request(self):
        """测试权限请求"""
        req = PermissionRequest(
            id="perm_001",
            type=PermissionType.FILE_READ,
            resource="test.txt",
            description="Test permission",
            requested_by="Test Agent",
            action=PermissionAction.ASK,
        )
        assert req.id == "perm_001"
        assert req.type == "file_read"


class TestPermissionHandler:
    """权限处理器测试"""
    
    @pytest.mark.asyncio
    async def test_auto_allow(self):
        """测试自动允许规则"""
        handler = PermissionQuestionHandler(
            auto_allow_patterns=[r"^file_read:.*\.txt$"]
        )
        
        req = PermissionRequest(
            id="perm_001",
            type=PermissionType.FILE_READ,
            resource="test.txt",
            description="Test",
            requested_by="Test Agent",
            action=PermissionAction.ASK,
        )
        
        response = await handler.handle_permission(req)
        assert response.action == PermissionAction.ALLOW
    
    @pytest.mark.asyncio
    async def test_pending_request(self):
        """测试待处理请求"""
        handler = PermissionQuestionHandler()
        
        req = PermissionRequest(
            id="perm_002",
            type=PermissionType.FILE_WRITE,
            resource="test.py",
            description="Test",
            requested_by="Test Agent",
            action=PermissionAction.ASK,
        )
        
        response = await handler.handle_permission(req)
        assert response.action == PermissionAction.ASK
        assert len(handler.pending_permissions) == 1


class TestAgentMemory:
    """Agent 记忆系统测试"""
    
    def test_add_and_get(self):
        """测试添加和获取记忆"""
        memory = AgentMemory()
        
        memory.add("key1", "value1", "short")
        assert memory.get("key1", "short") == "value1"
    
    def test_long_term_memory(self):
        """测试长期记忆"""
        memory = AgentMemory()
        
        memory.add("key2", "value2", "long")
        assert memory.get("key2", "long") == "value2"
    
    def test_delete(self):
        """测试删除记忆"""
        memory = AgentMemory()
        
        memory.add("key3", "value3")
        assert memory.delete("key3")
        assert memory.get("key3") is None
    
    def test_clear(self):
        """测试清空记忆"""
        memory = AgentMemory()
        
        memory.add("key1", "value1")
        memory.add("key2", "value2", "long")
        
        memory.clear("short")
        assert memory.get("key1") is None
        assert memory.get("key2", "long") == "value2"


class TestAgentRegistry:
    """Agent 注册表测试"""
    
    def test_register_role(self):
        """测试注册角色"""
        AgentRegistry.register("Test Role 1", Agent, "core")
        roles = AgentRegistry.list_roles()
        assert "Test Role 1" in roles
    
    def test_get_role(self):
        """测试获取角色"""
        role_class = AgentRegistry.get_role("Test Role 1")
        assert role_class == Agent
    
    def test_list_by_category(self):
        """测试按分类列出角色"""
        roles = AgentRegistry.list_roles("core")
        assert "Test Role 1" in roles


class TestDocumentStore:
    """文档存储测试"""
    
    @pytest.mark.asyncio
    async def test_save_and_load(self, tmp_path):
        """测试保存和加载文档"""
        store = DocumentStore(base_path=str(tmp_path / "storage"))
        
        doc = Document(
            id="doc_001",
            path="test/test.md",
            metadata=DocumentMetadata(
                title="Test Document",
                doc_type=DocumentType.OTHER,
                author="Test Agent",
                created_at=0,
                updated_at=0,
                version=1,
            ),
            content=DocumentContent(
                content="# Test\n\nContent",
            ),
        )
        
        # 保存
        result = await store.save(doc)
        assert result is True
        
        # 加载
        loaded = await store.load("doc_001")
        assert loaded is not None
        assert loaded.id == "doc_001"
    
    @pytest.mark.asyncio
    async def test_delete(self, tmp_path):
        """测试删除文档"""
        store = DocumentStore(base_path=str(tmp_path / "storage"))
        
        doc = Document(
            id="doc_002",
            path="test/test.md",
            metadata=DocumentMetadata(
                title="Test",
                doc_type=DocumentType.OTHER,
                author="Test",
                created_at=0,
                updated_at=0,
                version=1,
            ),
            content=DocumentContent(content="Test"),
        )
        
        await store.save(doc)
        result = await store.delete("doc_002")
        assert result is True
        
        loaded = await store.load("doc_002")
        assert loaded is None


class TestRequestBoard:
    """诉求看板测试"""
    
    @pytest.mark.asyncio
    async def test_create_request(self):
        """测试创建诉求"""
        board = RequestBoard()
        
        req = Request(
            id="req_001",
            type=RequestType.COLLABORATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent="Agent 1",
            to_agent="Agent 2",
            subject="Test Request",
            content="Test content",
            created_at=0,
            updated_at=0,
        )
        
        request_id = await board.create_request(req)
        assert request_id == "req_001"
    
    @pytest.mark.asyncio
    async def test_get_requests_for_agent(self):
        """测试获取 Agent 的诉求"""
        board = RequestBoard()
        
        req = Request(
            id="req_002",
            type=RequestType.COLLABORATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent="Agent 1",
            to_agent="Agent 2",
            subject="Test",
            content="Test",
            created_at=0,
            updated_at=0,
        )
        
        await board.create_request(req)
        requests = await board.get_requests_for_agent("Agent 2")
        assert len(requests) == 1
    
    @pytest.mark.asyncio
    async def test_add_response(self):
        """测试添加响应"""
        board = RequestBoard()
        
        req = Request(
            id="req_003",
            type=RequestType.COLLABORATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent="Agent 1",
            to_agent="Agent 2",
            subject="Test",
            content="Test",
            created_at=0,
            updated_at=0,
        )
        
        await board.create_request(req)
        
        from request_board.models import RequestResponse
        
        response = RequestResponse(
            id="resp_001",
            request_id="req_003",
            from_agent="Agent 2",
            content="Response",
            timestamp=0,
        )
        
        result = await board.add_response("req_003", response)
        assert result is True


class TestRalphLoop:
    """Ralph Loop 引擎测试"""
    
    def test_config(self):
        """测试配置"""
        config = RalphLoopConfig()
        assert config.max_iterations == 50
        assert config.completion_threshold == 0.9
    
    def test_iteration_state(self):
        """测试迭代状态"""
        state = IterationState(
            iteration_number=1,
            start_time=0,
            status=LoopStatus.RUNNING,
            agents_participating=["Agent 1"],
        )
        assert state.iteration_number == 1
        assert state.status == LoopStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_controller(self):
        """测试控制器"""
        controller = IterationController()
        
        await controller.start([], None)
        assert controller.status == LoopStatus.RUNNING
        
        await controller.stop()
        assert controller.status == LoopStatus.STOPPED
    
    def test_setback_handler(self):
        """测试挫折处理器"""
        handler = SetbackHandler()
        assert len(handler.get_setbacks()) == 0
    
    def test_completion_checker(self):
        """测试完成度检查器"""
        criteria = CompletionCriteria()
        checker = CompletionChecker(criteria)
        
        result = asyncio.run(checker.check({
            "requirement_coverage": 0.95,
            "document_completeness": 0.9,
            "quality_score": 0.85,
        }))
        
        assert result["ready"] is True
        assert result["score"] >= 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

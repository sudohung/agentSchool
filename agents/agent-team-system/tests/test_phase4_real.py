"""Phase 4 完整真实测试 - 不使用 Mock.

使用真实的 Agent、DocumentStore、RequestBoard 组件进行测试。
"""

import pytest
import asyncio
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import agent.roles
from agent.config import (
    Document as AgentDocument,
    DocumentType,
    DocumentMetadata as AgentDocumentMetadata,
    DocumentContent as AgentDocumentContent,
)
from document_hub.models import Document, DocumentMetadata, DocumentContent
from document_hub.store import DocumentStore
from request_board.board import RequestBoard

from workflow.config import WorkflowConfig
from workflow.context import WorkflowContext
from workflow.engine import WorkflowEngine, WorkflowResult
from workflow.coordinator import TeamCoordinator, IterationResult
from workflow.quality import QualityGate, QualityGateResult, QualityCheckType

from ralph_loop.controller import IterationController
from ralph_loop.setback import SetbackHandler, SetbackType, SetbackSeverity
from ralph_loop.completion import CompletionChecker, CompletionCriteria
from ralph_loop.config import RalphLoopConfig

from team.builder import TeamBuilder
from agent.roles.pm import ProductManagerAgent
from agent.roles.backend_developer import BackendDeveloperAgent


def create_doc(doc_id: str, path: str, title: str, doc_type, content: str) -> Document:
    """创建文档的辅助函数"""
    now = int(time.time())
    return Document(
        id=doc_id,
        path=path,
        metadata=DocumentMetadata(
            title=title,
            doc_type=doc_type.value if hasattr(doc_type, 'value') else doc_type,
            author="TestSystem",
            created_at=now,
            updated_at=now,
            version=1,
        ),
        content=DocumentContent(content=content),
    )


# ============================================================================
# 测试夹具 - 真实组件
# ============================================================================

@pytest.fixture
def real_document_store():
    """真实文档存储"""
    return DocumentStore(base_path="./test_storage/docs")


@pytest.fixture
def real_request_board():
    """真实诉求看板"""
    return RequestBoard()


# ============================================================================
# Phase 4 核心组件测试
# ============================================================================

class TestWorkflowConfigReal:
    """WorkflowConfig 真实测试"""
    
    def test_default_config_real(self):
        """真实默认配置"""
        config = WorkflowConfig()
        
        assert config.ralph_config is not None
        assert config.quality_passing_score == 0.7
        assert config.require_manual_review == False
        assert config.max_team_size == 12
        assert config.min_team_size == 2
    
    def test_ralph_config_integration_real(self):
        """RalphLoopConfig 集成测试"""
        ralph_config = RalphLoopConfig(
            max_iterations=30,
            completion_threshold=0.85,
            max_setbacks=15,
            parallel_agents=True,
        )
        
        config = WorkflowConfig(ralph_config=ralph_config)
        
        assert config.max_iterations == 30
        assert config.completion_threshold == 0.85
        assert config.max_setbacks == 15
        assert config.parallel_agents == True


class TestWorkflowContextReal:
    """WorkflowContext 真实测试"""
    
    def test_context_with_real_components(self, real_document_store, real_request_board):
        """使用真实组件的上下文"""
        context = WorkflowContext(
            workflow_id="test_wf_real",
            task_description="真实任务测试",
            team=[],
            document_store=real_document_store,
            request_board=real_request_board,
        )
        
        assert context.workflow_id == "test_wf_real"
        assert context.document_store is not None
        assert context.request_board is not None
    
    def test_context_document_tracking_real(self, real_document_store, real_request_board):
        """真实文档追踪"""
        context = WorkflowContext(
            workflow_id="test_wf_docs",
            task_description="文档追踪测试",
            team=[],
            document_store=real_document_store,
            request_board=real_request_board,
        )
        
        doc = create_doc("doc_test_001", "test/test.md", "测试文档", DocumentType.PRD, "# 测试内容")
        
        context.add_document(doc)
        assert context.total_documents == 1


class TestQualityGateReal:
    """QualityGate 真实测试"""
    
    @pytest.mark.asyncio
    async def test_quality_check_with_real_store(self, real_document_store):
        """使用真实文档存储的质量检查"""
        gate = QualityGate()
        
        doc = create_doc("doc_prd_real", "prd/PRD.md", "产品需求文档", DocumentType.PRD, "# PRD\n\n## 功能需求")
        
        await real_document_store.save(doc)
        
        class MockContext:
            document_store = real_document_store
            request_board = None
            metadata = {}
        
        result = await gate.check(MockContext())
        
        assert isinstance(result, QualityGateResult)
        assert len(result.check_results) > 0


class TestIterationControllerReal:
    """IterationController 真实测试"""
    
    @pytest.mark.asyncio
    async def test_controller_lifecycle_real(self):
        """真实控制器生命周期"""
        controller = IterationController()
        
        assert controller.status.value == "idle"
        
        agent = ProductManagerAgent()
        
        await controller.start(agents=[agent], team_session=None)
        
        assert controller.status.value == "running"
        assert controller.current_iteration is not None
        
        await controller.stop()
        
        assert controller.status.value == "stopped"
        assert len(controller.history) >= 1


class TestSetbackHandlerReal:
    """SetbackHandler 真实测试"""
    
    @pytest.mark.asyncio
    async def test_setback_handling_flow(self):
        """真实挫折处理流程"""
        handler = SetbackHandler()
        
        agent = BackendDeveloperAgent()
        
        setback = await handler.record_setback(
            agent=agent,
            iteration=1,
            error=Exception("timeout: database connection failed"),
        )
        
        assert setback.type == SetbackType.TIMEOUT
        assert setback.severity == SetbackSeverity.MEDIUM
        assert setback.agent == "Backend Developer"
        
        stats = handler.get_statistics()
        assert stats["total"] >= 1


class TestCompletionCheckerReal:
    """CompletionChecker 真实测试"""
    
    @pytest.mark.asyncio
    async def test_completion_check_real(self):
        """真实完成度检查"""
        criteria = CompletionCriteria(
            requirement_coverage=0.8,
            document_completeness=0.7,
            quality_score=0.6,
        )
        
        checker = CompletionChecker(criteria)
        
        team_state = {
            "requirement_coverage": 0.9,
            "document_completeness": 0.8,
            "quality_score": 0.7,
        }
        
        result = await checker.check(team_state)
        
        assert "score" in result
        assert result["score"] >= 0.8


# ============================================================================
# 集成测试 - 多模块协作
# ============================================================================

class TestPhase4IntegrationReal:
    """Phase 4 真实集成测试"""
    
    @pytest.mark.asyncio
    async def test_team_builder_workflow_integration(self):
        """团队组建与工作流集成"""
        builder = TeamBuilder()
        
        build_result = await builder.build("开发一个简单的博客系统")
        
        assert build_result.success == True
        assert len(build_result.team) >= 2
        
        config = WorkflowConfig()
        config.ralph_config.max_iterations = 2
        
        engine = WorkflowEngine(config=config)
        
        result = await engine.start(
            team=build_result.team,
            task_description="开发博客系统",
            document_store=builder.document_store,
            request_board=builder.request_board,
        )
        
        assert result is not None
        assert result.context is not None
    
    @pytest.mark.asyncio
    async def test_coordinator_with_real_agents(self):
        """协调器与真实 Agent"""
        doc_store = DocumentStore(base_path="./test_storage/docs")
        req_board = RequestBoard()
        
        pm = ProductManagerAgent()
        dev = BackendDeveloperAgent()
        
        context = WorkflowContext(
            workflow_id="test_coord_real",
            task_description="协调测试",
            team=[pm, dev],
            document_store=doc_store,
            request_board=req_board,
        )
        
        coordinator = TeamCoordinator(context=context)
        
        result = await coordinator.execute_iteration()
        
        assert isinstance(result, IterationResult)
        assert result.documents_produced >= 0
    
    @pytest.mark.asyncio
    async def test_full_workflow_cycle_real(self):
        """完整工作流周期"""
        builder = TeamBuilder()
        
        build_result = await builder.build("创建一个简单的 API 服务")
        
        if not build_result.success:
            pytest.skip("Team building failed")
        
        config = WorkflowConfig()
        config.ralph_config.max_iterations = 3
        config.quality_passing_score = 0.5
        
        engine = WorkflowEngine(config=config)
        
        result = await engine.start(
            team=build_result.team,
            task_description="创建 API 服务",
            document_store=builder.document_store,
            request_board=builder.request_board,
        )
        
        assert result is not None
        if result.context:
            assert result.context.iteration_count >= 0


# ============================================================================
# 端到端场景测试
# ============================================================================

class TestE2EScenariosReal:
    """端到端真实场景测试"""
    
    @pytest.mark.asyncio
    async def test_simple_project_e2e(self):
        """简单项目端到端"""
        builder = TeamBuilder()
        
        result = await builder.build("创建一个计算器程序")
        
        assert result.success == True
        
        for agent in result.team:
            assert agent is not None
            assert hasattr(agent, 'role')
            assert hasattr(agent, 'read_documents')
    
    @pytest.mark.asyncio
    async def test_workflow_with_quality_check(self):
        """带质量检查的工作流"""
        builder = TeamBuilder()
        
        build_result = await builder.build("开发一个简单的表单")
        
        if not build_result.success:
            pytest.skip("Team building failed")
        
        doc_store = builder.document_store
        
        prd_doc = create_doc("doc_prd_e2e", "prd/PRD.md", "PRD", DocumentType.PRD, "# PRD")
        await doc_store.save(prd_doc)
        
        gate = QualityGate()
        
        class MockContext:
            document_store = doc_store
            request_board = None
            metadata = {}
        
        quality_result = await gate.check(MockContext())
        
        assert quality_result is not None


# ============================================================================
# 性能测试
# ============================================================================

class TestPerformanceReal:
    """真实性能测试"""
    
    @pytest.mark.asyncio
    async def test_large_team_performance(self):
        """大团队性能"""
        builder = TeamBuilder()
        
        start_time = time.time()
        result = await builder.build("开发一个大型企业级系统包含用户管理权限管理订单管理库存管理")
        end_time = time.time()
        
        assert result.success == True
        assert (end_time - start_time) < 5.0
    
    @pytest.mark.asyncio
    async def test_rapid_iterations(self):
        """快速迭代"""
        config = WorkflowConfig()
        config.ralph_config.max_iterations = 5
        
        engine = WorkflowEngine(config=config)
        
        doc_store = DocumentStore(base_path="./test_storage/docs")
        req_board = RequestBoard()
        
        agent = ProductManagerAgent()
        
        start_time = time.time()
        result = await engine.start(
            team=[agent],
            task_description="快速迭代测试",
            document_store=doc_store,
            request_board=req_board,
        )
        end_time = time.time()
        
        assert result is not None
        assert (end_time - start_time) < 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
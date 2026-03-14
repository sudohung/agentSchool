"""Phase 4 工作流引擎测试."""

import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from workflow.config import WorkflowConfig
from workflow.context import WorkflowContext
from workflow.engine import WorkflowEngine, WorkflowResult
from workflow.coordinator import TeamCoordinator, IterationResult
from workflow.quality import (
    QualityGate,
    QualityGateResult,
    QualityCheckType,
)


class TestWorkflowConfig:
    """测试工作流配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = WorkflowConfig()
        
        assert config.ralph_config is not None
        assert config.quality_passing_score == 0.7
        assert config.require_manual_review == False
        assert config.max_team_size == 12
        assert config.min_team_size == 2
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = WorkflowConfig(
            quality_passing_score=0.8,
            require_manual_review=True,
        )
        
        assert config.quality_passing_score == 0.8
        assert config.require_manual_review == True
    
    def test_ralph_config_properties(self):
        """测试 Ralph Loop 配置代理属性"""
        config = WorkflowConfig()
        
        # 测试代理属性
        assert hasattr(config, 'max_iterations')
        assert hasattr(config, 'completion_threshold')
        assert hasattr(config, 'max_setbacks')
        assert hasattr(config, 'parallel_agents')


class TestWorkflowContext:
    """测试工作流上下文"""
    
    def test_context_creation(self):
        """测试上下文创建"""
        context = WorkflowContext(
            workflow_id="test_wf_001",
            task_description="测试任务",
            team=[],
            document_store=None,
            request_board=None,
        )
        
        assert context.workflow_id == "test_wf_001"
        assert context.task_description == "测试任务"
        assert context.status == "initialized"
        assert context.iteration_count == 0
    
    def test_context_methods(self):
        """测试上下文方法"""
        context = WorkflowContext(
            workflow_id="test_wf_002",
            task_description="测试任务",
            team=[],
            document_store=None,
            request_board=None,
        )
        
        # 测试 add_document
        context.add_document({"id": "doc1"})
        assert context.total_documents == 1
        
        # 测试 add_request
        context.add_request({"id": "req1"})
        assert context.total_requests == 1
        
        # 测试 record_setback
        context.record_setback()
        assert context.total_setbacks == 1
        
        # 测试 complete
        context.complete("test_completed")
        assert context.status == "completed"
        assert context.completion_reason == "test_completed"
        
        # 测试 fail
        context2 = WorkflowContext(
            workflow_id="test_wf_003",
            task_description="测试任务",
            team=[],
            document_store=None,
            request_board=None,
        )
        context2.fail("test_error")
        assert context2.status == "failed"
        assert context2.error == "test_error"


class TestQualityGate:
    """测试质量门控"""
    
    @pytest.mark.asyncio
    async def test_quality_gate_creation(self):
        """测试质量门控创建"""
        gate = QualityGate()
        
        assert gate.config is not None
        assert gate.config.passing_score == 0.7
    
    @pytest.mark.asyncio
    async def test_quality_check_result(self):
        """测试质量检查结果"""
        gate = QualityGate()
        
        # 创建模拟上下文
        class MockContext:
            document_store = None
            request_board = None
        
        context = MockContext()
        result = await gate.check(context)
        
        assert isinstance(result, QualityGateResult)
        assert hasattr(result, 'passed')
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'check_results')


class TestIterationResult:
    """测试迭代结果"""
    
    def test_iteration_result_creation(self):
        """测试迭代结果创建"""
        result = IterationResult(
            success=True,
            documents_produced=5,
            requests_processed=10,
            setbacks_count=0,
            errors=[],
        )
        
        assert result.success == True
        assert result.documents_produced == 5
        assert result.requests_processed == 10
        assert result.setbacks_count == 0
        assert len(result.errors) == 0


class TestWorkflowEngineBasic:
    """测试工作流引擎基础功能"""
    
    def test_engine_creation(self):
        """测试引擎创建"""
        engine = WorkflowEngine()
        
        assert engine.config is not None
        assert engine.status == "initialized"
        assert engine._running == False
    
    def test_engine_with_custom_config(self):
        """测试自定义配置引擎"""
        config = WorkflowConfig(
            quality_passing_score=0.8,
        )
        engine = WorkflowEngine(config=config)
        
        assert engine.config.quality_passing_score == 0.8


class TestCoordinatorBasic:
    """测试协调器基础功能"""
    
    def test_coordinator_creation(self):
        """测试协调器创建"""
        from workflow.context import WorkflowContext
        
        context = WorkflowContext(
            workflow_id="test_wf",
            task_description="测试",
            team=[],
            document_store=None,
            request_board=None,
        )
        
        coordinator = TeamCoordinator(context=context)
        
        assert coordinator.context == context
        assert coordinator._paused == False
        assert coordinator._stopped == False
    
    @pytest.mark.asyncio
    async def test_coordinator_stop(self):
        """测试协调器停止"""
        from workflow.context import WorkflowContext
        
        context = WorkflowContext(
            workflow_id="test_wf",
            task_description="测试",
            team=[],
            document_store=None,
            request_board=None,
        )
        
        coordinator = TeamCoordinator(context=context)
        
        # 测试停止
        await coordinator.stop()
        assert coordinator._stopped == True
        
        # 测试停止后执行迭代
        result = await coordinator.execute_iteration()
        assert result.success == False


class TestWorkflowIntegration:
    """工作流集成测试"""
    
    @pytest.mark.asyncio
    async def test_workflow_result_structure(self):
        """测试工作流结果结构"""
        from workflow.context import WorkflowContext
        
        context = WorkflowContext(
            workflow_id="test_wf",
            task_description="测试",
            team=[],
            document_store=None,
            request_board=None,
        )
        
        result = WorkflowResult(
            success=True,
            team=[],
            context=context,
        )
        
        assert result.success == True
        assert result.context == context
        assert result.error is None
        assert result.delivery_path is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
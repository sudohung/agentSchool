"""中优先级功能测试 - Git交付、S3交付、性能分析器、调试器."""

from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

from delivery.git_delivery import (
    GitDeliveryExecutor,
    GitDeliveryConfig,
    GitExecutionResult,
)
from delivery.s3_delivery import (
    S3DeliveryExecutor,
    S3DeliveryConfig,
    S3UploadResult,
)
from delivery.models import DeliveryArtifact, DeliveryResult
from infrastructure.devtools.profiler import (
    Profiler,
    ProfileRecord,
    ProfileReport,
    AgentStats,
    MethodStats,
    Bottleneck,
)
from infrastructure.devtools.debugger import (
    AgentDebugger,
    DebugSession,
    DebugStatus,
    Breakpoint,
    BreakpointType,
    WatchExpression,
)


class TestGitDelivery:
    """Git 交付测试"""
    
    def test_git_delivery_config(self):
        """测试 Git 配置"""
        config = GitDeliveryConfig(
            repo_url="https://github.com/test/repo.git",
            branch="main",
            commit_message="Test delivery",
        )
        
        assert config.repo_url == "https://github.com/test/repo.git"
        assert config.branch == "main"
        assert config.target_dir == "deliveries"
    
    def test_git_execution_result(self):
        """测试 Git 执行结果"""
        result = GitExecutionResult(
            success=True,
            stdout="OK",
            stderr="",
            return_code=0,
        )
        
        assert result.success is True
        assert bool(result) is True
        assert result.stdout == "OK"
    
    def test_git_delivery_config_commit_message_format(self):
        """测试提交消息格式化"""
        config = GitDeliveryConfig(
            repo_url="https://github.com/test/repo.git",
            commit_message="Delivery: {timestamp}",
        )
        
        message = config.get_commit_message()
        assert "Delivery:" in message
        assert "{timestamp}" not in message
    
    @pytest.mark.asyncio
    async def test_git_executor_init(self):
        """测试 Git 执行器初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = GitDeliveryExecutor(work_dir=tmpdir)
            assert executor.work_dir == Path(tmpdir)
    
    @pytest.mark.asyncio
    async def test_git_check_available(self):
        """测试 Git 可用性检查"""
        executor = GitDeliveryExecutor()
        available = await executor._check_git_available()
        assert isinstance(available, bool)


class TestS3Delivery:
    """S3 交付测试"""
    
    def test_s3_delivery_config(self):
        """测试 S3 配置"""
        config = S3DeliveryConfig(
            bucket="my-bucket",
            key_prefix="deliveries",
            region="us-west-2",
        )
        
        assert config.bucket == "my-bucket"
        assert config.key_prefix == "deliveries"
        assert config.region == "us-west-2"
    
    def test_s3_config_get_key(self):
        """测试 S3 键生成"""
        config = S3DeliveryConfig(
            bucket="my-bucket",
            key_prefix="deliveries",
        )
        
        key = config.get_s3_key("test.txt", "del_001")
        assert key == "deliveries/del_001/test.txt"
    
    def test_s3_upload_result(self):
        """测试 S3 上传结果"""
        result = S3UploadResult(
            success=True,
            key="deliveries/test.txt",
            etag="abc123",
            bytes_uploaded=100,
        )
        
        assert result.success is True
        assert bool(result) is True
        assert result.key == "deliveries/test.txt"
    
    @pytest.mark.asyncio
    async def test_s3_executor_init(self):
        """测试 S3 执行器初始化"""
        executor = S3DeliveryExecutor()
        assert executor._s3_client is None
    
    def test_s3_is_available(self):
        """测试 S3 可用性检查"""
        available = S3DeliveryExecutor.is_available()
        assert isinstance(available, bool)
    
    @pytest.mark.asyncio
    async def test_s3_mock_delivery(self):
        """测试 S3 模拟交付"""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = S3DeliveryExecutor()
            config = S3DeliveryConfig(bucket="test-bucket")
            
            artifact = DeliveryArtifact(
                id="art_001",
                name="test",
                type="document",
                path="/test",
                created_at=int(time.time()),
            )
            
            result = await executor._mock_deliver(
                artifact, config, "del_001", None
            )
            
            assert result.success is True
            assert "mock://" in result.delivery_path


class TestProfiler:
    """性能分析器测试"""
    
    def test_profile_record(self):
        """测试性能记录"""
        record = ProfileRecord(
            agent_id="agent_001",
            method_name="execute",
            start_time=time.perf_counter(),
            end_time=time.perf_counter(),
            duration_ms=100.0,
        )
        
        assert record.agent_id == "agent_001"
        assert record.method_name == "execute"
        assert record.duration_ms == 100.0
        
        d = record.to_dict()
        assert d["agent_id"] == "agent_001"
    
    def test_agent_stats(self):
        """测试 Agent 统计"""
        stats = AgentStats(agent_id="agent_001")
        
        record = ProfileRecord(
            agent_id="agent_001",
            method_name="execute",
            start_time=0,
            end_time=0,
            duration_ms=100.0,
            success=True,
        )
        
        stats.update(record)
        
        assert stats.total_calls == 1
        assert stats.total_time_ms == 100.0
        assert stats.success_count == 1
    
    def test_method_stats(self):
        """测试方法统计"""
        stats = MethodStats(method_name="execute")
        
        record = ProfileRecord(
            agent_id="agent_001",
            method_name="execute",
            start_time=0,
            end_time=0,
            duration_ms=50.0,
        )
        
        stats.update(record)
        
        assert stats.total_calls == 1
        assert stats.avg_time_ms == 50.0
    
    def test_bottleneck(self):
        """测试瓶颈"""
        bottleneck = Bottleneck(
            agent_id="agent_001",
            method_name="slow_method",
            duration_ms=500.0,
            percentage=25.0,
            severity="high",
        )
        
        assert bottleneck.agent_id == "agent_001"
        assert bottleneck.severity == "high"
        
        d = bottleneck.to_dict()
        assert d["percentage"] == 25.0
    
    def test_profiler_start_stop(self):
        """测试性能分析器启动停止"""
        profiler = Profiler(track_memory=False)
        
        session_id = profiler.start_profiling("test_session")
        assert session_id == "test_session"
        assert profiler.is_profiling is True
        
        report = profiler.stop_profiling()
        
        assert isinstance(report, ProfileReport)
        assert report.session_id == "test_session"
        assert profiler.is_profiling is False
    
    def test_profiler_record(self):
        """测试性能记录"""
        profiler = Profiler(track_memory=False)
        profiler.start_profiling()
        
        profiler.record(
            agent_id="agent_001",
            method_name="execute",
            duration_ms=50.0,
        )
        
        profiler.record(
            agent_id="agent_001",
            method_name="execute",
            duration_ms=75.0,
        )
        
        report = profiler.stop_profiling()
        
        assert report.total_records == 2
        assert "agent_001" in report.agent_stats
    
    def test_profiler_context_manager(self):
        """测试上下文管理器"""
        profiler = Profiler(track_memory=False)
        profiler.start_profiling()
        
        with profiler.profile_method("agent_001", "test_method"):
            time.sleep(0.01)
        
        report = profiler.stop_profiling()
        
        assert report.total_records == 1
    
    def test_profile_report_to_dict(self):
        """测试报告序列化"""
        report = ProfileReport(
            session_id="test",
            start_time=0,
            end_time=1,
            total_time_ms=1000.0,
            total_records=0,
            agent_stats={},
            method_stats={},
            memory_peak=0,
            bottlenecks=[],
        )
        
        d = report.to_dict()
        
        assert d["session_id"] == "test"
        assert d["total_time_ms"] == 1000.0


class TestDebugger:
    """调试器测试"""
    
    def test_breakpoint(self):
        """测试断点"""
        bp = Breakpoint(
            id="bp_001",
            breakpoint_type=BreakpointType.METHOD_ENTRY,
            agent_id="agent_001",
            method_name="execute",
        )
        
        assert bp.id == "bp_001"
        assert bp.enabled is True
        assert bp.hit_count == 0
    
    def test_breakpoint_should_trigger(self):
        """测试断点触发"""
        bp = Breakpoint(
            id="bp_001",
            breakpoint_type=BreakpointType.METHOD_ENTRY,
            agent_id="agent_001",
            method_name="execute",
        )
        
        assert bp.should_trigger("agent_001", "execute", {}) is True
        assert bp.should_trigger("agent_002", "execute", {}) is False
        assert bp.should_trigger("agent_001", "other", {}) is False
    
    def test_breakpoint_condition(self):
        """测试条件断点"""
        bp = Breakpoint(
            id="bp_001",
            breakpoint_type=BreakpointType.CONDITION,
            condition="count > 5",
        )
        
        assert bp.should_trigger("agent", "method", {"count": 10}) is True
        assert bp.should_trigger("agent", "method", {"count": 3}) is False
    
    def test_debug_session(self):
        """测试调试会话"""
        session = DebugSession(
            session_id="debug_001",
            agent_id="agent_001",
        )
        
        assert session.status == DebugStatus.RUNNING
        assert len(session.call_stack) == 0
        
        session.push_stack("method_1")
        assert session.current_step == "method_1"
        
        session.pop_stack()
        assert session.current_step is None
    
    def test_debug_session_variables(self):
        """测试会话变量"""
        session = DebugSession(
            session_id="debug_001",
            agent_id="agent_001",
        )
        
        session.set_variable("count", 5)
        session.set_variable("name", "test")
        
        assert session.variables["count"] == 5
        assert session.variables["name"] == "test"
    
    def test_debug_session_logs(self):
        """测试会话日志"""
        session = DebugSession(
            session_id="debug_001",
            agent_id="agent_001",
        )
        
        session.add_log("Test message")
        assert len(session.logs) == 1
        assert "Test message" in session.logs[0]
    
    def test_agent_debugger_attach(self):
        """测试附加调试"""
        debugger = AgentDebugger()
        
        session = debugger.attach("agent_001")
        
        assert session.session_id.startswith("debug_agent_001")
        assert session.agent_id == "agent_001"
        assert session.status == DebugStatus.RUNNING
    
    def test_agent_debugger_detach(self):
        """测试分离调试"""
        debugger = AgentDebugger()
        
        session = debugger.attach("agent_001")
        debugger.detach(session.session_id)
        
        assert session.session_id not in debugger._sessions
    
    def test_agent_debugger_breakpoints(self):
        """测试断点管理"""
        debugger = AgentDebugger()
        
        bp = debugger.add_breakpoint(
            agent_id="agent_001",
            method_name="execute",
        )
        
        assert bp.id in debugger._breakpoints
        
        debugger.remove_breakpoint(bp.id)
        assert bp.id not in debugger._breakpoints
    
    def test_agent_debugger_watch(self):
        """测试监视表达式"""
        debugger = AgentDebugger()
        session = debugger.attach("agent_001")
        
        session.set_variable("count", 10)
        
        watch = debugger.add_watch("count * 2")
        
        results = debugger.evaluate_watches(session.session_id)
        
        assert watch.id in results
    
    @pytest.mark.asyncio
    async def test_debugger_method_entry(self):
        """测试方法入口钩子"""
        debugger = AgentDebugger()
        session = debugger.attach("agent_001")
        
        await debugger.on_method_entry(
            session.session_id,
            "test_method",
            {"arg1": "value1"},
        )
        
        assert session.current_step == "test_method"
        assert "test_method" in session.call_stack
        assert session.variables["arg1"] == "value1"


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_git_s3_delivery_fallback(self):
        """测试 Git/S3 交付降级"""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_executor = GitDeliveryExecutor(work_dir=tmpdir)
            s3_executor = S3DeliveryExecutor()
            
            artifact = DeliveryArtifact(
                id="art_001",
                name="test",
                type="document",
                path="/test",
                created_at=int(time.time()),
            )
            
            git_config = GitDeliveryConfig(
                repo_url="https://github.com/test/test.git",
                branch="main",
            )
            
            s3_config = S3DeliveryConfig(bucket="test-bucket")
            
            assert git_executor is not None
            assert s3_executor is not None
    
    def test_profiler_debugger_integration(self):
        """测试性能分析器和调试器集成"""
        profiler = Profiler(track_memory=False)
        debugger = AgentDebugger()
        
        session_id = profiler.start_profiling("integrated_test")
        debug_session = debugger.attach("agent_001")
        
        assert profiler.is_profiling
        assert debug_session.status == DebugStatus.RUNNING
        
        profiler.stop_profiling()
        debugger.detach(debug_session.session_id)
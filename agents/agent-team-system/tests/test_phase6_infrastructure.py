"""Phase 6 基础设施模块集成测试."""

import pytest
import asyncio
import tempfile
from pathlib import Path

from infrastructure.exceptions import (
    InfrastructureError,
    MetricsCollectionError,
    ConfigValidationError,
    LogError,
)
from infrastructure.monitoring.types import MetricType, Metric, MetricSnapshot
from infrastructure.monitoring.metrics import MetricsCollector
from infrastructure.logging.config import LogLevel, LogConfig
from infrastructure.logging.logger import StructuredLogger, get_logger
from infrastructure.config.validators import ConfigValidator, ValidationError
from infrastructure.config.manager import SystemConfig, ConfigManager


# ============ 异常处理测试 ============

class TestExceptions:
    """测试异常处理"""
    
    def test_infrastructure_error_basic(self):
        """测试基础异常"""
        error = InfrastructureError("Test error")
        assert str(error) == "[INFRA_ERROR] Test error"
        assert error.code == "INFRA_ERROR"
    
    def test_infrastructure_error_with_details(self):
        """测试带详情的异常"""
        error = InfrastructureError(
            "Test error",
            code="TEST_ERROR",
            details={"key": "value"}
        )
        assert error.code == "TEST_ERROR"
        assert error.details == {"key": "value"}
    
    def test_metrics_error(self):
        """测试指标异常"""
        error = MetricsCollectionError("Collection failed")
        assert error.code == "METRICS_COLLECTION_ERROR"
    
    def test_config_validation_error(self):
        """测试配置验证异常"""
        error = ConfigValidationError(
            "Validation failed",
            errors=["error1", "error2"]
        )
        assert "error1" in str(error)
        assert "error2" in str(error)


# ============ 监控模块测试 ============

class TestMonitoring:
    """测试监控模块"""
    
    def test_metric_type_enum(self):
        """测试指标类型枚举"""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
    
    def test_metric_creation(self):
        """测试指标创建"""
        metric = Metric(
            name="test_metric",
            value=100.0,
            labels={"env": "test"}
        )
        assert metric.name == "test_metric"
        assert metric.value == 100.0
        assert metric.labels == {"env": "test"}
    
    def test_metric_validation(self):
        """测试指标验证"""
        with pytest.raises(Exception):
            Metric(name="", value=1.0)
        
        with pytest.raises(Exception):
            Metric(name="test", value=-1.0, metric_type=MetricType.COUNTER)
    
    @pytest.mark.asyncio
    async def test_metrics_collector_increment(self):
        """测试计数器增加"""
        collector = MetricsCollector(prefix="test")
        await collector.increment("requests", 1.0)
        await collector.increment("requests", 2.0)
        
        assert collector.get_counter("requests") == 3.0
    
    @pytest.mark.asyncio
    async def test_metrics_collector_gauge(self):
        """测试仪表值"""
        collector = MetricsCollector(prefix="test")
        await collector.gauge("memory", 512.0)
        
        assert collector.get_gauge("memory") == 512.0
        
        await collector.gauge("memory", 256.0)
        assert collector.get_gauge("memory") == 256.0
    
    @pytest.mark.asyncio
    async def test_metrics_collector_histogram(self):
        """测试直方图"""
        collector = MetricsCollector(prefix="test")
        await collector.histogram("response_time", 0.1)
        await collector.histogram("response_time", 0.2)
        await collector.histogram("response_time", 0.3)
        
        stats = collector.get_histogram_stats("response_time")
        assert stats["count"] == 3
        assert abs(stats["avg"] - 0.2) < 0.001  # 浮点数比较
    
    def test_metrics_export_prometheus(self):
        """测试 Prometheus 导出"""
        collector = MetricsCollector(prefix="ats")
        asyncio.run(collector.increment("requests", 10.0))
        asyncio.run(collector.gauge("memory", 1024.0))
        
        output = collector.export_prometheus()
        assert "ats_requests" in output
        assert "ats_memory" in output


# ============ 日志模块测试 ============

class TestLogging:
    """测试日志模块"""
    
    def test_log_level_enum(self):
        """测试日志级别枚举"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
    
    def test_log_level_from_string(self):
        """测试从字符串创建日志级别"""
        level = LogLevel.from_string("debug")
        assert level == LogLevel.DEBUG
        
        level = LogLevel.from_string("ERROR")
        assert level == LogLevel.ERROR
    
    def test_log_config_default(self):
        """测试默认日志配置"""
        config = LogConfig.default()
        assert config.level == LogLevel.INFO
        assert config.async_write == True
    
    def test_log_config_validation(self):
        """测试日志配置验证"""
        with pytest.raises(LogError):
            LogConfig(max_bytes=100)  # 小于 1MB
        
        with pytest.raises(LogError):
            LogConfig(backup_count=0)
    
    def test_structured_logger_creation(self):
        """测试日志记录器创建"""
        logger = StructuredLogger("test")
        assert logger.name == "test"
    
    def test_structured_logger_with_context(self):
        """测试上下文绑定"""
        logger = StructuredLogger("test")
        logger_with_agent = logger.with_agent("agent_001")
        
        assert logger_with_agent._context["agent_id"] == "agent_001"
        assert logger._context == {}  # 原 logger 不受影响
    
    def test_get_logger_convenience(self):
        """测试便捷函数"""
        logger = get_logger("test_convenience")
        assert isinstance(logger, StructuredLogger)


# ============ 配置模块测试 ============

class TestConfig:
    """测试配置模块"""
    
    def test_config_validator_not_empty(self):
        """测试非空验证"""
        error = ConfigValidator.validate_not_empty("", "field")
        assert error is not None
        assert error.field == "field"
        
        error = ConfigValidator.validate_not_empty("value", "field")
        assert error is None
    
    def test_config_validator_min(self):
        """测试最小值验证"""
        error = ConfigValidator.validate_min(0, 1, "count")
        assert error is not None
        assert "must be >= 1" in error.message
        
        error = ConfigValidator.validate_min(5, 1, "count")
        assert error is None
    
    def test_config_validator_port(self):
        """测试端口验证"""
        error = ConfigValidator.validate_port(0)
        assert error is not None
        
        error = ConfigValidator.validate_port(8080)
        assert error is None
        
        error = ConfigValidator.validate_port(70000)
        assert error is not None
    
    def test_system_config_default(self):
        """测试默认系统配置"""
        config = SystemConfig()
        assert config.app_name == "agent-team-system"
        assert config.max_agents == 20
        assert config.metrics_port == 9090
    
    def test_system_config_validation(self):
        """测试系统配置验证"""
        config = SystemConfig()
        config.max_agents = 0  # 无效值
        
        errors = config.validate()
        assert len(errors) > 0
    
    def test_config_manager_load_default(self):
        """测试配置管理器加载默认值"""
        manager = ConfigManager()
        config = manager.load()
        
        assert config.app_name == "agent-team-system"
        assert manager.is_loaded == True
    
    def test_config_manager_get_set(self):
        """测试配置读写"""
        manager = ConfigManager()
        manager.load()
        
        assert manager.get("max_agents") == 20
        manager.set("max_agents", 50)
        assert manager.get("max_agents") == 50
    
    @pytest.mark.asyncio
    async def test_config_manager_watch(self):
        """测试配置监听"""
        manager = ConfigManager()
        manager.load()
        
        notified = []
        
        def watcher(config):
            notified.append(config.max_agents)
        
        manager.watch(watcher)
        manager.set("max_agents", 100)
        
        await asyncio.sleep(0.1)  # 等待异步通知
        assert 100 in notified
    
    def test_config_from_env(self):
        """测试从环境变量加载"""
        import os
        os.environ["ATS_MAX_AGENTS"] = "99"
        
        manager = ConfigManager()
        config = manager.load()
        
        assert config.max_agents == 99
        
        del os.environ["ATS_MAX_AGENTS"]


# ============ 集成测试 ============

class TestIntegration:
    """集成测试"""
    
    def test_metrics_and_logging_integration(self):
        """测试监控和日志集成"""
        # 创建日志记录器
        logger = get_logger("integration_test")
        
        # 创建指标收集器
        collector = MetricsCollector(prefix="integration")
        
        # 记录日志和指标
        logger.info("Starting integration test")
        asyncio.run(collector.increment("test_counter", 1.0))
        
        # 验证
        assert collector.get_counter("test_counter") == 1.0
    
    def test_config_and_logging_integration(self):
        """测试配置和日志集成"""
        # 创建配置
        config = LogConfig(level=LogLevel.DEBUG)
        
        # 创建日志记录器
        logger = StructuredLogger("config_test", config)
        
        assert logger.config.level == LogLevel.DEBUG
    
    def test_full_infrastructure_stack(self):
        """测试完整基础设施栈"""
        # 1. 加载配置
        config_manager = ConfigManager()
        system_config = config_manager.load()
        
        # 2. 初始化日志
        log_config = LogConfig(level=LogLevel.INFO)
        logger = get_logger("full_stack", log_config)
        
        # 3. 初始化监控
        metrics = MetricsCollector(prefix="full")
        
        # 4. 执行操作
        logger.info("Full stack test started")
        asyncio.run(metrics.increment("operations", 1.0))
        
        # 5. 验证
        assert system_config.app_name == "agent-team-system"
        assert metrics.get_counter("operations") == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

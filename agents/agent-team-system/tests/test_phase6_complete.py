"""Phase 6 基础设施模块完整测试套件.

严格遵循 Phase 6 设计文档进行测试验证.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# 导入被测试模块
from infrastructure.exceptions import (
    InfrastructureError,
    MetricsError,
    MetricsCollectionError,
    MetricsExportError,
    MetricValidationError,
    LogError,
    LogWriteError,
    LogFormatError,
    ConfigurationError,
    ConfigLoadError,
    ConfigValidationError,
    DevToolsError,
    DebuggerError,
    CLIError,
    get_error_handling_strategy,
)

from infrastructure.monitoring.types import MetricType, Metric, MetricSnapshot
from infrastructure.monitoring.metrics import MetricsCollector, MetricRegistry

from infrastructure.logging.config import LogLevel, LogConfig
from infrastructure.logging.logger import (
    StructuredLogger,
    LoggerManager,
    LogRecord,
    get_logger,
    configure_logging,
)

from infrastructure.config.validators import ValidationError, ConfigValidator
from infrastructure.config.manager import SystemConfig, ConfigManager


# ============================================================
# 异常处理测试 (TC-EXC-001 到 TC-EXC-015)
# ============================================================

class TestExceptions:
    """异常处理测试"""
    
    def test_infrastructure_error_basic(self):
        """TC-EXC-001: 测试基础异常创建"""
        error = InfrastructureError("Test error message")
        assert str(error) == "[INFRA_ERROR] Test error message"
        assert error.code == "INFRA_ERROR"
        assert error.message == "Test error message"
        assert error.details == {}
    
    def test_infrastructure_error_with_code(self):
        """TC-EXC-002: 测试带错误码的异常"""
        error = InfrastructureError("Test error", code="CUSTOM_ERROR")
        assert error.code == "CUSTOM_ERROR"
    
    def test_infrastructure_error_with_details(self):
        """TC-EXC-003: 测试带详情的异常"""
        details = {"key": "value", "count": 42}
        error = InfrastructureError("Test error", details=details)
        assert error.details == details
    
    def test_metrics_error_hierarchy(self):
        """TC-EXC-004: 测试指标异常层次结构"""
        error = MetricsCollectionError("Collection failed")
        assert isinstance(error, MetricsError)
        assert isinstance(error, InfrastructureError)
        assert error.code == "METRICS_COLLECTION_ERROR"
    
    def test_metrics_export_error(self):
        """TC-EXC-005: 测试指标导出异常"""
        error = MetricsExportError("Export failed")
        assert error.code == "METRICS_EXPORT_ERROR"
    
    def test_log_error_hierarchy(self):
        """TC-EXC-006: 测试日志异常层次结构"""
        error = LogWriteError("Write failed")
        assert isinstance(error, LogError)
        assert isinstance(error, InfrastructureError)
        assert error.code == "LOG_WRITE_ERROR"
    
    def test_config_validation_error_with_list(self):
        """TC-EXC-007: 测试配置验证异常（带错误列表）"""
        errors = ["Field A is invalid", "Field B is missing"]
        error = ConfigValidationError("Validation failed", errors=errors)
        assert error.code == "CONFIG_VALIDATION_ERROR"
        assert error.errors == errors
        assert "Field A is invalid" in str(error)
    
    def test_devtools_error_hierarchy(self):
        """TC-EXC-008: 测试开发工具异常层次结构"""
        error = DebuggerError("Debug failed")
        assert isinstance(error, DevToolsError)
        assert isinstance(error, InfrastructureError)
        assert error.code == "DEBUGGER_ERROR"
    
    def test_cli_error(self):
        """TC-EXC-009: 测试 CLI 异常"""
        error = CLIError("Command failed")
        assert error.code == "CLI_ERROR"
    
    def test_error_handling_strategy_metrics_collection(self):
        """TC-EXC-010: 测试 MetricsCollectionError 处理策略"""
        error = MetricsCollectionError("Test")
        strategy = get_error_handling_strategy(error)
        assert strategy["strategy"] == "log_and_continue"
        assert strategy["retry"] == False
    
    def test_error_handling_strategy_metrics_export(self):
        """TC-EXC-011: 测试 MetricsExportError 处理策略"""
        error = MetricsExportError("Test")
        strategy = get_error_handling_strategy(error)
        assert strategy["strategy"] == "cache_and_retry"
        assert strategy["retry"] == True
        assert strategy["max_retries"] == 3
    
    def test_error_handling_strategy_log_write(self):
        """TC-EXC-012: 测试 LogWriteError 处理策略"""
        error = LogWriteError("Test")
        strategy = get_error_handling_strategy(error)
        assert strategy["strategy"] == "fallback_handler"
        assert strategy["retry"] == False
    
    def test_error_handling_strategy_config_load(self):
        """TC-EXC-013: 测试 ConfigLoadError 处理策略"""
        error = ConfigLoadError("Test")
        strategy = get_error_handling_strategy(error)
        assert strategy["strategy"] == "use_defaults"
        assert strategy["retry"] == False
    
    def test_error_handling_strategy_config_validation(self):
        """TC-EXC-014: 测试 ConfigValidationError 处理策略"""
        error = ConfigValidationError("Test")
        strategy = get_error_handling_strategy(error)
        assert strategy["strategy"] == "prevent_startup"
        assert strategy["retry"] == False
    
    def test_error_handling_strategy_unknown(self):
        """TC-EXC-015: 测试未知异常处理策略"""
        error = Exception("Unknown error")
        strategy = get_error_handling_strategy(error)
        assert strategy["strategy"] == "log_and_continue"
        assert strategy["retry"] == False


# ============================================================
# 监控模块测试 (TC-MET-001 到 TC-MET-020)
# ============================================================

class TestMonitoringTypes:
    """监控类型测试"""
    
    def test_metric_type_enum_values(self):
        """TC-MET-001: 测试 MetricType 枚举值"""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"
    
    def test_metric_creation(self):
        """TC-MET-002: 测试 Metric 创建"""
        metric = Metric(
            name="test_metric",
            value=100.0,
            labels={"env": "test"}
        )
        assert metric.name == "test_metric"
        assert metric.value == 100.0
        assert metric.labels == {"env": "test"}
        assert metric.metric_type == MetricType.GAUGE
        assert metric.timestamp > 0
    
    def test_metric_to_dict(self):
        """TC-MET-003: 测试 Metric 转换为字典"""
        metric = Metric(name="test", value=42.0)
        data = metric.to_dict()
        assert data["name"] == "test"
        assert data["value"] == 42.0
        assert data["type"] == "gauge"
    
    def test_metric_with_label(self):
        """TC-MET-004: 测试 Metric 添加标签"""
        metric = Metric(name="test", value=1.0)
        metric.with_label("key", "value")
        assert metric.labels["key"] == "value"
    
    def test_metric_validation_empty_name(self):
        """TC-MET-005: 测试 Metric 名称验证（空名称）"""
        with pytest.raises(MetricValidationError) as exc_info:
            Metric(name="", value=1.0)
        assert "non-empty string" in str(exc_info.value)
    
    def test_metric_validation_invalid_value(self):
        """TC-MET-006: 测试 Metric 值验证（无效类型）"""
        with pytest.raises(MetricValidationError) as exc_info:
            Metric(name="test", value="invalid")
        assert "must be a number" in str(exc_info.value)
    
    def test_metric_validation_negative_counter(self):
        """TC-MET-007: 测试 Counter 负值验证"""
        with pytest.raises(MetricValidationError) as exc_info:
            Metric(name="test", value=-1.0, metric_type=MetricType.COUNTER)
        assert "cannot be negative" in str(exc_info.value)
    
    def test_metric_snapshot_creation(self):
        """TC-MET-008: 测试 MetricSnapshot 创建"""
        snapshot = MetricSnapshot()
        assert snapshot.metrics == []
        assert snapshot.timestamp > 0
    
    def test_metric_snapshot_add(self):
        """TC-MET-009: 测试 MetricSnapshot 添加指标"""
        snapshot = MetricSnapshot()
        metric = Metric(name="test", value=1.0)
        snapshot.add(metric)
        assert len(snapshot.metrics) == 1
    
    def test_metric_snapshot_to_prometheus(self):
        """TC-MET-010: 测试 Prometheus 格式导出"""
        snapshot = MetricSnapshot()
        snapshot.add(Metric(name="counter1", value=10.0, metric_type=MetricType.COUNTER))
        snapshot.add(Metric(name="gauge1", value=5.0, metric_type=MetricType.GAUGE))
        
        output = snapshot.to_prometheus()
        assert "# TYPE counter1 counter" in output
        assert "counter1 10.0" in output
        assert "# TYPE gauge1 gauge" in output
        assert "gauge1 5.0" in output


class TestMetricsCollector:
    """MetricsCollector 测试"""
    
    @pytest.mark.asyncio
    async def test_increment(self):
        """TC-MET-011: 测试计数器增加"""
        collector = MetricsCollector(prefix="test")
        await collector.increment("requests", 1.0)
        await collector.increment("requests", 2.0)
        assert collector.get_counter("requests") == 3.0
    
    @pytest.mark.asyncio
    async def test_increment_with_labels(self):
        """TC-MET-012: 测试带标签的计数器增加"""
        collector = MetricsCollector(prefix="test")
        await collector.increment("requests", 1.0, labels={"method": "GET"})
        await collector.increment("requests", 1.0, labels={"method": "POST"})
        assert collector.get_counter("requests", labels={"method": "GET"}) == 1.0
        assert collector.get_counter("requests", labels={"method": "POST"}) == 1.0
    
    @pytest.mark.asyncio
    async def test_decrement(self):
        """TC-MET-013: 测试计数器减少"""
        collector = MetricsCollector(prefix="test")
        await collector.gauge("temperature", 100.0)
        await collector.decrement("temperature", 10.0)
        assert collector.get_gauge("temperature") == 90.0
    
    @pytest.mark.asyncio
    async def test_gauge(self):
        """TC-MET-014: 测试仪表值设置"""
        collector = MetricsCollector(prefix="test")
        await collector.gauge("memory", 512.0)
        assert collector.get_gauge("memory") == 512.0
        
        await collector.gauge("memory", 256.0)
        assert collector.get_gauge("memory") == 256.0
    
    @pytest.mark.asyncio
    async def test_histogram(self):
        """TC-MET-015: 测试直方图记录"""
        collector = MetricsCollector(prefix="test")
        await collector.histogram("response_time", 0.1)
        await collector.histogram("response_time", 0.2)
        await collector.histogram("response_time", 0.3)
        
        stats = collector.get_histogram_stats("response_time")
        assert stats["count"] == 3
        assert abs(stats["avg"] - 0.2) < 0.001
        assert stats["min"] == 0.1
        assert stats["max"] == 0.3
    
    @pytest.mark.asyncio
    async def test_summary(self):
        """TC-MET-016: 测试摘要记录"""
        collector = MetricsCollector(prefix="test")
        await collector.summary("request_size", 100.0)
        await collector.summary("request_size", 200.0)
        
        # 验证内部存储
        full_name = collector._make_full_name("request_size")
        assert len(collector._registry.summaries[full_name]) == 2
    
    def test_create_snapshot(self):
        """TC-MET-017: 测试创建指标快照"""
        collector = MetricsCollector(prefix="test")
        asyncio.run(collector.increment("counter1", 10.0))
        asyncio.run(collector.gauge("gauge1", 5.0))
        
        snapshot = collector.create_snapshot()
        assert len(snapshot.metrics) >= 2
    
    def test_export_prometheus(self):
        """TC-MET-018: 测试 Prometheus 格式导出"""
        collector = MetricsCollector(prefix="ats")
        asyncio.run(collector.increment("requests", 100.0))
        asyncio.run(collector.gauge("memory", 1024.0))
        
        output = collector.export_prometheus()
        assert "ats_requests" in output
        assert "ats_memory" in output
        assert "# TYPE ats_requests counter" in output
        assert "# TYPE ats_memory gauge" in output
    
    def test_export_json(self):
        """TC-MET-019: 测试 JSON 格式导出"""
        collector = MetricsCollector(prefix="test")
        asyncio.run(collector.increment("counter1", 10.0))
        asyncio.run(collector.gauge("gauge1", 5.0))
        
        data = collector.export_json()
        assert "timestamp" in data
        assert "counters" in data
        assert "gauges" in data
        assert data["counters"]["test_counter1"] == 10.0
        assert data["gauges"]["test_gauge1"] == 5.0
    
    def test_reset(self):
        """TC-MET-020: 测试重置指标"""
        collector = MetricsCollector(prefix="test")
        asyncio.run(collector.increment("counter1", 10.0))
        assert collector.get_counter("counter1") == 10.0
        
        collector.reset()
        assert collector.get_counter("counter1") == 0.0


# ============================================================
# 日志模块测试 (TC-LOG-001 到 TC-LOG-020)
# ============================================================

class TestLogLevel:
    """日志级别测试"""
    
    def test_log_level_enum_values(self):
        """TC-LOG-001: 测试 LogLevel 枚举值"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"
    
    def test_log_level_from_string(self):
        """TC-LOG-002: 测试从字符串创建日志级别"""
        assert LogLevel.from_string("debug") == LogLevel.DEBUG
        assert LogLevel.from_string("INFO") == LogLevel.INFO
        assert LogLevel.from_string("Warning") == LogLevel.WARNING
    
    def test_log_level_from_string_invalid(self):
        """TC-LOG-003: 测试无效的日志级别字符串"""
        with pytest.raises(LogError) as exc_info:
            LogLevel.from_string("invalid")
        assert "Invalid log level" in str(exc_info.value)
    
    def test_log_level_to_int(self):
        """TC-LOG-004: 测试日志级别转整数"""
        assert LogLevel.DEBUG.to_int() == 10
        assert LogLevel.INFO.to_int() == 20
        assert LogLevel.WARNING.to_int() == 30
        assert LogLevel.ERROR.to_int() == 40
        assert LogLevel.CRITICAL.to_int() == 50


class TestLogConfig:
    """日志配置测试"""
    
    def test_default_config(self):
        """TC-LOG-005: 测试默认配置"""
        config = LogConfig.default()
        assert config.level == LogLevel.INFO
        assert config.async_write == True
        assert config.handlers == ["console"]
    
    def test_development_config(self):
        """TC-LOG-006: 测试开发环境配置"""
        config = LogConfig.development()
        assert config.level == LogLevel.DEBUG
        assert config.async_write == False
        assert config.handlers == ["console"]
    
    def test_production_config(self):
        """TC-LOG-007: 测试生产环境配置"""
        config = LogConfig.production()
        assert config.level == LogLevel.INFO
        assert config.handlers == ["console", "file"]
        assert config.file_path == "logs/app.log"
        assert config.json_format == True
    
    def test_config_validation_max_bytes_too_small(self):
        """TC-LOG-008: 测试 max_bytes 验证（太小）"""
        with pytest.raises(LogError) as exc_info:
            LogConfig(max_bytes=100)
        assert "at least 1MB" in str(exc_info.value)
    
    def test_config_validation_backup_count_zero(self):
        """TC-LOG-009: 测试 backup_count 验证（为0）"""
        with pytest.raises(LogError) as exc_info:
            LogConfig(backup_count=0)
        assert "at least 1" in str(exc_info.value)
    
    def test_config_to_dict(self):
        """TC-LOG-010: 测试配置转字典"""
        config = LogConfig(level=LogLevel.DEBUG)
        data = config.to_dict()
        assert data["level"] == "DEBUG"
        assert data["async_write"] == True
    
    def test_config_from_dict(self):
        """TC-LOG-011: 测试从字典创建配置"""
        data = {"level": "WARNING", "max_bytes": 20 * 1024 * 1024}
        config = LogConfig.from_dict(data)
        assert config.level == LogLevel.WARNING
        assert config.max_bytes == 20 * 1024 * 1024
    
    def test_config_merge(self):
        """TC-LOG-012: 测试配置合并"""
        base = LogConfig(level=LogLevel.INFO)
        override = LogConfig(level=LogLevel.DEBUG, max_bytes=50 * 1024 * 1024)
        merged = base.merge(override)
        assert merged.level == LogLevel.DEBUG
        assert merged.max_bytes == 50 * 1024 * 1024


class TestStructuredLogger:
    """结构化日志记录器测试"""
    
    def test_logger_creation(self):
        """TC-LOG-013: 测试日志记录器创建"""
        logger = StructuredLogger("test_logger")
        assert logger.name == "test_logger"
    
    def test_logger_with_context(self):
        """TC-LOG-014: 测试上下文绑定"""
        logger = StructuredLogger("test")
        logger_with_context = logger.with_context(request_id="123", user_id="456")
        
        assert logger_with_context._context["request_id"] == "123"
        assert logger_with_context._context["user_id"] == "456"
        assert logger._context == {}  # 原 logger 不受影响
    
    def test_logger_with_agent(self):
        """TC-LOG-015: 测试 Agent ID 绑定"""
        logger = StructuredLogger("test")
        logger_with_agent = logger.with_agent("agent_001")
        assert logger_with_agent._context["agent_id"] == "agent_001"
    
    def test_logger_with_workflow(self):
        """TC-LOG-016: 测试 Workflow ID 绑定"""
        logger = StructuredLogger("test")
        logger_with_workflow = logger.with_workflow("wf_001")
        assert logger_with_workflow._context["workflow_id"] == "wf_001"
    
    def test_logger_sanitize_sensitive_fields(self):
        """TC-LOG-017: 测试敏感信息脱敏"""
        config = LogConfig(sensitive_fields=["password", "token"])
        logger = StructuredLogger("test", config)
        
        data = {"username": "admin", "password": "secret123", "token": "abc"}
        sanitized = logger._sanitize(data)
        
        assert sanitized["username"] == "admin"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"
    
    def test_logger_manager_singleton(self):
        """TC-LOG-018: 测试 LoggerManager 单例"""
        manager1 = LoggerManager()
        manager2 = LoggerManager()
        assert manager1 is manager2
    
    def test_get_logger_convenience(self):
        """TC-LOG-019: 测试 get_logger 便捷函数"""
        logger = get_logger("test_convenience")
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test_convenience"
    
    def test_configure_logging(self):
        """TC-LOG-020: 测试配置日志系统"""
        config = LogConfig(level=LogLevel.WARNING)
        configure_logging(config)
        
        # 验证配置已应用
        logger = get_logger("test_config")
        assert logger.config.level == LogLevel.WARNING


# ============================================================
# 配置模块测试 (TC-CFG-001 到 TC-CFG-020)
# ============================================================

class TestConfigValidator:
    """配置验证器测试"""
    
    def test_validate_not_empty(self):
        """TC-CFG-001: 测试非空验证"""
        assert ConfigValidator.validate_not_empty("value", "field") is None
        error = ConfigValidator.validate_not_empty("", "field")
        assert error is not None
        assert error.field == "field"
    
    def test_validate_min(self):
        """TC-CFG-002: 测试最小值验证"""
        assert ConfigValidator.validate_min(5, 1, "count") is None
        error = ConfigValidator.validate_min(0, 1, "count")
        assert error is not None
        assert "must be >= 1" in error.message
    
    def test_validate_max(self):
        """TC-CFG-003: 测试最大值验证"""
        assert ConfigValidator.validate_max(5, 10, "count") is None
        error = ConfigValidator.validate_max(15, 10, "count")
        assert error is not None
        assert "must be <= 10" in error.message
    
    def test_validate_range(self):
        """TC-CFG-004: 测试范围验证"""
        assert ConfigValidator.validate_range(5, 1, 10, "value") is None
        error = ConfigValidator.validate_range(15, 1, 10, "value")
        assert error is not None
    
    def test_validate_port(self):
        """TC-CFG-005: 测试端口验证"""
        assert ConfigValidator.validate_port(8080) is None
        assert ConfigValidator.validate_port(1) is None
        assert ConfigValidator.validate_port(65535) is None
        
        error = ConfigValidator.validate_port(0)
        assert error is not None
        
        error = ConfigValidator.validate_port(70000)
        assert error is not None
    
    def test_validate_positive(self):
        """TC-CFG-006: 测试正数验证"""
        assert ConfigValidator.validate_positive(5, "count") is None
        error = ConfigValidator.validate_positive(0, "count")
        assert error is not None
    
    def test_validate_in_choices(self):
        """TC-CFG-007: 测试选项验证"""
        choices = ["a", "b", "c"]
        assert ConfigValidator.validate_in_choices("a", choices, "field") is None
        error = ConfigValidator.validate_in_choices("d", choices, "field")
        assert error is not None
    
    def test_validate_pattern(self):
        """TC-CFG-008: 测试正则验证"""
        assert ConfigValidator.validate_pattern("abc123", r"^[a-z0-9]+$", "field") is None
        error = ConfigValidator.validate_pattern("ABC", r"^[a-z0-9]+$", "field")
        assert error is not None
    
    def test_validate_url(self):
        """TC-CFG-009: 测试 URL 验证"""
        assert ConfigValidator.validate_url("https://example.com") is None
        assert ConfigValidator.validate_url("http://localhost:8080") is None
        error = ConfigValidator.validate_url("not-a-url")
        assert error is not None
    
    def test_validate_file_path(self):
        """TC-CFG-010: 测试文件路径验证"""
        assert ConfigValidator.validate_file_path("/path/to/file.txt") is None
        assert ConfigValidator.validate_file_path("relative/path") is None


class TestSystemConfig:
    """系统配置测试"""
    
    def test_default_config(self):
        """TC-CFG-011: 测试默认配置"""
        config = SystemConfig()
        assert config.app_name == "agent-team-system"
        assert config.max_agents == 20
        assert config.max_iterations == 10
        assert config.metrics_port == 9090
    
    def test_validate_max_agents(self):
        """TC-CFG-012: 测试 max_agents 验证"""
        config = SystemConfig(max_agents=0)
        errors = config.validate()
        assert any(e.field == "max_agents" for e in errors)
    
    def test_validate_max_iterations(self):
        """TC-CFG-013: 测试 max_iterations 验证"""
        config = SystemConfig(max_iterations=0)
        errors = config.validate()
        assert any(e.field == "max_iterations" for e in errors)
    
    def test_validate_metrics_port(self):
        """TC-CFG-014: 测试 metrics_port 验证"""
        config = SystemConfig(metrics_port=0)
        errors = config.validate()
        assert any(e.field == "metrics_port" for e in errors)
    
    def test_validate_valid_config(self):
        """TC-CFG-015: 测试有效配置"""
        config = SystemConfig()
        errors = config.validate()
        assert len(errors) == 0


class TestConfigManager:
    """配置管理器测试"""
    
    def test_load_default_config(self):
        """TC-CFG-016: 测试加载默认配置"""
        manager = ConfigManager()
        config = manager.load()
        
        assert config.app_name == "agent-team-system"
        assert manager.is_loaded == True
    
    def test_get_config_value(self):
        """TC-CFG-017: 测试获取配置值"""
        manager = ConfigManager()
        manager.load()
        
        assert manager.get("max_agents") == 20
        assert manager.get("nonexistent", "default") == "default"
    
    def test_set_config_value(self):
        """TC-CFG-018: 测试设置配置值"""
        manager = ConfigManager()
        manager.load()
        
        manager.set("max_agents", 50)
        assert manager.get("max_agents") == 50
    
    def test_config_manager_watch(self):
        """TC-CFG-019: 测试配置监听"""
        manager = ConfigManager()
        manager.load()
        
        notified_values = []
        def watcher(config):
            notified_values.append(config.max_agents)
        
        manager.watch(watcher)
        manager.set("max_agents", 100)
        
        assert 100 in notified_values
    
    def test_load_from_env(self):
        """TC-CFG-020: 测试从环境变量加载"""
        os.environ["ATS_MAX_AGENTS"] = "99"
        
        try:
            manager = ConfigManager()
            config = manager.load()
            assert config.max_agents == 99
        finally:
            del os.environ["ATS_MAX_AGENTS"]


# ============================================================
# 集成测试 (TC-INT-001 到 TC-INT-010)
# ============================================================

class TestIntegration:
    """集成测试"""
    
    def test_metrics_and_logging_integration(self):
        """TC-INT-001: 测试监控和日志集成"""
        logger = get_logger("integration_test")
        collector = MetricsCollector(prefix="integration")
        
        logger.info("Starting integration test")
        asyncio.run(collector.increment("test_counter", 1.0))
        
        assert collector.get_counter("test_counter") == 1.0
    
    def test_config_and_logging_integration(self):
        """TC-INT-002: 测试配置和日志集成"""
        config = LogConfig(level=LogLevel.DEBUG)
        logger = StructuredLogger("config_test", config)
        
        assert logger.config.level == LogLevel.DEBUG
    
    def test_full_infrastructure_stack(self):
        """TC-INT-003: 测试完整基础设施栈"""
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
    
    def test_error_handling_integration(self):
        """TC-INT-004: 测试错误处理集成"""
        error = MetricsCollectionError("Test error")
        strategy = get_error_handling_strategy(error)
        
        assert strategy["strategy"] == "log_and_continue"
        logger = get_logger("error_test")
        logger.error(f"Error occurred: {error}")
    
    def test_config_reload_integration(self):
        """TC-INT-005: 测试配置重载集成"""
        manager = ConfigManager()
        manager.load()
        
        initial_value = manager.get("max_agents")
        manager.set("max_agents", initial_value + 10)
        
        assert manager.get("max_agents") == initial_value + 10
    
    def test_metrics_snapshot_and_export(self):
        """TC-INT-006: 测试指标快照和导出集成"""
        collector = MetricsCollector(prefix="test")
        asyncio.run(collector.increment("counter1", 10.0))
        asyncio.run(collector.gauge("gauge1", 5.0))
        
        # 创建快照
        snapshot = collector.create_snapshot()
        assert len(snapshot.metrics) >= 2
        
        # 导出 Prometheus
        prometheus_output = collector.export_prometheus()
        assert "test_counter1" in prometheus_output
        
        # 导出 JSON
        json_output = collector.export_json()
        assert json_output["counters"]["test_counter1"] == 10.0
    
    def test_logger_context_propagation(self):
        """TC-INT-007: 测试日志上下文传播"""
        logger = get_logger("context_test")
        logger_with_agent = logger.with_agent("agent_001")
        logger_with_workflow = logger_with_agent.with_workflow("wf_001")
        
        assert logger_with_workflow._context["agent_id"] == "agent_001"
        assert logger_with_workflow._context["workflow_id"] == "wf_001"
    
    def test_config_validation_prevents_invalid_values(self):
        """TC-INT-008: 测试配置验证阻止无效值"""
        config = SystemConfig(max_agents=-1)
        errors = config.validate()
        
        assert len(errors) > 0
        assert any(e.field == "max_agents" for e in errors)
    
    def test_sensitive_data_sanitization(self):
        """TC-INT-009: 测试敏感数据脱敏"""
        config = LogConfig(sensitive_fields=["password"])
        logger = StructuredLogger("sanitize_test", config)
        
        data = {"username": "admin", "password": "secret"}
        sanitized = logger._sanitize(data)
        
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["username"] == "admin"
    
    def test_async_metrics_collection(self):
        """TC-INT-010: 测试异步指标收集"""
        collector = MetricsCollector(prefix="async")
        
        async def collect_metrics():
            await collector.increment("counter", 1.0)
            await collector.gauge("gauge", 100.0)
            await collector.histogram("hist", 0.5)
        
        asyncio.run(collect_metrics())
        
        assert collector.get_counter("counter") == 1.0
        assert collector.get_gauge("gauge") == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""基础设施异常处理模块."""

from typing import Dict, List, Any, Optional


class InfrastructureError(Exception):
    """基础设施异常基类"""
    
    code = "INFRA_ERROR"
    
    def __init__(self, message: str, code: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.code
        self.details = details or {}
    
    def __str__(self):
        return f"[{self.code}] {self.message}"


# ============ 监控系统异常 ============

class MetricsError(InfrastructureError):
    """指标收集异常"""
    code = "METRICS_ERROR"


class MetricsCollectionError(MetricsError):
    """指标收集失败"""
    code = "METRICS_COLLECTION_ERROR"


class MetricsExportError(MetricsError):
    """指标导出失败"""
    code = "METRICS_EXPORT_ERROR"


class MetricValidationError(MetricsError):
    """指标验证失败"""
    code = "METRIC_VALIDATION_ERROR"
    
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


# ============ 日志系统异常 ============

class LogError(InfrastructureError):
    """日志系统异常"""
    code = "LOG_ERROR"
    
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


class LogWriteError(LogError):
    """日志写入失败"""
    code = "LOG_WRITE_ERROR"


class LogFormatError(LogError):
    """日志格式错误"""
    code = "LOG_FORMAT_ERROR"


class LogHandlerError(LogError):
    """日志处理器错误"""
    code = "LOG_HANDLER_ERROR"


# ============ 配置管理异常 ============

class ConfigurationError(InfrastructureError):
    """配置异常"""
    code = "CONFIG_ERROR"


class ConfigLoadError(ConfigurationError):
    """配置加载失败"""
    code = "CONFIG_LOAD_ERROR"


class ConfigSaveError(ConfigurationError):
    """配置保存失败"""
    code = "CONFIG_SAVE_ERROR"


class ConfigValidationError(ConfigurationError):
    """配置验证失败"""
    code = "CONFIG_VALIDATION_ERROR"
    
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []
    
    def __str__(self):
        if self.errors:
            return f"[{self.code}] {self.message}: {'; '.join(self.errors)}"
        return f"[{self.code}] {self.message}"


# ============ 开发工具异常 ============

class DevToolsError(InfrastructureError):
    """开发工具异常"""
    code = "DEVTOOLS_ERROR"


class DebuggerError(DevToolsError):
    """调试器异常"""
    code = "DEBUGGER_ERROR"


class CLIError(DevToolsError):
    """CLI 工具异常"""
    code = "CLI_ERROR"


class ProfilerError(DevToolsError):
    """性能分析器异常"""
    code = "PROFILER_ERROR"


# ============ 错误处理策略 ============

ERROR_HANDLING_STRATEGIES = {
    MetricsCollectionError.__name__: {
        "strategy": "log_and_continue",
        "retry": False,
    },
    MetricsExportError.__name__: {
        "strategy": "cache_and_retry",
        "retry": True,
        "max_retries": 3,
    },
    LogWriteError.__name__: {
        "strategy": "fallback_handler",
        "retry": False,
    },
    ConfigLoadError.__name__: {
        "strategy": "use_defaults",
        "retry": False,
    },
    ConfigValidationError.__name__: {
        "strategy": "prevent_startup",
        "retry": False,
    },
}


def get_error_handling_strategy(error: Exception) -> Dict[str, Any]:
    """获取错误处理策略"""
    error_name = error.__class__.__name__
    return ERROR_HANDLING_STRATEGIES.get(error_name, {
        "strategy": "log_and_continue",
        "retry": False,
    })

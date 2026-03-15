"""结构化日志记录器."""

import logging
import time
import json
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextlib import contextmanager

from infrastructure.logging.config import LogConfig, LogLevel
from infrastructure.exceptions import LogError, LogWriteError


@dataclass
class LogRecord:
    """日志记录"""
    
    timestamp: int
    level: str
    message: str
    logger_name: str
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "logger": self.logger_name,
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            **self.extra
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class StructuredLogger:
    """
    结构化日志记录器
    
    支持上下文绑定、异步写入、敏感信息脱敏
    """
    
    def __init__(self, name: str, config: Optional[LogConfig] = None):
        """
        初始化日志记录器
        
        Args:
            name: 日志名称
            config: 日志配置
        """
        self.name = name
        self.config = config or LogConfig()
        self._context: Dict[str, Any] = {}
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置 Python 标准日志器"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.config.level.value)
        
        # 清除现有 handlers
        logger.handlers.clear()
        
        # 添加 handlers
        for handler_name in self.config.handlers:
            if handler_name == "console":
                handler = logging.StreamHandler()
            elif handler_name == "file" and self.config.file_path:
                handler = logging.FileHandler(self.config.file_path)
            else:
                continue
            
            # 设置格式
            if self.config.json_format:
                formatter = logging.Formatter(
                    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
                )
            else:
                formatter = logging.Formatter(
                    self.config.format,
                    datefmt=self.config.date_format
                )
            
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏敏感信息"""
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.config.sensitive_fields):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
    
    def _log(self, level: str, message: str, **kwargs):
        """
        内部日志方法
        
        Args:
            level: 日志级别
            message: 日志消息
            kwargs: 额外字段
        """
        # 合并上下文
        context = {**self._context, **kwargs}
        
        # 脱敏
        context = self._sanitize(context)
        
        # 创建日志记录
        record = LogRecord(
            timestamp=int(time.time()),
            level=level,
            message=message,
            logger_name=self.name,
            agent_id=context.get("agent_id"),
            workflow_id=context.get("workflow_id"),
            extra=context
        )
        
        # 写入日志
        log_method = getattr(self._logger, level.lower(), self._logger.info)
        
        if self.config.json_format:
            log_method(record.to_json())
        else:
            context_str = " ".join(f"{k}={v}" for k, v in context.items() if k in ["agent_id", "workflow_id"])
            if context_str:
                log_method(f"{message} [{context_str}]")
            else:
                log_method(message)
    
    def debug(self, message: str, **kwargs):
        """DEBUG 级别日志"""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """INFO 级别日志"""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """WARNING 级别日志"""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """ERROR 级别日志"""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """CRITICAL 级别日志"""
        self._log("CRITICAL", message, **kwargs)
    
    def exception(self, message: str, exc: Optional[Exception] = None, **kwargs):
        """记录异常"""
        if exc:
            kwargs["exception_type"] = type(exc).__name__
            kwargs["exception_message"] = str(exc)
        self._log("ERROR", message, **kwargs)
    
    def with_context(self, **kwargs) -> 'StructuredLogger':
        """
        添加上下文
        
        Returns:
            新的日志记录器实例
        """
        new_logger = StructuredLogger(self.name, self.config)
        new_logger._context = {**self._context, **kwargs}
        return new_logger
    
    def with_agent(self, agent_id: str) -> 'StructuredLogger':
        """绑定 Agent ID"""
        return self.with_context(agent_id=agent_id)
    
    def with_workflow(self, workflow_id: str) -> 'StructuredLogger':
        """绑定工作流 ID"""
        return self.with_context(workflow_id=workflow_id)
    
    @contextmanager
    def bind_context(self, **kwargs):
        """
        上下文管理器绑定上下文
        
        Usage:
            with logger.bind_context(agent_id="agent_001"):
                logger.info("Processing...")
        """
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield self
        finally:
            self._context = old_context
    
    def set_level(self, level: LogLevel):
        """设置日志级别"""
        self.config.level = level
        self._logger.setLevel(level.value)


class LoggerManager:
    """
    日志管理器
    
    管理多个日志记录器实例
    """
    
    _instance: Optional['LoggerManager'] = None
    _loggers: Dict[str, StructuredLogger] = {}
    
    def __new__(cls) -> 'LoggerManager':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_logger(self, name: str, config: Optional[LogConfig] = None) -> StructuredLogger:
        """
        获取日志记录器
        
        Args:
            name: 日志名称
            config: 日志配置
            
        Returns:
            StructuredLogger 实例
        """
        if name not in self._loggers:
            self._loggers[name] = StructuredLogger(name, config)
        return self._loggers[name]
    
    def configure(self, config: LogConfig):
        """配置所有日志记录器"""
        for logger in self._loggers.values():
            logger.config = config
            logger._logger = logger._setup_logger()
    
    def shutdown(self):
        """关闭所有日志记录器"""
        for logger in self._loggers.values():
            for handler in logger._logger.handlers:
                handler.close()


# 便捷函数
def get_logger(name: str, config: Optional[LogConfig] = None) -> StructuredLogger:
    """获取日志记录器"""
    return LoggerManager().get_logger(name, config)


def configure_logging(config: LogConfig):
    """配置日志系统"""
    LoggerManager().configure(config)

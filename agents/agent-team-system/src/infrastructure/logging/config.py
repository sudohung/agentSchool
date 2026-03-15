"""日志配置模块."""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from infrastructure.exceptions import LogError


class LogLevel(str, Enum):
    """日志级别"""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_string(cls, level: str) -> 'LogLevel':
        """从字符串创建日志级别"""
        level_upper = level.upper()
        if level_upper not in cls._value2member_map_:
            raise LogError(f"Invalid log level: {level}")
        return cls(level_upper)
    
    def to_int(self) -> int:
        """转换为整数级别"""
        mapping = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }
        return mapping.get(self.value, 20)


@dataclass
class LogConfig:
    """日志配置"""
    
    # 基础配置
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # 处理器配置
    handlers: List[str] = field(default_factory=lambda: ["console"])
    file_path: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # 格式配置
    json_format: bool = False
    async_write: bool = True  # 异步写入
    
    # 安全配置
    sensitive_fields: List[str] = field(default_factory=lambda: [
        "password",
        "token",
        "api_key",
        "secret",
        "credential",
        "private_key",
    ])
    
    # 上下文配置
    include_context: bool = True
    context_fields: List[str] = field(default_factory=lambda: [
        "agent_id",
        "workflow_id",
        "request_id",
    ])
    
    def __post_init__(self):
        """验证配置"""
        if self.max_bytes < 1024 * 1024:
            raise LogError(
                "max_bytes must be at least 1MB",
                errors=[f"Current value: {self.max_bytes} bytes"]
            )
        if self.backup_count < 1:
            raise LogError(
                "backup_count must be at least 1",
                errors=[f"Current value: {self.backup_count}"]
            )
        if not self.format:
            raise LogError(
                "format cannot be empty",
                errors=["Please provide a valid log format"]
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "level": self.level.value,
            "format": self.format,
            "date_format": self.date_format,
            "handlers": self.handlers,
            "file_path": self.file_path,
            "max_bytes": self.max_bytes,
            "backup_count": self.backup_count,
            "json_format": self.json_format,
            "async_write": self.async_write,
            "sensitive_fields": self.sensitive_fields,
            "include_context": self.include_context,
            "context_fields": self.context_fields,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogConfig':
        """从字典创建配置"""
        # 转换 level
        if "level" in data and isinstance(data["level"], str):
            data["level"] = LogLevel.from_string(data["level"])
        
        # 移除未知字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    def merge(self, other: 'LogConfig') -> 'LogConfig':
        """合并配置（other 优先）"""
        return LogConfig(
            level=other.level if other.level != LogLevel.INFO else self.level,
            format=other.format if other.format else self.format,
            date_format=other.date_format if other.date_format else self.date_format,
            handlers=other.handlers if other.handlers else self.handlers,
            file_path=other.file_path or self.file_path,
            max_bytes=other.max_bytes if other.max_bytes != 10 * 1024 * 1024 else self.max_bytes,
            backup_count=other.backup_count if other.backup_count != 5 else self.backup_count,
            json_format=other.json_format if other.json_format else self.json_format,
            async_write=other.async_write if other.async_write else self.async_write,
            sensitive_fields=other.sensitive_fields if other.sensitive_fields else self.sensitive_fields,
            include_context=other.include_context if other.include_context else self.include_context,
            context_fields=other.context_fields if other.context_fields else self.context_fields,
        )
    
    @classmethod
    def default(cls) -> 'LogConfig':
        """创建默认配置"""
        return cls()
    
    @classmethod
    def development(cls) -> 'LogConfig':
        """创建开发环境配置"""
        return cls(
            level=LogLevel.DEBUG,
            handlers=["console"],
            async_write=False,
        )
    
    @classmethod
    def production(cls) -> 'LogConfig':
        """创建生产环境配置"""
        return cls(
            level=LogLevel.INFO,
            handlers=["console", "file"],
            file_path="logs/app.log",
            max_bytes=50 * 1024 * 1024,
            backup_count=10,
            json_format=True,
        )

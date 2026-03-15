"""配置管理器模块."""

import os
import yaml
from pathlib import Path
from typing import Any, Callable, List, Optional, Dict
from dataclasses import dataclass, field, fields, is_dataclass
from copy import deepcopy

from infrastructure.exceptions import ConfigLoadError, ConfigValidationError
from infrastructure.config.validators import ConfigValidator, ValidationError


@dataclass
class SystemConfig:
    """系统配置"""
    
    # 基础配置
    app_name: str = "agent-team-system"
    environment: str = "development"
    debug: bool = False
    
    # Agent 配置
    max_agents: int = 20
    max_iterations: int = 10
    iteration_timeout: int = 3600
    
    # 存储配置
    document_storage: str = "local"
    document_path: str = "./documents"
    database_url: Optional[str] = None
    
    # 监控配置
    metrics_enabled: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # 性能配置
    max_concurrent_tasks: int = 10
    task_timeout: int = 300
    
    def validate(self) -> List[ValidationError]:
        """验证配置"""
        errors = []
        
        # Agent 配置验证
        if error := ConfigValidator.validate_min(self.max_agents, 1, "max_agents"):
            errors.append(error)
        if error := ConfigValidator.validate_min(self.max_iterations, 1, "max_iterations"):
            errors.append(error)
        if error := ConfigValidator.validate_min(self.iteration_timeout, 60, "iteration_timeout"):
            errors.append(error)
        
        # 端口验证
        if error := ConfigValidator.validate_port(self.metrics_port, "metrics_port"):
            errors.append(error)
        
        # 性能配置验证
        if error := ConfigValidator.validate_min(self.max_concurrent_tasks, 1, "max_concurrent_tasks"):
            errors.append(error)
        if error := ConfigValidator.validate_min(self.task_timeout, 10, "task_timeout"):
            errors.append(error)
        
        # 路径验证
        if self.document_path:
            if error := ConfigValidator.validate_directory_path(self.document_path, "document_path"):
                errors.append(error)
        
        return errors


class ConfigManager:
    """
    配置管理器
    
    支持多源配置加载（环境变量、文件、默认值）
    支持配置热重载和监听
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self._config: SystemConfig = SystemConfig()
        self._config_path: Optional[Path] = Path(config_path) if config_path else None
        self._watchers: List[Callable[[SystemConfig], None]] = []
        self._loaded = False
    
    def load(self, config_path: Optional[str] = None) -> SystemConfig:
        """
        加载配置
        
        优先级：环境变量 > 配置文件 > 默认值
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            SystemConfig 配置对象
        """
        if config_path:
            self._config_path = Path(config_path)
            self._load_from_file(self._config_path)
        
        # 从环境变量加载（覆盖文件配置）
        self._load_from_env()
        
        # 验证配置
        errors = self._config.validate()
        if errors:
            error_messages = [str(e) for e in errors]
            raise ConfigValidationError(
                message="Configuration validation failed",
                errors=error_messages
            )
        
        self._loaded = True
        return self._config
    
    def reload(self) -> SystemConfig:
        """重新加载配置"""
        if self._config_path and self._config_path.exists():
            self._load_from_file(self._config_path)
            self._load_from_env()
            
            # 验证
            errors = self._config.validate()
            if errors:
                error_messages = [str(e) for e in errors]
                raise ConfigValidationError(
                    message="Configuration validation failed",
                    errors=error_messages
                )
            
            # 通知观察者
            self._notify_watchers()
        
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self._notify_watchers()
        else:
            raise AttributeError(f"Unknown config key: {key}")
    
    def watch(self, callback: Callable[[SystemConfig], None]):
        """
        监听配置变化
        
        Args:
            callback: 回调函数
        """
        self._watchers.append(callback)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            field.name: getattr(self._config, field.name)
            for field in fields(self._config)
        }
    
    def _load_from_file(self, path: Path):
        """从文件加载配置"""
        if not path.exists():
            raise ConfigLoadError(f"Config file not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data:
                self._apply_dict(data)
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Failed to parse config file: {e}")
        except Exception as e:
            raise ConfigLoadError(f"Failed to load config file: {e}")
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mapping = {
            "ATS_APP_NAME": "app_name",
            "ATS_ENVIRONMENT": "environment",
            "ATS_DEBUG": "debug",
            "ATS_MAX_AGENTS": "max_agents",
            "ATS_MAX_ITERATIONS": "max_iterations",
            "ATS_ITERATION_TIMEOUT": "iteration_timeout",
            "ATS_DOCUMENT_STORAGE": "document_storage",
            "ATS_DOCUMENT_PATH": "document_path",
            "ATS_DATABASE_URL": "database_url",
            "ATS_METRICS_ENABLED": "metrics_enabled",
            "ATS_METRICS_PORT": "metrics_port",
            "ATS_LOG_LEVEL": "log_level",
            "ATS_LOG_FILE": "log_file",
            "ATS_MAX_CONCURRENT_TASKS": "max_concurrent_tasks",
            "ATS_TASK_TIMEOUT": "task_timeout",
        }
        
        for env_name, config_key in env_mapping.items():
            if env_name in os.environ:
                value = os.environ[env_name]
                
                # 类型转换
                current_value = getattr(self._config, config_key)
                if isinstance(current_value, bool):
                    value = value.lower() in ('true', '1', 'yes')
                elif isinstance(current_value, int):
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                
                setattr(self._config, config_key, value)
    
    def _apply_dict(self, data: Dict[str, Any]):
        """应用字典配置"""
        for field in fields(self._config):
            if field.name in data:
                value = data[field.name]
                current_value = getattr(self._config, field.name)
                
                # 类型检查
                if type(current_value) == type(value) or value is None:
                    setattr(self._config, field.name, value)
    
    def _notify_watchers(self):
        """通知配置观察者"""
        for watcher in self._watchers:
            try:
                watcher(deepcopy(self._config))
            except Exception:
                # 观察者错误不影响主流程
                pass
    
    @property
    def config(self) -> SystemConfig:
        """获取配置对象"""
        return self._config
    
    @property
    def is_loaded(self) -> bool:
        """配置是否已加载"""
        return self._loaded


# 便捷函数
def load_config(config_path: Optional[str] = None) -> SystemConfig:
    """加载配置"""
    manager = ConfigManager(config_path)
    return manager.load()


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """获取配置管理器"""
    return ConfigManager(config_path)

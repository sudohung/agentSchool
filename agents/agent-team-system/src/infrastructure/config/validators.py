"""配置验证器模块."""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class ValidationError:
    """验证错误"""
    
    field: str
    message: str
    value: Optional[Any] = None
    
    def __str__(self) -> str:
        return f"{self.field}: {self.message} (got: {self.value})"


class ConfigValidator:
    """
    配置验证器
    
    验证配置值的有效性
    """
    
    @staticmethod
    def validate_not_empty(value: Any, field_name: str) -> Optional[ValidationError]:
        """验证值不为空"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return ValidationError(
                field=field_name,
                message="cannot be empty",
                value=value
            )
        return None
    
    @staticmethod
    def validate_min(value: int, min_value: int, field_name: str) -> Optional[ValidationError]:
        """验证最小值"""
        if value < min_value:
            return ValidationError(
                field=field_name,
                message=f"must be >= {min_value}",
                value=value
            )
        return None
    
    @staticmethod
    def validate_max(value: int, max_value: int, field_name: str) -> Optional[ValidationError]:
        """验证最大值"""
        if value > max_value:
            return ValidationError(
                field=field_name,
                message=f"must be <= {max_value}",
                value=value
            )
        return None
    
    @staticmethod
    def validate_range(
        value: int,
        min_value: int,
        max_value: int,
        field_name: str
    ) -> Optional[ValidationError]:
        """验证范围"""
        if value < min_value or value > max_value:
            return ValidationError(
                field=field_name,
                message=f"must be between {min_value} and {max_value}",
                value=value
            )
        return None
    
    @staticmethod
    def validate_port(value: int, field_name: str = "port") -> Optional[ValidationError]:
        """验证端口号"""
        return ConfigValidator.validate_range(value, 1, 65535, field_name)
    
    @staticmethod
    def validate_positive(value: int, field_name: str) -> Optional[ValidationError]:
        """验证正数"""
        return ConfigValidator.validate_min(value, 1, field_name)
    
    @staticmethod
    def validate_in_choices(
        value: Any,
        choices: List[Any],
        field_name: str
    ) -> Optional[ValidationError]:
        """验证在选项中"""
        if value not in choices:
            return ValidationError(
                field=field_name,
                message=f"must be one of {choices}",
                value=value
            )
        return None
    
    @staticmethod
    def validate_pattern(
        value: str,
        pattern: str,
        field_name: str
    ) -> Optional[ValidationError]:
        """验证正则表达式匹配"""
        import re
        if not re.match(pattern, value):
            return ValidationError(
                field=field_name,
                message=f"must match pattern {pattern}",
                value=value
            )
        return None
    
    @staticmethod
    def validate_url(value: str, field_name: str = "url") -> Optional[ValidationError]:
        """验证 URL 格式"""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return ConfigValidator.validate_pattern(value, pattern, field_name)
    
    @staticmethod
    def validate_file_path(value: str, field_name: str = "path") -> Optional[ValidationError]:
        """验证文件路径"""
        from pathlib import Path
        try:
            Path(value)
            return None
        except Exception as e:
            return ValidationError(
                field=field_name,
                message=f"invalid path: {e}",
                value=value
            )
    
    @staticmethod
    def validate_directory_path(value: str, field_name: str = "path") -> Optional[ValidationError]:
        """验证目录路径"""
        from pathlib import Path
        try:
            path = Path(value)
            if not path.exists():
                # 尝试创建目录
                path.mkdir(parents=True, exist_ok=True)
            return None
        except Exception as e:
            return ValidationError(
                field=field_name,
                message=f"invalid directory: {e}",
                value=value
            )

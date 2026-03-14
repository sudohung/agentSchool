"""交付配置."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class DeliveryMethod(Enum):
    """交付方式"""
    ZIP = "zip"                    # 打包为 ZIP 文件
    GIT = "git"                    # 推送到 Git 仓库
    S3 = "s3"                      # 上传到 S3 存储
    LOCAL = "local"                # 本地目录
    CUSTOM = "custom"              # 自定义方式


@dataclass
class DeliveryConfig:
    """
    交付配置
    
    定义交付方式、位置、选项等配置
    """
    
    # 交付方式
    method: DeliveryMethod = DeliveryMethod.LOCAL
    
    # 交付位置
    delivery_path: str = "./deliveries"
    git_repo_url: Optional[str] = None
    git_branch: str = "main"
    s3_bucket: Optional[str] = None
    s3_key_prefix: str = "deliveries"
    
    # 交付选项
    include_source_code: bool = True
    include_tests: bool = True
    include_docs: bool = True
    include_deployment: bool = True
    
    # 打包选项
    create_zip: bool = True
    zip_compression: int = 8  # 1-9, 9 为最高压缩
    
    # 通知配置
    notify_on_delivery: bool = True
    notification_channels: List[str] = field(default_factory=list)
    
    # 反馈配置
    collect_feedback: bool = True
    feedback_timeout: int = 86400  # 24 小时（秒）
    auto_process_feedback: bool = True
    
    # 交付清单
    generate_manifest: bool = True
    manifest_format: str = "markdown"  # markdown, json, yaml
    
    # 自定义选项
    custom_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 验证配置
        if self.method == DeliveryMethod.GIT and not self.git_repo_url:
            raise ValueError("Git delivery requires git_repo_url")
        
        if self.method == DeliveryMethod.S3 and not self.s3_bucket:
            raise ValueError("S3 delivery requires s3_bucket")
        
        # 确保压缩级别在有效范围内
        self.zip_compression = max(1, min(9, self.zip_compression))
    
    @classmethod
    def default(cls) -> DeliveryConfig:
        """创建默认配置"""
        return cls(
            method=DeliveryMethod.LOCAL,
            delivery_path="./deliveries",
            create_zip=True,
            generate_manifest=True,
        )
    
    @classmethod
    def for_git(cls, repo_url: str, branch: str = "main") -> DeliveryConfig:
        """创建 Git 交付配置"""
        return cls(
            method=DeliveryMethod.GIT,
            git_repo_url=repo_url,
            git_branch=branch,
            delivery_path="./.delivery_tmp",
        )
    
    @classmethod
    def for_zip(cls, output_path: str) -> DeliveryConfig:
        """创建 ZIP 交付配置"""
        return cls(
            method=DeliveryMethod.ZIP,
            delivery_path=output_path,
            create_zip=True,
        )

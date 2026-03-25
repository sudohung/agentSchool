"""交付系统模块."""

from .config import DeliveryConfig, DeliveryMethod
from .integrator import ProductIntegrator, DeliveryPackage
from .packager import DeliveryPackager, DeliveryArtifact
from .deliverer import DeliveryExecutor, DeliveryResult, DeliveryRecipient
from .feedback import FeedbackProcessor, FeedbackType, FeedbackPriority, FeedbackStatus
from .storage import DeliveryStorage
from .manifest import ManifestGenerator
from .service import DeliveryService
from .models import (
    DeliveryStatus,
    QualityLevel,
    QualityCheckResult,
    FeedbackItem,
    DeliveryReport,
)
from .git_delivery import GitDeliveryExecutor, GitDeliveryConfig, GitExecutionResult
from .s3_delivery import S3DeliveryExecutor, S3DeliveryConfig, S3UploadResult

__all__ = [
    # 配置
    "DeliveryConfig",
    "DeliveryMethod",
    # 模型
    "DeliveryStatus",
    "QualityLevel",
    "QualityCheckResult",
    "FeedbackItem",
    "DeliveryReport",
    "DeliveryArtifact",
    "DeliveryPackage",
    "DeliveryResult",
    "DeliveryRecipient",
    # 核心模块
    "ProductIntegrator",
    "DeliveryPackager",
    "DeliveryExecutor",
    "FeedbackProcessor",
    "FeedbackType",
    "FeedbackPriority",
    "FeedbackStatus",
    "DeliveryStorage",
    "ManifestGenerator",
    "DeliveryService",
    # Git 交付
    "GitDeliveryExecutor",
    "GitDeliveryConfig",
    "GitExecutionResult",
    # S3 交付
    "S3DeliveryExecutor",
    "S3DeliveryConfig",
    "S3UploadResult",
]

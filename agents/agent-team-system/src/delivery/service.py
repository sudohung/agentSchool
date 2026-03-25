"""交付服务 - 统一的交付入口 - 完善版."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .models import (
    DeliveryPackage,
    DeliveryStatus,
    DeliveryMethod,
    DeliveryReport,
    QualityLevel,
    FeedbackItem,
)
from .integrator import ProductIntegrator
from .quality_checker import QualityChecker
from .packager import DeliveryPackager
from .feedback import FeedbackProcessor
from .storage import DeliveryStorage
from .manifest import ManifestGenerator

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    交付服务 - 完善版
    
    统一的交付入口，协调各模块完成交付流程
    
    功能：
    1. 产品整合
    2. 质量检查
    3. 打包交付物
    4. 反馈处理
    5. 交付历史管理
    """
    
    def __init__(
        self,
        document_hub: Any,
        request_board: Any = None,
        output_path: str = "./deliverables",
    ):
        self.document_hub = document_hub
        self.request_board = request_board
        self.output_path = Path(output_path)
        
        # 初始化各模块
        self.integrator = ProductIntegrator(document_hub, output_path)
        self.quality_checker = QualityChecker()
        self.packager = DeliveryPackager(output_path)
        self.feedback_processor = FeedbackProcessor(request_board, document_hub)
        self.storage = DeliveryStorage(str(output_path))
        self.manifest_generator = ManifestGenerator()
        
        self._packages: Dict[str, DeliveryPackage] = {}
        self._delivery_history: List[Dict[str, Any]] = []
    
    async def prepare_delivery(self, project_name: str) -> DeliveryPackage:
        """准备交付"""
        logger.info(f"Preparing delivery for: {project_name}")
        
        package = await self.integrator.integrate(project_name)
        package.status = DeliveryStatus.QUALITY_CHECKING
        
        quality_results = await self.quality_checker.check(package)
        package.quality_checks = quality_results
        
        score, level = self.quality_checker.calculate_overall_score(quality_results)
        package.quality_score = score
        package.quality_level = level
        
        package.status = DeliveryStatus.PACKAGING
        await self.packager.package(package)
        
        package.status = DeliveryStatus.READY
        
        self._packages[package.id] = package
        
        logger.info(f"Delivery ready: {package.id}, quality: {level.value} ({score:.1%})")
        
        return package
    
    async def process_feedback(
        self,
        delivery_id: str,
        content: str,
        feedback_type: str = "other",
        priority: str = "p2_medium",
        user_id: str = "user",
    ) -> FeedbackItem:
        """处理反馈"""
        feedback = await self.feedback_processor.collect(
            delivery_id=delivery_id,
            content=content,
            feedback_type=feedback_type,
            priority=priority,
            user_id=user_id,
        )
        
        # 分析反馈
        analysis = await self.feedback_processor.analyze(feedback)
        
        # 优先级排序
        final_priority = await self.feedback_processor.prioritize(feedback, analysis)
        
        # 创建任务
        task = await self.feedback_processor.create_task(feedback, analysis)
        
        logger.info(
            f"Feedback processed: {feedback.id} -> "
            f"{analysis.feedback_type.value}, {final_priority.value}"
        )
        
        return feedback
    
    async def get_feedback_list(
        self,
        feedback_type: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[FeedbackItem]:
        """获取反馈列表"""
        return await self.feedback_processor.get_feedback(
            feedback_type=feedback_type,
            priority=priority,
            status=status,
        )
    
    async def get_delivery_history(
        self,
        package_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取交付历史"""
        if package_id:
            return [h for h in self._delivery_history if h["package_id"] == package_id]
        return self._delivery_history.copy()
    
    def get_package(self, package_id: str) -> Optional[DeliveryPackage]:
        """获取交付包"""
        return self._packages.get(package_id)
    
    def list_packages(self) -> List[DeliveryPackage]:
        """列出所有交付包"""
        return list(self._packages.values())

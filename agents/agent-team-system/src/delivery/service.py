"""交付服务 - 统一的交付入口."""

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
from .feedback import FeedbackHandler

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    交付服务
    
    统一的交付入口，协调各模块完成交付流程
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
        
        self.integrator = ProductIntegrator(document_hub, output_path)
        self.quality_checker = QualityChecker()
        self.packager = DeliveryPackager(output_path)
        self.feedback_handler = FeedbackHandler(request_board)
        
        self._packages: Dict[str, DeliveryPackage] = {}
    
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
        await self.packager.package(package, DeliveryMethod.DIRECTORY)
        
        package.status = DeliveryStatus.READY
        
        self._packages[package.id] = package
        
        logger.info(f"Delivery ready: {package.id}, quality: {level.value} ({score:.1%})")
        
        return package
    
    async def deliver(
        self,
        package_id: str,
        method: DeliveryMethod = DeliveryMethod.DIRECTORY,
    ) -> Path:
        """执行交付"""
        package = self._packages.get(package_id)
        
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        if package.status != DeliveryStatus.READY:
            raise RuntimeError(f"Package not ready: {package.status.value}")
        
        delivery_path = await self.packager.package(package, method)
        
        package.status = DeliveryStatus.DELIVERED
        package.delivered_at = int(time.time())
        
        logger.info(f"Delivered: {package_id} to {delivery_path}")
        
        return delivery_path
    
    async def accept_delivery(self, package_id: str) -> bool:
        """验收交付"""
        package = self._packages.get(package_id)
        
        if not package:
            return False
        
        package.status = DeliveryStatus.ACCEPTED
        logger.info(f"Delivery accepted: {package_id}")
        
        return True
    
    async def reject_delivery(self, package_id: str, reason: str) -> bool:
        """拒绝交付"""
        package = self._packages.get(package_id)
        
        if not package:
            return False
        
        package.status = DeliveryStatus.REJECTED
        logger.info(f"Delivery rejected: {package_id}, reason: {reason}")
        
        return True
    
    async def submit_feedback(
        self,
        package_id: str,
        feedback_type: str,
        priority: str,
        content: str,
        related_artifact: Optional[str] = None,
    ) -> FeedbackItem:
        """提交反馈"""
        package = self._packages.get(package_id)
        
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        package.status = DeliveryStatus.FEEDBACK
        
        feedback = await self.feedback_handler.submit_feedback(
            feedback_type=feedback_type,
            priority=priority,
            content=content,
            related_artifact=related_artifact,
        )
        
        logger.info(f"Feedback submitted for {package_id}: {feedback.id}")
        
        return feedback
    
    async def generate_report(
        self,
        package_id: str,
        participating_agents: List[str] = None,
        iterations: int = 0,
        total_time: float = 0.0,
    ) -> DeliveryReport:
        """生成交付报告"""
        package = self._packages.get(package_id)
        
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        feedback_items = await self.feedback_handler.get_feedback()
        
        summary = self._generate_summary(package)
        
        report = DeliveryReport(
            package_id=package_id,
            project_name=package.name,
            summary=summary,
            total_artifacts=len(package.artifacts),
            quality_score=package.quality_score,
            quality_level=package.quality_level,
            participating_agents=participating_agents or [],
            iterations=iterations,
            total_time=total_time,
            feedback_items=feedback_items,
            generated_at=int(time.time()),
        )
        
        return report
    
    def _generate_summary(self, package: DeliveryPackage) -> str:
        """生成摘要"""
        artifact_types = {}
        for artifact in package.artifacts:
            artifact_types[artifact.type] = artifact_types.get(artifact.type, 0) + 1
        
        type_str = ", ".join(f"{t}: {c}" for t, c in artifact_types.items())
        
        return (
            f"项目 '{package.name}' 交付完成。"
            f"共产出 {len(package.artifacts)} 个产物（{type_str}）。"
            f"质量评分：{package.quality_score:.1%}（{package.quality_level.value}）。"
        )
    
    def get_package(self, package_id: str) -> Optional[DeliveryPackage]:
        """获取交付包"""
        return self._packages.get(package_id)
    
    def list_packages(self) -> List[DeliveryPackage]:
        """列出所有交付包"""
        return list(self._packages.values())

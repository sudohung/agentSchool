"""交付执行器 - 执行实际交付操作."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import time

from .models import (
    DeliveryArtifact,
    DeliveryStatus,
    DeliveryMethod,
    DeliveryResult,
)

logger = logging.getLogger(__name__)


class DeliveryRecipient:
    """交付接收方"""
    
    def __init__(
        self,
        user_id: str,
        name: str,
        email: Optional[str] = None,
        local_path: Optional[str] = None,
        git_repo: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        notification_channels: Optional[List[str]] = None,
    ):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.local_path = local_path
        self.git_repo = git_repo
        self.s3_bucket = s3_bucket
        self.notification_channels = notification_channels or []
    
    def __repr__(self) -> str:
        return f"DeliveryRecipient({self.user_id}, {self.name})"


class DeliveryExecutor:
    """
    交付执行器
    
    职责：
    1. 执行实际交付操作
    2. 支持多种交付方式（本地/ZIP/Git/S3）
    3. 发送交付通知
    4. 记录交付历史
    """
    
    def __init__(
        self,
        output_path: str = "./deliverables",
        notification_service: Optional[Any] = None,
    ):
        self.output_path = Path(output_path)
        self.notification_service = notification_service
        self._delivery_history: List[Dict[str, Any]] = []
        
        self._ensure_output_path()
    
    def _ensure_output_path(self):
        """确保输出目录存在"""
        self.output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output path ensured: {self.output_path}")
    
    async def execute(
        self,
        artifact: DeliveryArtifact,
        recipient: DeliveryRecipient,
        method: DeliveryMethod = DeliveryMethod.DIRECTORY,
    ) -> DeliveryResult:
        """
        执行交付
        
        Args:
            artifact: 交付产物
            recipient: 接收方信息
            method: 交付方式
        
        Returns:
            DeliveryResult: 交付结果
        """
        logger.info(f"Executing delivery: {artifact.id} for {recipient.user_id}")
        
        try:
            # 根据交付方式选择执行策略
            if method == DeliveryMethod.DIRECTORY:
                result = await self._deliver_local(artifact, recipient)
            elif method == DeliveryMethod.ZIP:
                result = await self._deliver_zip(artifact, recipient)
            elif method == DeliveryMethod.GIT:
                result = await self._deliver_git(artifact, recipient)
            else:
                raise ValueError(f"Unsupported delivery method: {method}")
            
            # 验证交付成功
            if result.success:
                result.verified = await self._verify_delivery(result)
                
                # 发送通知
                if recipient.notification_channels:
                    await self._send_notification(result, recipient.notification_channels)
                
                # 记录交付历史
                await self._record_delivery(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Delivery failed: {e}")
            return DeliveryResult(
                success=False,
                delivery_id="",
                artifact_id=artifact.id,
                delivery_method=method.value,
                error=str(e),
            )
    
    async def _deliver_local(
        self,
        artifact: DeliveryArtifact,
        recipient: DeliveryRecipient,
    ) -> DeliveryResult:
        """
        本地交付
        
        Args:
            artifact: 交付产物
            recipient: 接收方
        
        Returns:
            DeliveryResult: 交付结果
        """
        logger.info(f"Delivering locally: {artifact.id}")
        
        try:
            # 确定交付路径
            if recipient.local_path:
                target_path = Path(recipient.local_path)
            else:
                target_path = self.output_path / f"{artifact.package.project_name}"
            
            # 创建目标目录
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 复制交付物
            if artifact.local_path and Path(artifact.local_path).exists():
                source_path = Path(artifact.local_path)
                # 复制所有文件
                for item in source_path.iterdir():
                    dest = target_path / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
            else:
                # 从 artifact 创建文件
                await self._create_from_artifact(artifact, target_path)
            
            delivery_id = f"del_{int(time.time())}"
            
            return DeliveryResult(
                success=True,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method=DeliveryMethod.DIRECTORY.value,
                delivery_path=str(target_path),
                verified=False,
            )
            
        except Exception as e:
            logger.error(f"Local delivery failed: {e}")
            return DeliveryResult(
                success=False,
                delivery_id="",
                artifact_id=artifact.id,
                delivery_method=DeliveryMethod.DIRECTORY.value,
                error=str(e),
            )
    
    async def _deliver_zip(
        self,
        artifact: DeliveryArtifact,
        recipient: DeliveryRecipient,
    ) -> DeliveryResult:
        """
        ZIP 打包交付
        
        Args:
            artifact: 交付产物
            recipient: 接收方
        
        Returns:
            DeliveryResult: 交付结果
        """
        logger.info(f"Delivering as ZIP: {artifact.id}")
        
        try:
            # 确定 ZIP 文件路径
            zip_name = f"{artifact.package.project_name}"
            zip_path = self.output_path / zip_name
            
            # 如果已有 ZIP 路径，直接使用
            if artifact.zip_path and Path(artifact.zip_path).exists():
                source_zip = Path(artifact.zip_path)
                target_zip = zip_path.with_suffix('.zip')
                shutil.copy2(source_zip, target_zip)
            else:
                # 从本地路径创建 ZIP
                if artifact.local_path and Path(artifact.local_path).exists():
                    shutil.make_archive(str(zip_path), 'zip', artifact.local_path)
                else:
                    # 从 artifact 创建临时目录并打包
                    temp_dir = self.output_path / f"temp_{artifact.id}"
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    await self._create_from_artifact(artifact, temp_dir)
                    shutil.make_archive(str(zip_path), 'zip', temp_dir)
                    shutil.rmtree(temp_dir)
            
            target_zip = zip_path.with_suffix('.zip')
            delivery_id = f"del_{int(time.time())}"
            
            return DeliveryResult(
                success=True,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method=DeliveryMethod.ZIP.value,
                delivery_path=str(target_zip),
                verified=False,
            )
            
        except Exception as e:
            logger.error(f"ZIP delivery failed: {e}")
            return DeliveryResult(
                success=False,
                delivery_id="",
                artifact_id=artifact.id,
                delivery_method=DeliveryMethod.ZIP.value,
                error=str(e),
            )
    
    async def _deliver_git(
        self,
        artifact: DeliveryArtifact,
        recipient: DeliveryRecipient,
    ) -> DeliveryResult:
        """
        Git 仓库交付
        
        Args:
            artifact: 交付产物
            recipient: 接收方
        
        Returns:
            DeliveryResult: 交付结果
        """
        logger.info(f"Delivering to Git: {artifact.id}")
        
        # TODO: 实现 Git 交付
        # 需要 gitpython 库支持
        logger.warning("Git delivery not yet implemented")
        
        return DeliveryResult(
            success=False,
            delivery_id="",
            artifact_id=artifact.id,
            delivery_method=DeliveryMethod.GIT.value,
            error="Git delivery not yet implemented",
        )
    
    async def _create_from_artifact(
        self,
        artifact: DeliveryArtifact,
        target_path: Path,
    ):
        """从 artifact 创建文件"""
        package = artifact.package
        
        # 创建文档
        docs_dir = target_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        for doc in package.documents:
            doc_path = docs_dir / f"{doc.id}.md"
            doc_path.write_text(doc.content if hasattr(doc, 'content') else str(doc))
        
        # 创建源代码
        src_dir = target_path / "src"
        src_dir.mkdir(exist_ok=True)
        
        for file_path, content in package.source_code.items():
            file_path_obj = src_dir / file_path
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            file_path_obj.write_text(content)
        
        # 创建 README
        readme_path = target_path / "README.md"
        readme_content = f"# {package.project_name}\n\n"
        readme_content += f"Delivered at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        readme_content += f"Files: {len(package.source_code)} code files, {len(package.documents)} documents\n"
        readme_path.write_text(readme_content)
    
    async def _verify_delivery(self, result: DeliveryResult) -> bool:
        """
        验证交付成功
        
        Args:
            result: 交付结果
        
        Returns:
            bool: 是否验证通过
        """
        if not result.delivery_path:
            return False
        
        path = Path(result.delivery_path)
        
        if not path.exists():
            logger.error(f"Delivery path does not exist: {path}")
            return False
        
        # 验证文件数量
        if path.is_dir():
            file_count = len(list(path.rglob("*")))
            if file_count == 0:
                logger.warning(f"Delivery directory is empty: {path}")
                return False
            logger.info(f"Verified: {file_count} files in delivery")
        elif path.is_file():
            if path.stat().st_size == 0:
                logger.warning(f"Delivery file is empty: {path}")
                return False
            logger.info(f"Verified: ZIP file size {path.stat().st_size} bytes")
        
        return True
    
    async def _send_notification(
        self,
        result: DeliveryResult,
        channels: List[str],
    ):
        """
        发送交付通知
        
        Args:
            result: 交付结果
            channels: 通知渠道列表
        """
        if not self.notification_service:
            logger.debug("No notification service available")
            return
        
        message = f"✅ Delivery completed: {result.delivery_id}"
        if result.delivery_path:
            message += f"\nLocation: {result.delivery_path}"
        
        for channel in channels:
            try:
                if channel == "email":
                    # TODO: 发送邮件通知
                    logger.info(f"Email notification would be sent for {result.delivery_id}")
                elif channel == "slack":
                    # TODO: 发送 Slack 通知
                    logger.info(f"Slack notification would be sent for {result.delivery_id}")
                else:
                    logger.debug(f"Unknown notification channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
    
    async def _record_delivery(self, result: DeliveryResult):
        """
        记录交付历史
        
        Args:
            result: 交付结果
        """
        record = {
            "delivery_id": result.delivery_id,
            "artifact_id": result.artifact_id,
            "delivery_method": result.delivery_method,
            "delivery_path": result.delivery_path,
            "success": result.success,
            "verified": result.verified,
            "timestamp": int(time.time()),
        }
        
        self._delivery_history.append(record)
        logger.info(f"Delivery recorded: {result.delivery_id}")
    
    def get_delivery_history(
        self,
        delivery_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取交付历史
        
        Args:
            delivery_id: 可选的交付 ID
        
        Returns:
            交付历史记录列表
        """
        if delivery_id:
            return [r for r in self._delivery_history if r["delivery_id"] == delivery_id]
        return self._delivery_history.copy()

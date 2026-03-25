"""S3 交付实现 - 支持将交付物上传到 S3 存储."""

from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import logging
import os
import tempfile
import shutil

from delivery.models import DeliveryArtifact, DeliveryResult

logger = logging.getLogger(__name__)

S3_AVAILABLE = False
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception


@dataclass
class S3DeliveryConfig:
    """S3 交付配置"""
    
    bucket: str
    key_prefix: str = "deliveries"
    region: str = "us-east-1"
    acl: str = "private"
    storage_class: str = "STANDARD"
    metadata: Dict[str, str] = field(default_factory=dict)
    content_type: str = "application/octet-stream"
    max_concurrent_uploads: int = 5
    chunk_size: int = 8 * 1024 * 1024
    timeout: int = 300
    
    def get_s3_key(self, filename: str, delivery_id: Optional[str] = None) -> str:
        """生成 S3 键"""
        key = self.key_prefix
        if delivery_id:
            key = f"{key}/{delivery_id}"
        return f"{key}/{filename}"


@dataclass
class S3UploadResult:
    """S3 上传结果"""
    
    success: bool
    key: str
    etag: Optional[str] = None
    version_id: Optional[str] = None
    location: Optional[str] = None
    error: Optional[str] = None
    bytes_uploaded: int = 0
    
    def __bool__(self) -> bool:
        return self.success


class S3DeliveryExecutor:
    """
    S3 交付执行器
    
    职责：
    1. 上传文件到 S3
    2. 上传目录到 S3
    3. 管理上传进度
    4. 验证上传成功
    """
    
    def __init__(
        self,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.progress_callback = progress_callback
        self.endpoint_url = endpoint_url
        self._s3_client = None
        self._s3_available = S3_AVAILABLE
    
    def _get_s3_client(self):
        """获取 S3 客户端（延迟初始化）"""
        if not self._s3_available:
            return None
            
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                )
            except Exception as e:
                logger.error(f"Failed to create S3 client: {e}")
                return None
        
        return self._s3_client
    
    async def deliver(
        self,
        artifact: DeliveryArtifact,
        config: S3DeliveryConfig,
        local_path: Optional[Path] = None,
    ) -> DeliveryResult:
        """
        执行 S3 交付
        
        Args:
            artifact: 交付产物
            config: S3 配置
            local_path: 本地交付物路径
            
        Returns:
            DeliveryResult: 交付结果
        """
        delivery_id = f"s3_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        self._report_progress(f"Starting S3 delivery: {delivery_id}", 0, 0)
        
        if not self._s3_available:
            return await self._mock_deliver(artifact, config, delivery_id, local_path)
        
        try:
            s3_client = self._get_s3_client()
            if not s3_client:
                return DeliveryResult(
                    success=False,
                    delivery_id=delivery_id,
                    artifact_id=artifact.id,
                    delivery_method="s3",
                    error="S3 client not available",
                )
            
            bucket_exists = await self._check_bucket(s3_client, config.bucket)
            if not bucket_exists:
                return DeliveryResult(
                    success=False,
                    delivery_id=delivery_id,
                    artifact_id=artifact.id,
                    delivery_method="s3",
                    error=f"Bucket {config.bucket} does not exist or no access",
                )
            
            self._report_progress("Bucket verified", 10, 0)
            
            if local_path and local_path.exists():
                if local_path.is_dir():
                    results = await self._upload_directory(
                        s3_client, local_path, config, delivery_id
                    )
                else:
                    result = await self._upload_file(
                        s3_client, local_path, config, delivery_id
                    )
                    results = [result]
            else:
                results = await self._upload_artifact_metadata(
                    s3_client, artifact, config, delivery_id
                )
            
            success_count = sum(1 for r in results if r.success)
            total_count = len(results)
            
            if success_count == total_count:
                self._report_progress("Upload completed", 100, total_count)
                
                location = f"s3://{config.bucket}/{config.key_prefix}/{delivery_id}/"
                
                return DeliveryResult(
                    success=True,
                    delivery_id=delivery_id,
                    artifact_id=artifact.id,
                    delivery_method="s3",
                    delivery_path=location,
                    verified=True,
                )
            else:
                errors = [r.error for r in results if r.error]
                return DeliveryResult(
                    success=False,
                    delivery_id=delivery_id,
                    artifact_id=artifact.id,
                    delivery_method="s3",
                    error=f"Partial upload: {success_count}/{total_count}. Errors: {'; '.join(errors[:3])}",
                )
                
        except NoCredentialsError:
            return DeliveryResult(
                success=False,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method="s3",
                error="AWS credentials not configured",
            )
        except Exception as e:
            logger.error(f"S3 delivery failed: {e}")
            return DeliveryResult(
                success=False,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method="s3",
                error=str(e),
            )
    
    async def _check_bucket(self, s3_client, bucket: str) -> bool:
        """检查 bucket 是否存在"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                s3_client.head_bucket,
                Bucket=bucket
            )
            return True
        except ClientError:
            return False
    
    async def _upload_file(
        self,
        s3_client,
        file_path: Path,
        config: S3DeliveryConfig,
        delivery_id: str,
    ) -> S3UploadResult:
        """上传单个文件"""
        key = config.get_s3_key(file_path.name, delivery_id)
        
        self._report_progress(f"Uploading {file_path.name}", 0, 0)
        
        try:
            extra_args = {
                "ACL": config.acl,
                "StorageClass": config.storage_class,
                "ContentType": self._get_content_type(file_path),
            }
            
            if config.metadata:
                extra_args["Metadata"] = config.metadata
            
            loop = asyncio.get_event_loop()
            
            def upload():
                s3_client.upload_file(
                    str(file_path),
                    config.bucket,
                    key,
                    ExtraArgs=extra_args,
                )
            
            await asyncio.wait_for(
                loop.run_in_executor(None, upload),
                timeout=config.timeout
            )
            
            file_size = file_path.stat().st_size
            
            self._report_progress(f"Uploaded {file_path.name}", 100, 1)
            
            return S3UploadResult(
                success=True,
                key=key,
                location=f"s3://{config.bucket}/{key}",
                bytes_uploaded=file_size,
            )
            
        except asyncio.TimeoutError:
            return S3UploadResult(
                success=False,
                key=key,
                error="Upload timed out",
            )
        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            return S3UploadResult(
                success=False,
                key=key,
                error=str(e),
            )
    
    async def _upload_directory(
        self,
        s3_client,
        dir_path: Path,
        config: S3DeliveryConfig,
        delivery_id: str,
    ) -> List[S3UploadResult]:
        """上传整个目录"""
        results = []
        files = list(dir_path.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        total_files = len(files)
        
        semaphore = asyncio.Semaphore(config.max_concurrent_uploads)
        
        async def upload_with_semaphore(file_path: Path, index: int):
            async with semaphore:
                relative_path = file_path.relative_to(dir_path)
                key = config.get_s3_key(str(relative_path), delivery_id)
                
                progress = int((index / total_files) * 100)
                self._report_progress(f"Uploading {relative_path}", progress, index)
                
                return await self._upload_file(
                    s3_client, file_path, config, delivery_id
                )
        
        tasks = [
            upload_with_semaphore(f, i)
            for i, f in enumerate(files)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return list(results)
    
    async def _upload_artifact_metadata(
        self,
        s3_client,
        artifact: DeliveryArtifact,
        config: S3DeliveryConfig,
        delivery_id: str,
    ) -> List[S3UploadResult]:
        """上传产物元数据"""
        import json
        
        metadata_key = config.get_s3_key("artifact_metadata.json", delivery_id)
        
        metadata = {
            "id": artifact.id,
            "name": artifact.name,
            "type": artifact.type,
            "path": artifact.path,
            "size": artifact.size,
            "created_at": artifact.created_at,
            "delivery_id": delivery_id,
            "delivered_at": time.time(),
        }
        
        try:
            loop = asyncio.get_event_loop()
            
            def upload_metadata():
                s3_client.put_object(
                    Bucket=config.bucket,
                    Key=metadata_key,
                    Body=json.dumps(metadata, indent=2),
                    ContentType="application/json",
                    ACL=config.acl,
                    Metadata=config.metadata,
                )
            
            await loop.run_in_executor(None, upload_metadata)
            
            return [S3UploadResult(
                success=True,
                key=metadata_key,
                bytes_uploaded=len(json.dumps(metadata)),
            )]
            
        except Exception as e:
            return [S3UploadResult(
                success=False,
                key=metadata_key,
                error=str(e),
            )]
    
    async def _mock_deliver(
        self,
        artifact: DeliveryArtifact,
        config: S3DeliveryConfig,
        delivery_id: str,
        local_path: Optional[Path] = None,
    ) -> DeliveryResult:
        """模拟交付（无 boto3 时）"""
        logger.warning("boto3 not available, using mock S3 delivery")
        
        mock_path = Path(tempfile.gettempdir()) / "ats_s3_mock" / config.bucket / config.key_prefix / delivery_id
        
        try:
            mock_path.mkdir(parents=True, exist_ok=True)
            
            if local_path and local_path.exists():
                if local_path.is_dir():
                    for item in local_path.rglob("*"):
                        if item.is_file():
                            relative = item.relative_to(local_path)
                            dest = mock_path / relative
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, dest)
                else:
                    shutil.copy2(local_path, mock_path / local_path.name)
            else:
                metadata = {
                    "id": artifact.id,
                    "name": artifact.name,
                    "delivery_id": delivery_id,
                }
                (mock_path / "metadata.json").write_text(str(metadata))
            
            self._report_progress("Mock upload completed", 100, 1)
            
            return DeliveryResult(
                success=True,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method="s3",
                delivery_path=f"mock://{config.bucket}/{config.key_prefix}/{delivery_id}/",
                verified=True,
            )
            
        except Exception as e:
            return DeliveryResult(
                success=False,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method="s3",
                error=f"Mock delivery failed: {e}",
            )
    
    def _get_content_type(self, file_path: Path) -> str:
        """获取文件内容类型"""
        suffix = file_path.suffix.lower()
        content_types = {
            ".txt": "text/plain",
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".mp4": "video/mp4",
            ".mp3": "audio/mpeg",
        }
        return content_types.get(suffix, self._get_s3_config().content_type)
    
    def _get_s3_config(self) -> S3DeliveryConfig:
        """获取默认 S3 配置"""
        return S3DeliveryConfig(bucket="default")
    
    def _report_progress(self, message: str, progress: int, file_count: int):
        """报告进度"""
        logger.info(f"S3 delivery progress: {progress}% - {message} ({file_count} files)")
        if self.progress_callback:
            self.progress_callback(message, progress, file_count)
    
    @staticmethod
    def is_available() -> bool:
        """检查 S3 是否可用"""
        return S3_AVAILABLE
"""交付存储管理."""

from __future__ import annotations

import os
import shutil
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .models import DeliveryPackage, DeliveryStatus

logger = logging.getLogger(__name__)


class DeliveryStorage:
    """
    交付存储管理
    
    职责：
    1. 交付物存储管理
    2. 版本控制
    3. 清理过期交付
    """
    
    def __init__(self, base_path: str = "./deliveries"):
        self.base_path = Path(base_path)
        self._metadata_file = self.base_path / "metadata.json"
        self._deliveries: Dict[str, Dict[str, Any]] = {}
        
        self._ensure_base_path()
        self._load_metadata()
    
    def _ensure_base_path(self):
        """确保基础目录存在"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage base path ensured: {self.base_path}")
    
    def _load_metadata(self):
        """加载元数据"""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, 'r') as f:
                    self._deliveries = json.load(f)
                logger.info(f"Loaded metadata for {len(self._deliveries)} deliveries")
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
                self._deliveries = {}
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            with open(self._metadata_file, 'w') as f:
                json.dump(self._deliveries, f, indent=2)
            logger.debug("Metadata saved")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    async def store(
        self,
        package: DeliveryPackage,
        artifact_path: Optional[Path] = None,
    ) -> Path:
        """
        存储交付物
        
        Args:
            package: 交付包
            artifact_path: 交付物路径（可选）
        
        Returns:
            Path: 存储路径
        """
        logger.info(f"Storing delivery: {package.id}")
        
        # 创建项目目录
        project_dir = self.base_path / package.name
        version_dir = project_dir / package.version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果有 artifact 路径，复制文件
        if artifact_path and artifact_path.exists():
            if artifact_path.is_dir():
                # 复制整个目录
                for item in artifact_path.iterdir():
                    dest = version_dir / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
            else:
                # 复制文件
                shutil.copy2(artifact_path, version_dir)
        
        # 保存元数据
        delivery_record = {
            "id": package.id,
            "name": package.name,
            "version": package.version,
            "status": package.status.value,
            "quality_score": package.quality_score,
            "quality_level": package.quality_level.value,
            "created_at": package.created_at,
            "delivered_at": package.delivered_at,
            "storage_path": str(version_dir),
            "artifact_count": len(package.artifacts),
        }
        
        self._deliveries[package.id] = delivery_record
        self._save_metadata()
        
        logger.info(f"Delivery stored: {version_dir}")
        
        return version_dir
    
    async def retrieve(
        self,
        delivery_id: str,
    ) -> Optional[DeliveryPackage]:
        """
        检索交付物
        
        Args:
            delivery_id: 交付 ID
        
        Returns:
            DeliveryPackage: 交付包，如果不存在则返回 None
        """
        logger.info(f"Retrieving delivery: {delivery_id}")
        
        if delivery_id not in self._deliveries:
            logger.warning(f"Delivery not found: {delivery_id}")
            return None
        
        record = self._deliveries[delivery_id]
        storage_path = Path(record["storage_path"])
        
        if not storage_path.exists():
            logger.error(f"Storage path does not exist: {storage_path}")
            return None
        
        # 从存储重建 DeliveryPackage
        # 这里简化处理，实际应该从文件重建
        logger.info(f"Delivery retrieved: {delivery_id}")
        
        # 返回基本信息
        return None  # TODO: 实现完整的重建逻辑
    
    async def list_deliveries(
        self,
        project_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出交付记录
        
        Args:
            project_name: 项目名称（可选）
            status: 状态（可选）
        
        Returns:
            交付记录列表
        """
        results = list(self._deliveries.values())
        
        if project_name:
            results = [r for r in results if r["name"] == project_name]
        
        if status:
            results = [r for r in results if r["status"] == status]
        
        # 按创建时间排序（最新的在前）
        results.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        
        return results
    
    async def cleanup(
        self,
        older_than_days: int = 30,
        keep_versions: int = 3,
    ) -> int:
        """
        清理过期交付
        
        Args:
            older_than_days: 清理多少天前的交付
            keep_versions: 每个项目保留的最新版本数
        
        Returns:
            清理的交付数量
        """
        logger.info(f"Cleaning up deliveries older than {older_than_days} days")
        
        current_time = int(time.time())
        cutoff_time = current_time - (older_than_days * 24 * 60 * 60)
        
        cleaned_count = 0
        
        # 按项目分组
        projects: Dict[str, List[Dict[str, Any]]] = {}
        for delivery_id, record in self._deliveries.items():
            project_name = record["name"]
            if project_name not in projects:
                projects[project_name] = []
            projects[project_name].append((delivery_id, record))
        
        # 清理每个项目
        for project_name, deliveries in projects.items():
            # 按创建时间排序
            deliveries.sort(key=lambda x: x[1]["created_at"], reverse=True)
            
            # 保留最新版本
            for i, (delivery_id, record) in enumerate(deliveries):
                if i < keep_versions:
                    continue  # 保留
                
                # 检查是否超过保留期限
                if record["created_at"] < cutoff_time:
                    # 删除存储
                    storage_path = Path(record.get("storage_path", ""))
                    if storage_path.exists():
                        try:
                            shutil.rmtree(storage_path)
                            logger.info(f"Deleted storage: {storage_path}")
                        except Exception as e:
                            logger.error(f"Failed to delete storage: {e}")
                    
                    # 从元数据中删除
                    del self._deliveries[delivery_id]
                    cleaned_count += 1
                    logger.info(f"Cleaned up delivery: {delivery_id}")
        
        # 保存更新后的元数据
        self._save_metadata()
        
        logger.info(f"Cleanup complete: {cleaned_count} deliveries removed")
        
        return cleaned_count
    
    async def get_delivery_info(
        self,
        delivery_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        获取交付信息
        
        Args:
            delivery_id: 交付 ID
        
        Returns:
            交付信息字典
        """
        return self._deliveries.get(delivery_id)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计
        
        Returns:
            统计信息
        """
        total_deliveries = len(self._deliveries)
        total_size = 0
        
        # 计算总大小
        for record in self._deliveries.values():
            storage_path = Path(record.get("storage_path", ""))
            if storage_path.exists():
                for dirpath, dirnames, filenames in os.walk(storage_path):
                    for filename in filenames:
                        file_path = Path(dirpath) / filename
                        if file_path.exists():
                            total_size += file_path.stat().st_size
        
        # 按项目统计
        projects = {}
        for record in self._deliveries.values():
            project_name = record["name"]
            if project_name not in projects:
                projects[project_name] = 0
            projects[project_name] += 1
        
        return {
            "total_deliveries": total_deliveries,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "projects": len(projects),
            "by_project": projects,
        }

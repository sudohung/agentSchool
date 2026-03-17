"""版本控制 - 完整的版本管理功能."""

from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import Document
from .diff import DiffCalculator, DiffResult


class DocumentVersion:
    """文档版本"""
    
    def __init__(
        self,
        version_id: str,
        document_id: str,
        version: int,
        content: str,
        author: str,
        timestamp: int,
        change_summary: str,
        diff: Optional[DiffResult] = None,
        parent_version_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        self.version_id = version_id
        self.document_id = document_id
        self.version = version
        self.content = content
        self.author = author
        self.timestamp = timestamp
        self.change_summary = change_summary
        self.diff = diff
        self.parent_version_id = parent_version_id
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        diff_dict = None
        if self.diff:
            diff_dict = {
                "old_version": self.diff.old_version,
                "new_version": self.diff.new_version,
                "additions": self.diff.additions,
                "deletions": self.diff.deletions,
                "modifications": self.diff.modifications,
                "summary": self.diff.summary,
            }
        
        return {
            "version_id": self.version_id,
            "document_id": self.document_id,
            "version": self.version,
            "content": self.content,
            "author": self.author,
            "timestamp": self.timestamp,
            "change_summary": self.change_summary,
            "diff": diff_dict,
            "parent_version_id": self.parent_version_id,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentVersion":
        """从字典创建"""
        diff = None
        if data.get("diff"):
            diff = DiffResult(
                old_version=data["diff"]["old_version"],
                new_version=data["diff"]["new_version"],
                lines=[],
                additions=data["diff"].get("additions", 0),
                deletions=data["diff"].get("deletions", 0),
                modifications=data["diff"].get("modifications", 0),
                summary=data["diff"].get("summary", ""),
            )
        
        return cls(
            version_id=data["version_id"],
            document_id=data["document_id"],
            version=data["version"],
            content=data["content"],
            author=data["author"],
            timestamp=data["timestamp"],
            change_summary=data["change_summary"],
            diff=diff,
            parent_version_id=data.get("parent_version_id"),
            tags=data.get("tags", []),
        )


class VersionControl:
    """
    版本控制器
    
    功能：
    - 创建版本快照
    - 计算版本间 Diff
    - 版本回滚
    - 版本历史管理
    """
    
    def __init__(self, store, version_path: Optional[Path] = None):
        """
        初始化版本控制器
        
        Args:
            store: DocumentStore 实例
            version_path: 版本存储路径
        """
        self.store = store
        self.version_path = version_path or store.base_path.parent / "versions"
        self.diff_calculator = DiffCalculator()
        
        self.version_path.mkdir(parents=True, exist_ok=True)
    
    async def create_version(
        self,
        document_id: str,
        content: str,
        author: str,
        change_summary: str = "",
    ) -> DocumentVersion:
        """
        创建新版本
        
        Args:
            document_id: 文档 ID
            content: 文档内容
            author: 作者
            change_summary: 变更摘要
            
        Returns:
            DocumentVersion: 新创建的版本
        """
        current_version = await self._get_current_version(document_id)
        new_version = current_version + 1
        
        diff = None
        if current_version > 0:
            prev_version = await self.get_version(document_id, current_version)
            if prev_version:
                diff = self.diff_calculator.calculate(
                    prev_version.content,
                    content,
                    current_version,
                    new_version,
                )
        
        version = DocumentVersion(
            version_id=self._generate_version_id(document_id, new_version),
            document_id=document_id,
            version=new_version,
            content=content,
            author=author,
            timestamp=int(time.time()),
            change_summary=change_summary,
            diff=diff,
            parent_version_id=self._generate_version_id(document_id, current_version) if current_version > 0 else None,
        )
        
        await self._save_version(version)
        
        return version
    
    async def get_version(
        self,
        document_id: str,
        version: int,
    ) -> Optional[DocumentVersion]:
        """
        获取指定版本
        
        Args:
            document_id: 文档 ID
            version: 版本号
            
        Returns:
            DocumentVersion 或 None
        """
        version_file = self._get_version_file_path(document_id, version)
        
        if not version_file.exists():
            return None
        
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return DocumentVersion.from_dict(data)
    
    async def get_version_history(
        self,
        document_id: str,
        limit: int = 50,
    ) -> List[DocumentVersion]:
        """
        获取版本历史
        
        Args:
            document_id: 文档 ID
            limit: 最大返回数量
            
        Returns:
            版本列表（按版本号降序）
        """
        versions = []
        doc_version_dir = self.version_path / document_id
        
        if not doc_version_dir.exists():
            return versions
        
        version_files = sorted(
            doc_version_dir.glob("v*.json"),
            key=lambda p: int(p.stem[1:]),
            reverse=True
        )
        
        for vf in version_files[:limit]:
            with open(vf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            versions.append(DocumentVersion.from_dict(data))
        
        return versions
    
    async def rollback(
        self,
        document_id: str,
        target_version: int,
        author: str,
    ) -> DocumentVersion:
        """
        回滚到指定版本
        
        Args:
            document_id: 文档 ID
            target_version: 目标版本号
            author: 执行回滚的作者
            
        Returns:
            新版本（内容为回滚后的内容）
            
        Raises:
            ValueError: 目标版本不存在
        """
        target = await self.get_version(document_id, target_version)
        if not target:
            raise ValueError(f"Version {target_version} not found for document {document_id}")
        
        new_version = await self.create_version(
            document_id=document_id,
            content=target.content,
            author=author,
            change_summary=f"Rollback to version {target_version}",
        )
        
        return new_version
    
    async def compare_versions(
        self,
        document_id: str,
        version1: int,
        version2: int,
    ) -> Optional[DiffResult]:
        """
        比较两个版本
        
        Args:
            document_id: 文档 ID
            version1: 版本 1
            version2: 版本 2
            
        Returns:
            DiffResult 或 None
        """
        v1 = await self.get_version(document_id, version1)
        v2 = await self.get_version(document_id, version2)
        
        if not v1 or not v2:
            return None
        
        diff = self.diff_calculator.calculate(
            v1.content,
            v2.content,
            version1,
            version2,
        )
        
        return diff
    
    async def _get_current_version(self, document_id: str) -> int:
        """获取当前版本号"""
        doc_version_dir = self.version_path / document_id
        
        if not doc_version_dir.exists():
            return 0
        
        version_files = list(doc_version_dir.glob("v*.json"))
        if not version_files:
            return 0
        
        return max(int(vf.stem[1:]) for vf in version_files)
    
    def _generate_version_id(self, document_id: str, version: int) -> str:
        """生成版本 ID"""
        return f"{document_id}_v{version}"
    
    def _get_version_file_path(self, document_id: str, version: int) -> Path:
        """获取版本文件路径"""
        doc_version_dir = self.version_path / document_id
        doc_version_dir.mkdir(parents=True, exist_ok=True)
        return doc_version_dir / f"v{version}.json"
    
    async def _save_version(self, version: DocumentVersion):
        """保存版本到文件"""
        version_file = self._get_version_file_path(
            version.document_id,
            version.version
        )
        
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version.to_dict(), f, ensure_ascii=False, indent=2)
    
    async def get_statistics(self, document_id: str) -> Dict[str, Any]:
        """获取版本统计信息"""
        history = await self.get_version_history(document_id, limit=1000)
        
        if not history:
            return {
                "total_versions": 0,
                "authors": [],
                "first_version": None,
                "last_version": None,
            }
        
        authors = list(set(v.author for v in history))
        
        total_changes = sum(
            (v.diff.additions + v.diff.deletions) 
            for v in history if v.diff
        )
        
        return {
            "total_versions": len(history),
            "authors": authors,
            "first_version": history[-1].version if history else None,
            "last_version": history[0].version if history else None,
            "total_changes": total_changes,
        }

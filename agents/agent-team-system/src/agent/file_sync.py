"""文件同步服务 - 使用 opencode-4-py SDK."""

from __future__ import annotations

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """同步状态"""
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    content: str
    hash: str
    size: int
    modified_at: int
    sync_status: SyncStatus = SyncStatus.SYNCED


@dataclass
class SyncConflict:
    """同步冲突"""
    path: str
    local_content: str
    remote_content: str
    local_modified: int
    remote_modified: int
    resolution: Optional[str] = None


class FileSyncService:
    """
    文件同步服务
    
    使用 opencode-4-py SDK 实现文件同步
    
    功能：
    - 双向文件同步
    - 冲突检测和解决
    - 增量同步
    - 文件监控
    """
    
    def __init__(
        self,
        opencode_client: Any,
        document_hub: Any,
        local_base_path: str = "./workspace",
    ):
        """
        初始化文件同步服务
        
        Args:
            opencode_client: OpenCode 客户端 (opencode-4-py)
            document_hub: 文档中心
            local_base_path: 本地基础路径
        """
        self.client = opencode_client
        self.document_hub = document_hub
        self.local_base_path = Path(local_base_path)
        
        self._file_cache: Dict[str, FileInfo] = {}
        self._conflicts: List[SyncConflict] = []
        self._watch_callbacks: Dict[str, List[Callable]] = {}
        self._sync_lock = asyncio.Lock()
        
        self._running = False
        self._watch_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动同步服务"""
        self._running = True
        self._watch_task = asyncio.create_task(self._watch_loop())
        logger.info("FileSyncService started")
    
    async def stop(self):
        """停止同步服务"""
        self._running = False
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
        logger.info("FileSyncService stopped")
    
    async def read_file(self, path: str) -> Optional[str]:
        """
        读取文件
        
        优先从本地缓存读取，缓存未命中则从 OpenCode 读取
        """
        if path in self._file_cache:
            return self._file_cache[path].content
        
        try:
            content = await self._read_from_opencode(path)
            if content is not None:
                self._file_cache[path] = FileInfo(
                    path=path,
                    content=content,
                    hash=self._calculate_hash(content),
                    size=len(content),
                    modified_at=int(time.time()),
                )
            return content
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return None
    
    async def write_file(
        self,
        path: str,
        content: str,
        author: str,
        sync: bool = True,
    ) -> bool:
        """
        写入文件
        
        Args:
            path: 文件路径
            content: 文件内容
            author: 作者
            sync: 是否同步到 OpenCode
        """
        async with self._sync_lock:
            try:
                new_hash = self._calculate_hash(content)
                
                if path in self._file_cache:
                    cached = self._file_cache[path]
                    if cached.hash != new_hash and cached.sync_status == SyncStatus.PENDING:
                        await self._handle_conflict(path, content)
                        return False
                
                local_path = self.local_base_path / path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self._file_cache[path] = FileInfo(
                    path=path,
                    content=content,
                    hash=new_hash,
                    size=len(content),
                    modified_at=int(time.time()),
                    sync_status=SyncStatus.PENDING if sync else SyncStatus.SYNCED,
                )
                
                if sync:
                    success = await self._write_to_opencode(path, content)
                    if success:
                        self._file_cache[path].sync_status = SyncStatus.SYNCED
                
                await self._save_to_document_hub(path, content, author)
                
                logger.debug(f"Wrote file {path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to write file {path}: {e}")
                return False
    
    async def sync_file(self, path: str) -> SyncStatus:
        """同步单个文件"""
        async with self._sync_lock:
            try:
                remote_content = await self._read_from_opencode(path)
                
                if remote_content is None:
                    return SyncStatus.ERROR
                
                if path in self._file_cache:
                    cached = self._file_cache[path]
                    local_content = cached.content
                    
                    if local_content != remote_content:
                        remote_hash = self._calculate_hash(remote_content)
                        if cached.hash != remote_hash and cached.sync_status == SyncStatus.PENDING:
                            await self._handle_conflict(path, local_content)
                            return SyncStatus.CONFLICT
                
                self._file_cache[path] = FileInfo(
                    path=path,
                    content=remote_content,
                    hash=self._calculate_hash(remote_content),
                    size=len(remote_content),
                    modified_at=int(time.time()),
                    sync_status=SyncStatus.SYNCED,
                )
                
                return SyncStatus.SYNCED
                
            except Exception as e:
                logger.error(f"Failed to sync file {path}: {e}")
                return SyncStatus.ERROR
    
    async def sync_all(self, paths: Optional[List[str]] = None) -> Dict[str, SyncStatus]:
        """同步所有文件"""
        results = {}
        
        target_paths = paths or list(self._file_cache.keys())
        
        for path in target_paths:
            results[path] = await self.sync_file(path)
        
        return results
    
    async def watch_file(self, path: str, callback: Callable[[str, str], None]):
        """监控文件变化"""
        if path not in self._watch_callbacks:
            self._watch_callbacks[path] = []
        self._watch_callbacks[path].append(callback)
    
    async def unwatch_file(self, path: str, callback: Callable):
        """取消监控"""
        if path in self._watch_callbacks:
            self._watch_callbacks[path] = [
                cb for cb in self._watch_callbacks[path] if cb != callback
            ]
    
    async def get_conflicts(self) -> List[SyncConflict]:
        """获取所有冲突"""
        return self._conflicts.copy()
    
    async def resolve_conflict(
        self,
        path: str,
        resolution: str,
        content: Optional[str] = None,
    ):
        """
        解决冲突
        
        Args:
            path: 文件路径
            resolution: 解决方案 ("local", "remote", "merge")
            content: 合并后的内容（当 resolution="merge" 时）
        """
        conflict = next(
            (c for c in self._conflicts if c.path == path),
            None
        )
        
        if not conflict:
            return
        
        if resolution == "local":
            await self.write_file(path, conflict.local_content, "System")
        elif resolution == "remote":
            await self.write_file(path, conflict.remote_content, "System")
        elif resolution == "merge" and content:
            await self.write_file(path, content, "System")
        
        self._conflicts = [c for c in self._conflicts if c.path != path]
    
    async def _read_from_opencode(self, path: str) -> Optional[str]:
        """从 OpenCode 读取文件"""
        try:
            if not self.client:
                return None
            
            result = self.client.file.read(path=path)
            return result.content if result else None
            
        except Exception as e:
            logger.error(f"OpenCode read error: {e}")
            return None
    
    async def _write_to_opencode(self, path: str, content: str) -> bool:
        """写入文件到 OpenCode"""
        try:
            if not self.client:
                return False
            
            self.client.file.write(path=path, content=content)
            return True
            
        except Exception as e:
            logger.error(f"OpenCode write error: {e}")
            return False
    
    async def _save_to_document_hub(self, path: str, content: str, author: str):
        """保存到文档中心"""
        if not self.document_hub:
            return
        
        try:
            from document_hub.models import Document, DocumentMetadata, DocumentContent, DocumentType
            
            doc = Document(
                id=self._path_to_doc_id(path),
                path=path,
                metadata=DocumentMetadata(
                    title=Path(path).stem,
                    doc_type=self._infer_doc_type(path),
                    author=author,
                    created_at=int(time.time()),
                    updated_at=int(time.time()),
                    version=1,
                ),
                content=DocumentContent(content=content),
            )
            
            await self.document_hub.save(doc)
            
        except Exception as e:
            logger.error(f"Failed to save to document hub: {e}")
    
    async def _handle_conflict(self, path: str, local_content: str):
        """处理冲突"""
        remote_content = await self._read_from_opencode(path)
        
        if remote_content is None:
            return
        
        conflict = SyncConflict(
            path=path,
            local_content=local_content,
            remote_content=remote_content,
            local_modified=self._file_cache[path].modified_at if path in self._file_cache else int(time.time()),
            remote_modified=int(time.time()),
        )
        
        self._conflicts.append(conflict)
        self._file_cache[path].sync_status = SyncStatus.CONFLICT
        
        logger.warning(f"Sync conflict detected for {path}")
    
    async def _watch_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._check_file_changes()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                await asyncio.sleep(1)
    
    async def _check_file_changes(self):
        """检查文件变化"""
        for path, callbacks in self._watch_callbacks.items():
            try:
                content = await self.read_file(path)
                if content is None:
                    continue
                
                cached = self._file_cache.get(path)
                if cached:
                    new_hash = self._calculate_hash(content)
                    if new_hash != cached.hash:
                        for callback in callbacks:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(path, content)
                                else:
                                    callback(path, content)
                            except Exception as e:
                                logger.error(f"Error in watch callback: {e}")
            except Exception as e:
                logger.error(f"Error checking file {path}: {e}")
    
    def _calculate_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _path_to_doc_id(self, path: str) -> str:
        """路径转文档 ID"""
        return hashlib.md5(path.encode()).hexdigest()[:16]
    
    def _infer_doc_type(self, path: str) -> str:
        """推断文档类型"""
        path_lower = path.lower()
        
        if path_lower.endswith('.md'):
            return 'markdown'
        elif path_lower.endswith('.py'):
            return 'python'
        elif path_lower.endswith('.js') or path_lower.endswith('.ts'):
            return 'javascript'
        elif path_lower.endswith('.json'):
            return 'json'
        else:
            return 'other'
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取同步统计"""
        by_status = {}
        for info in self._file_cache.values():
            status = info.sync_status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_files": len(self._file_cache),
            "by_status": by_status,
            "conflicts": len(self._conflicts),
            "watched_files": len(self._watch_callbacks),
        }

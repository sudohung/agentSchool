"""锁管理器 - 完整的文档锁管理."""

from __future__ import annotations

import asyncio
import hashlib
import time
from enum import Enum
from typing import Optional, Dict, List, Set
from datetime import datetime
import logging

from .models import Document

logger = logging.getLogger(__name__)


class LockType(Enum):
    """锁类型"""
    READ = "read"
    WRITE = "write"


class LockStatus(Enum):
    """锁状态"""
    PENDING = "pending"
    ACQUIRED = "acquired"
    RELEASED = "released"
    EXPIRED = "expired"


class DeadlockError(Exception):
    """死锁异常"""
    pass


class LockTimeoutError(Exception):
    """锁超时异常"""
    pass


class DocumentLock:
    """文档锁"""
    
    def __init__(
        self,
        lock_id: str,
        document_id: str,
        lock_type: LockType,
        holder: str,
        acquired_at: int,
        expires_at: int,
        status: LockStatus = LockStatus.PENDING,
    ):
        self.lock_id = lock_id
        self.document_id = document_id
        self.lock_type = lock_type
        self.holder = holder
        self.acquired_at = acquired_at
        self.expires_at = expires_at
        self.status = status


class LockManager:
    """
    文档锁管理器
    
    功能：
    - 读写锁 (共享/独占)
    - 锁超时自动释放
    - 死锁检测
    - 锁等待队列
    """
    
    def __init__(
        self,
        default_timeout: int = 300,
        deadlock_check_interval: int = 10,
    ):
        """
        初始化锁管理器
        
        Args:
            default_timeout: 默认锁超时时间（秒）
            deadlock_check_interval: 死锁检测间隔（秒）
        """
        self.default_timeout = default_timeout
        self.deadlock_check_interval = deadlock_check_interval
        
        self._locks: Dict[str, List[DocumentLock]] = {}
        self._wait_queue: Dict[str, List[tuple]] = {}
        self._holder_index: Dict[str, List[str]] = {}
        self._lock_by_id: Dict[str, DocumentLock] = {}
        self._async_lock = asyncio.Lock()
        
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动锁管理器"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("LockManager started")
    
    async def stop(self):
        """停止锁管理器"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("LockManager stopped")
    
    async def acquire_read_lock(
        self,
        document_id: str,
        holder: str,
        timeout: Optional[int] = None,
    ) -> DocumentLock:
        """
        获取读锁
        
        读锁是共享的，多个 Agent 可以同时持有读锁，
        但不能在有写锁时获取读锁。
        """
        return await self._acquire_lock(
            document_id=document_id,
            lock_type=LockType.READ,
            holder=holder,
            timeout=timeout,
        )
    
    async def acquire_write_lock(
        self,
        document_id: str,
        holder: str,
        timeout: Optional[int] = None,
    ) -> DocumentLock:
        """
        获取写锁
        
        写锁是独占的，不能有其他的读锁或写锁。
        """
        return await self._acquire_lock(
            document_id=document_id,
            lock_type=LockType.WRITE,
            holder=holder,
            timeout=timeout,
        )
    
    async def release_lock(self, lock_id: str) -> bool:
        """
        释放锁
        
        Args:
            lock_id: 锁 ID
            
        Returns:
            bool: 是否成功释放
        """
        async with self._async_lock:
            lock = self._lock_by_id.get(lock_id)
            if not lock:
                return False
            
            document_id = lock.document_id
            
            if document_id in self._locks:
                self._locks[document_id] = [
                    l for l in self._locks[document_id] 
                    if l.lock_id != lock_id
                ]
            
            if lock.holder in self._holder_index:
                self._holder_index[lock.holder] = [
                    lid for lid in self._holder_index[lock.holder]
                    if lid != lock_id
                ]
            
            del self._lock_by_id[lock_id]
            lock.status = LockStatus.RELEASED
            
            await self._notify_waiters(document_id)
            
            logger.debug(f"Lock released: {lock_id} by {lock.holder}")
            return True
    
    async def release_all_locks(self, holder: str) -> int:
        """
        释放某个持有者的所有锁
        
        Args:
            holder: 持有者
            
        Returns:
            int: 释放的锁数量
        """
        lock_ids = self._holder_index.get(holder, []).copy()
        count = 0
        
        for lock_id in lock_ids:
            if await self.release_lock(lock_id):
                count += 1
        
        return count
    
    async def get_lock_info(self, document_id: str) -> List[DocumentLock]:
        """获取文档的锁信息"""
        return self._locks.get(document_id, []).copy()
    
    async def is_locked(self, document_id: str) -> bool:
        """检查文档是否被锁定"""
        return document_id in self._locks and len(self._locks[document_id]) > 0
    
    async def _acquire_lock(
        self,
        document_id: str,
        lock_type: LockType,
        holder: str,
        timeout: Optional[int] = None,
    ) -> DocumentLock:
        """内部获取锁方法"""
        timeout = timeout or self.default_timeout
        
        lock = DocumentLock(
            lock_id=self._generate_lock_id(document_id, holder),
            document_id=document_id,
            lock_type=lock_type,
            holder=holder,
            acquired_at=int(time.time()),
            expires_at=int(time.time()) + timeout,
            status=LockStatus.PENDING,
        )
        
        can_acquire = await self._can_acquire_lock(document_id, lock_type, holder)
        
        if can_acquire:
            async with self._async_lock:
                await self._register_lock(lock)
            return lock
        
        event = asyncio.Event()
        wait_entry = (lock, event)
        
        if document_id not in self._wait_queue:
            self._wait_queue[document_id] = []
        self._wait_queue[document_id].append(wait_entry)
        
        if await self._detect_deadlock(holder, document_id):
            self._wait_queue[document_id].remove(wait_entry)
            raise DeadlockError(f"Deadlock detected for {holder} on {document_id}")
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            
            async with self._async_lock:
                await self._register_lock(lock)
            
            return lock
            
        except asyncio.TimeoutError:
            if document_id in self._wait_queue:
                self._wait_queue[document_id] = [
                    w for w in self._wait_queue[document_id]
                    if w[0].lock_id != lock.lock_id
                ]
            raise LockTimeoutError(f"Timeout acquiring {lock_type.value} lock on {document_id}")
    
    async def _can_acquire_lock(
        self,
        document_id: str,
        lock_type: LockType,
        holder: str,
    ) -> bool:
        """检查是否可以获取锁"""
        existing_locks = self._locks.get(document_id, [])
        
        active_locks = [
            l for l in existing_locks
            if l.status == LockStatus.ACQUIRED and l.expires_at > int(time.time())
        ]
        
        if not active_locks:
            return True
        
        if lock_type == LockType.READ:
            has_write_lock = any(
                l.lock_type == LockType.WRITE for l in active_locks
            )
            return not has_write_lock
        
        else:
            return len(active_locks) == 0
    
    async def _register_lock(self, lock: DocumentLock):
        """注册锁"""
        lock.status = LockStatus.ACQUIRED
        
        if lock.document_id not in self._locks:
            self._locks[lock.document_id] = []
        self._locks[lock.document_id].append(lock)
        
        if lock.holder not in self._holder_index:
            self._holder_index[lock.holder] = []
        self._holder_index[lock.holder].append(lock.lock_id)
        
        self._lock_by_id[lock.lock_id] = lock
        
        logger.debug(f"Lock acquired: {lock.lock_id} ({lock.lock_type.value}) by {lock.holder}")
    
    async def _notify_waiters(self, document_id: str):
        """通知等待者"""
        wait_queue = self._wait_queue.get(document_id, [])
        
        for lock, event in wait_queue:
            can_acquire = await self._can_acquire_lock(
                document_id,
                lock.lock_type,
                lock.holder
            )
            if can_acquire:
                event.set()
    
    async def _detect_deadlock(self, holder: str, document_id: str) -> bool:
        """
        死锁检测
        
        使用等待图检测循环等待
        """
        wait_graph: Dict[str, Set[str]] = {}
        
        for doc_id, waiters in self._wait_queue.items():
            for lock, _ in waiters:
                if lock.holder not in wait_graph:
                    wait_graph[lock.holder] = set()
                
                for existing_lock in self._locks.get(doc_id, []):
                    wait_graph[lock.holder].add(existing_lock.holder)
        
        visited = set()
        path = set()
        
        def has_cycle(node: str) -> bool:
            if node in path:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            path.add(node)
            
            for neighbor in wait_graph.get(node, set()):
                if has_cycle(neighbor):
                    return True
            
            path.remove(node)
            return False
        
        return has_cycle(holder)
    
    def _generate_lock_id(self, document_id: str, holder: str) -> str:
        """生成锁 ID"""
        timestamp = int(time.time() * 1000)
        data = f"{document_id}:{holder}:{timestamp}"
        return "lock_" + hashlib.md5(data.encode()).hexdigest()[:12]
    
    async def _cleanup_loop(self):
        """清理过期锁的后台任务"""
        while self._running:
            try:
                await self._cleanup_expired_locks()
                await asyncio.sleep(self.deadlock_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired_locks(self):
        """清理过期锁"""
        now = int(time.time())
        expired_locks = []
        
        async with self._async_lock:
            for document_id, locks in list(self._locks.items()):
                for lock in locks[:]:
                    if lock.expires_at < now:
                        lock.status = LockStatus.EXPIRED
                        expired_locks.append(lock.lock_id)
                        locks.remove(lock)
                        
                        logger.warning(f"Lock expired: {lock.lock_id} by {lock.holder}")
                
                if not locks:
                    del self._locks[document_id]
        
        for document_id in set(l.split('_')[0] for l in expired_locks):
            await self._notify_waiters(document_id)
    
    def get_statistics(self) -> Dict:
        """获取锁统计信息"""
        total_locks = sum(len(locks) for locks in self._locks.values())
        total_waiters = sum(len(waiters) for waiters in self._wait_queue.values())
        
        locks_by_type = {
            LockType.READ.value: 0,
            LockType.WRITE.value: 0,
        }
        
        for locks in self._locks.values():
            for lock in locks:
                locks_by_type[lock.lock_type.value] += 1
        
        return {
            "total_active_locks": total_locks,
            "total_waiters": total_waiters,
            "locks_by_type": locks_by_type,
            "documents_locked": len(self._locks),
        }

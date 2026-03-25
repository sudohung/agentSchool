"""性能分析器模块."""

from __future__ import annotations

import time
import json
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
import logging
import functools

logger = logging.getLogger(__name__)


@dataclass
class ProfileRecord:
    """性能记录"""
    
    agent_id: str
    method_name: str
    start_time: float
    end_time: float
    duration_ms: float
    memory_before: int = 0
    memory_after: int = 0
    memory_delta: int = 0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "method_name": self.method_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "memory_before": self.memory_before,
            "memory_after": self.memory_after,
            "memory_delta": self.memory_delta,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class AgentStats:
    """Agent 统计信息"""
    
    agent_id: str
    total_calls: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    success_count: int = 0
    error_count: int = 0
    total_memory_delta: int = 0
    
    def update(self, record: ProfileRecord):
        self.total_calls += 1
        self.total_time_ms += record.duration_ms
        self.avg_time_ms = self.total_time_ms / self.total_calls
        self.min_time_ms = min(self.min_time_ms, record.duration_ms)
        self.max_time_ms = max(self.max_time_ms, record.duration_ms)
        self.total_memory_delta += record.memory_delta
        
        if record.success:
            self.success_count += 1
        else:
            self.error_count += 1


@dataclass
class MethodStats:
    """方法统计信息"""
    
    method_name: str
    total_calls: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    
    def update(self, record: ProfileRecord):
        self.total_calls += 1
        self.total_time_ms += record.duration_ms
        self.avg_time_ms = self.total_time_ms / self.total_calls
        self.min_time_ms = min(self.min_time_ms, record.duration_ms)
        self.max_time_ms = max(self.max_time_ms, record.duration_ms)


@dataclass
class Bottleneck:
    """性能瓶颈"""
    
    agent_id: str
    method_name: str
    duration_ms: float
    percentage: float
    severity: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "method_name": self.method_name,
            "duration_ms": self.duration_ms,
            "percentage": self.percentage,
            "severity": self.severity,
        }


@dataclass
class ProfileReport:
    """性能分析报告"""
    
    session_id: str
    start_time: float
    end_time: float
    total_time_ms: float
    total_records: int
    agent_stats: Dict[str, AgentStats]
    method_stats: Dict[str, MethodStats]
    memory_peak: int
    bottlenecks: List[Bottleneck]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_time_ms": self.total_time_ms,
            "total_records": self.total_records,
            "agent_stats": {
                k: {
                    "total_calls": v.total_calls,
                    "total_time_ms": v.total_time_ms,
                    "avg_time_ms": v.avg_time_ms,
                    "min_time_ms": v.min_time_ms if v.min_time_ms != float("inf") else 0,
                    "max_time_ms": v.max_time_ms,
                    "success_rate": v.success_count / v.total_calls if v.total_calls > 0 else 0,
                    "error_count": v.error_count,
                    "total_memory_delta": v.total_memory_delta,
                }
                for k, v in self.agent_stats.items()
            },
            "method_stats": {
                k: {
                    "total_calls": v.total_calls,
                    "total_time_ms": v.total_time_ms,
                    "avg_time_ms": v.avg_time_ms,
                    "min_time_ms": v.min_time_ms if v.min_time_ms != float("inf") else 0,
                    "max_time_ms": v.max_time_ms,
                }
                for k, v in self.method_stats.items()
            },
            "memory_peak": self.memory_peak,
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
        }
    
    def save(self, path: Path):
        """保存报告到文件"""
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        logger.info(f"Profile report saved to: {path}")
    
    def print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 60)
        print("📊 Performance Profile Report")
        print("=" * 60)
        print(f"Session ID: {self.session_id}")
        print(f"Total Time: {self.total_time_ms:.2f} ms")
        print(f"Total Records: {self.total_records}")
        print(f"Memory Peak: {self.memory_peak / 1024:.2f} KB")
        print("-" * 60)
        
        if self.agent_stats:
            print("\n📈 Agent Statistics:")
            print(f"{'Agent ID':<20} {'Calls':>8} {'Avg(ms)':>10} {'Total(ms)':>12} {'Errors':>8}")
            print("-" * 60)
            for agent_id, stats in sorted(
                self.agent_stats.items(),
                key=lambda x: x[1].total_time_ms,
                reverse=True
            ):
                print(
                    f"{agent_id:<20} {stats.total_calls:>8} "
                    f"{stats.avg_time_ms:>10.2f} {stats.total_time_ms:>12.2f} "
                    f"{stats.error_count:>8}"
                )
        
        if self.bottlenecks:
            print("\n⚠️  Top Bottlenecks:")
            for b in self.bottlenecks[:5]:
                print(
                    f"  {b.agent_id}.{b.method_name}: "
                    f"{b.duration_ms:.2f}ms ({b.percentage:.1f}%) [{b.severity}]"
                )
        
        print("=" * 60 + "\n")


class Profiler:
    """
    性能分析器
    
    功能：
    1. 记录 Agent 方法执行时间
    2. 追踪内存使用
    3. 识别性能瓶颈
    4. 生成分析报告
    """
    
    def __init__(self, track_memory: bool = True):
        self.track_memory = track_memory
        self._session_id: Optional[str] = None
        self._start_time: Optional[float] = None
        self._records: List[ProfileRecord] = []
        self._memory_peak: int = 0
        self._profiling: bool = False
    
    def start_profiling(self, session_id: Optional[str] = None) -> str:
        """开始性能分析"""
        if self._profiling:
            logger.warning("Profiler already running")
            return self._session_id
        
        self._session_id = session_id or f"profile_{int(time.time())}"
        self._start_time = time.perf_counter()
        self._records = []
        self._memory_peak = 0
        self._profiling = True
        
        if self.track_memory:
            tracemalloc.start()
        
        logger.info(f"Profiling started: {self._session_id}")
        return self._session_id
    
    def stop_profiling(self) -> ProfileReport:
        """停止性能分析并生成报告"""
        if not self._profiling:
            raise RuntimeError("Profiler not running")
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - self._start_time) * 1000
        
        if self.track_memory:
            self._memory_peak = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
        
        self._profiling = False
        
        agent_stats = self._calculate_agent_stats()
        method_stats = self._calculate_method_stats()
        bottlenecks = self._identify_bottlenecks(total_time_ms)
        
        report = ProfileReport(
            session_id=self._session_id,
            start_time=self._start_time,
            end_time=end_time,
            total_time_ms=total_time_ms,
            total_records=len(self._records),
            agent_stats=agent_stats,
            method_stats=method_stats,
            memory_peak=self._memory_peak,
            bottlenecks=bottlenecks,
        )
        
        logger.info(f"Profiling stopped: {self._session_id}, {len(self._records)} records")
        return report
    
    def record(
        self,
        agent_id: str,
        method_name: str,
        duration_ms: float,
        memory_delta: int = 0,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录一次执行"""
        if not self._profiling:
            return
        
        record = ProfileRecord(
            agent_id=agent_id,
            method_name=method_name,
            start_time=time.perf_counter(),
            end_time=time.perf_counter(),
            duration_ms=duration_ms,
            memory_delta=memory_delta,
            success=success,
            error=error,
            metadata=metadata or {},
        )
        
        self._records.append(record)
        self._memory_peak = max(self._memory_peak, memory_delta)
    
    @contextmanager
    def profile_method(
        self,
        agent_id: str,
        method_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """上下文管理器方式记录方法执行"""
        if not self._profiling:
            yield None
            return
        
        memory_before = 0
        if self.track_memory and tracemalloc.is_tracing():
            memory_before = tracemalloc.get_traced_memory()[0]
        
        start_time = time.perf_counter()
        error = None
        success = True
        
        try:
            yield None
        except Exception as e:
            error = str(e)
            success = False
            raise
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            memory_after = 0
            memory_delta = 0
            if self.track_memory and tracemalloc.is_tracing():
                memory_after = tracemalloc.get_traced_memory()[0]
                memory_delta = memory_after - memory_before
            
            self.record(
                agent_id=agent_id,
                method_name=method_name,
                duration_ms=duration_ms,
                memory_delta=memory_delta,
                success=success,
                error=error,
                metadata=metadata,
            )
    
    def profile_function(
        self,
        agent_id: str,
        method_name: Optional[str] = None,
    ):
        """装饰器方式记录函数执行"""
        def decorator(func):
            name = method_name or func.__name__
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.profile_method(agent_id, name):
                    return await func(*args, **kwargs)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.profile_method(agent_id, name):
                    return func(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    def _calculate_agent_stats(self) -> Dict[str, AgentStats]:
        """计算 Agent 统计"""
        stats: Dict[str, AgentStats] = {}
        
        for record in self._records:
            if record.agent_id not in stats:
                stats[record.agent_id] = AgentStats(agent_id=record.agent_id)
            stats[record.agent_id].update(record)
        
        return stats
    
    def _calculate_method_stats(self) -> Dict[str, MethodStats]:
        """计算方法统计"""
        stats: Dict[str, MethodStats] = {}
        
        for record in self._records:
            key = f"{record.agent_id}.{record.method_name}"
            if key not in stats:
                stats[key] = MethodStats(method_name=key)
            stats[key].update(record)
        
        return stats
    
    def _identify_bottlenecks(
        self,
        total_time_ms: float,
        threshold_percent: float = 5.0,
    ) -> List[Bottleneck]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        method_stats = self._calculate_method_stats()
        
        for key, stats in method_stats.items():
            if total_time_ms > 0:
                percentage = (stats.total_time_ms / total_time_ms) * 100
            else:
                percentage = 0
            
            if percentage >= threshold_percent:
                if percentage >= 20:
                    severity = "critical"
                elif percentage >= 10:
                    severity = "high"
                else:
                    severity = "medium"
                
                agent_id, method_name = key.split(".", 1) if "." in key else (key, "")
                
                bottlenecks.append(Bottleneck(
                    agent_id=agent_id,
                    method_name=method_name,
                    duration_ms=stats.total_time_ms,
                    percentage=percentage,
                    severity=severity,
                ))
        
        bottlenecks.sort(key=lambda b: b.duration_ms, reverse=True)
        return bottlenecks
    
    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前统计"""
        if not self._profiling:
            return {"status": "not_profiling"}
        
        elapsed = (time.perf_counter() - self._start_time) * 1000
        
        return {
            "status": "profiling",
            "session_id": self._session_id,
            "elapsed_ms": elapsed,
            "record_count": len(self._records),
            "memory_peak": self._memory_peak,
        }
    
    @property
    def is_profiling(self) -> bool:
        return self._profiling


import asyncio
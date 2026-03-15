"""监控指标收集器."""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from infrastructure.exceptions import MetricsCollectionError, MetricsExportError
from infrastructure.monitoring.types import Metric, MetricType, MetricSnapshot


@dataclass
class MetricRegistry:
    """指标注册表"""
    
    counters: Dict[str, float] = field(default_factory=dict)
    gauges: Dict[str, float] = field(default_factory=dict)
    histograms: Dict[str, List[float]] = field(default_factory=dict)
    summaries: Dict[str, List[float]] = field(default_factory=dict)


class MetricsCollector:
    """
    指标收集器
    
    用于收集和管理系统指标，支持 Counter、Gauge、Histogram 等类型
    """
    
    def __init__(self, prefix: str = "ats"):
        """
        初始化指标收集器
        
        Args:
            prefix: 指标名称前缀
        """
        self.prefix = prefix
        self._registry = MetricRegistry()
        self._lock = asyncio.Lock()
        self._snapshots: List[MetricSnapshot] = []
    
    async def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        计数器增加
        
        Args:
            name: 指标名称
            value: 增加的值
            labels: 标签字典
        """
        async with self._lock:
            full_name = self._make_full_name(name, labels)
            self._registry.counters[full_name] = self._registry.counters.get(full_name, 0) + value
            
            if value < 0:
                raise MetricsCollectionError(
                    "Counter increment value cannot be negative",
                    errors=[f"value={value}"]
                )
    
    async def decrement(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        计数器减少（用于 Gauge）
        
        Args:
            name: 指标名称
            value: 减少的值
            labels: 标签字典
        """
        async with self._lock:
            full_name = self._make_full_name(name, labels)
            self._registry.gauges[full_name] = self._registry.gauges.get(full_name, 0) - value
    
    async def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        设置仪表值
        
        Args:
            name: 指标名称
            value: 仪表值
            labels: 标签字典
        """
        async with self._lock:
            full_name = self._make_full_name(name, labels)
            self._registry.gauges[full_name] = value
    
    async def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        记录直方图值
        
        Args:
            name: 指标名称
            value: 观察值
            labels: 标签字典
        """
        async with self._lock:
            full_name = self._make_full_name(name, labels)
            if full_name not in self._registry.histograms:
                self._registry.histograms[full_name] = []
            self._registry.histograms[full_name].append(value)
    
    async def summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        记录摘要值
        
        Args:
            name: 指标名称
            value: 观察值
            labels: 标签字典
        """
        async with self._lock:
            full_name = self._make_full_name(name, labels)
            if full_name not in self._registry.summaries:
                self._registry.summaries[full_name] = []
            self._registry.summaries[full_name].append(value)
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """获取计数器值"""
        full_name = self._make_full_name(name, labels)
        return self._registry.counters.get(full_name, 0.0)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """获取仪表值"""
        full_name = self._make_full_name(name, labels)
        return self._registry.gauges.get(full_name, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        获取直方图统计
        
        Returns:
            包含 count, sum, avg, min, max 的字典
        """
        full_name = self._make_full_name(name, labels)
        values = self._registry.histograms.get(full_name, [])
        
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}
        
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }
    
    def create_snapshot(self) -> MetricSnapshot:
        """
        创建当前指标快照
        
        Returns:
            MetricSnapshot 对象
        """
        snapshot = MetricSnapshot()
        
        # 添加 counters
        for name, value in self._registry.counters.items():
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.COUNTER,
                timestamp=int(time.time())
            )
            snapshot.add(metric)
        
        # 添加 gauges
        for name, value in self._registry.gauges.items():
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                timestamp=int(time.time())
            )
            snapshot.add(metric)
        
        # 添加 histogram 统计
        for name, values in self._registry.histograms.items():
            if values:
                # 添加 count
                snapshot.add(Metric(
                    name=f"{name}_count",
                    value=len(values),
                    metric_type=MetricType.GAUGE
                ))
                # 添加 sum
                snapshot.add(Metric(
                    name=f"{name}_sum",
                    value=sum(values),
                    metric_type=MetricType.GAUGE
                ))
                # 添加 avg
                snapshot.add(Metric(
                    name=f"{name}_avg",
                    value=sum(values) / len(values),
                    metric_type=MetricType.GAUGE
                ))
        
        self._snapshots.append(snapshot)
        return snapshot
    
    def export_prometheus(self) -> str:
        """
        导出为 Prometheus 格式
        
        Returns:
            Prometheus 格式的字符串
        """
        snapshot = self.create_snapshot()
        return snapshot.to_prometheus()
    
    def export_json(self) -> Dict[str, Any]:
        """
        导出为 JSON 格式
        
        Returns:
            JSON 字典
        """
        return {
            "timestamp": int(time.time()),
            "counters": dict(self._registry.counters),
            "gauges": dict(self._registry.gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0
                }
                for name, values in self._registry.histograms.items()
            },
        }
    
    def _make_full_name(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """生成完整指标名称"""
        full_name = f"{self.prefix}_{name}" if self.prefix else name
        if labels:
            labels_str = "_".join(f"{k}_{v}" for k, v in sorted(labels.items()))
            full_name = f"{full_name}_{labels_str}"
        return full_name
    
    def reset(self):
        """重置所有指标"""
        self._registry = MetricRegistry()
    
    def clear_snapshots(self):
        """清除快照历史"""
        self._snapshots.clear()

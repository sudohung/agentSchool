"""监控系统类型定义."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time

from infrastructure.exceptions import MetricValidationError


class MetricType(Enum):
    """指标类型"""
    
    COUNTER = "counter"      # 单调递增（如请求次数）
    GAUGE = "gauge"          # 可增可减（如内存使用）
    HISTOGRAM = "histogram"  # 分布统计（如响应时间）
    SUMMARY = "summary"      # 摘要统计（如分位数）


@dataclass
class Metric:
    """指标数据模型"""
    
    name: str
    value: float
    timestamp: int = field(default_factory=lambda: int(time.time()))
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    
    def __post_init__(self):
        """验证指标数据"""
        if not self.name or not isinstance(self.name, str):
            raise MetricValidationError(
                "Metric name must be a non-empty string",
                errors=[f"Invalid name: {self.name}"]
            )
        if not isinstance(self.value, (int, float)):
            raise MetricValidationError(
                "Metric value must be a number",
                errors=[f"Invalid value type: {type(self.value)}"]
            )
        if self.value < 0 and self.metric_type == MetricType.COUNTER:
            raise MetricValidationError(
                "Counter value cannot be negative",
                errors=[f"Negative counter value: {self.value}"]
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels,
            "type": self.metric_type.value,
        }
    
    def with_label(self, key: str, value: str) -> 'Metric':
        """添加标签"""
        self.labels[key] = value
        return self


@dataclass
class MetricSnapshot:
    """指标快照"""
    
    metrics: list[Metric] = field(default_factory=list)
    timestamp: int = field(default_factory=lambda: int(time.time()))
    
    def add(self, metric: Metric):
        """添加指标"""
        self.metrics.append(metric)
    
    def to_prometheus(self) -> str:
        """导出为 Prometheus 格式"""
        lines = []
        metrics_by_type = {}
        
        # 按类型分组
        for metric in self.metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        # 生成 Prometheus 格式
        for metric_type, metrics in metrics_by_type.items():
            for metric in metrics:
                lines.append(f"# TYPE {metric.name} {metric_type.value}")
                if metric.labels:
                    labels_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
                    lines.append(f"{metric.name}{{{labels_str}}} {metric.value}")
                else:
                    lines.append(f"{metric.name} {metric.value}")
        
        return "\n".join(lines)

# Phase 6: 工具和基础设施设计

> 版本：1.1（已修复 P0/P1 问题）
> 创建日期：2026-03-15
> 审查日期：2026-03-15
> 审查评分：4.3/5.0
> 状态：设计完成（已修复 P0/P1 问题）

---

## 1. 概述

### 1.1 目标

构建完善的基础设施，包括监控系统、日志系统、配置管理和开发工具，为 Agent Team System 提供生产级的运维支持。

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| 🔍 **可观测性** | 系统状态完全可见 |
| 📊 **可度量性** | 关键指标可量化 |
| ⚙️ **可配置性** | 运行时配置灵活 |
| 🛠️ **易用性** | 开发调试便捷 |
| 🔒 **安全性** | 敏感信息加密，日志脱敏 |
| 🚀 **高性能** | 异步处理，批量操作 |

### 1.3 系统定位

```
┌─────────────────────────────────────────────────────────┐
│               Agent Team System 架构                     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Phase 1-5  │  │  Phase 6    │  │  Phase 7-8  │     │
│  │  核心功能   │──│  基础设施   │──│  文档测试   │     │
│  │  (已完成)   │  │  (设计中)   │  │  (待实施)   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         │                │                  │           │
│         ↓                ↓                  ↓           │
│   业务逻辑层        监控/日志/配置        文档/验证      │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 异常处理设计

### 2.1 异常层次结构

```python
class InfrastructureError(Exception):
    """基础设施异常基类"""
    def __init__(self, message: str, code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or "INFRA_ERROR"
        self.details = details or {}

# 监控系统异常
class MetricsError(InfrastructureError):
    """指标收集异常"""
    code = "METRICS_ERROR"

class MetricsCollectionError(MetricsError):
    """指标收集失败"""
    code = "METRICS_COLLECTION_ERROR"

class MetricsExportError(MetricsError):
    """指标导出失败"""
    code = "METRICS_EXPORT_ERROR"

# 日志系统异常
class LogError(InfrastructureError):
    """日志系统异常"""
    code = "LOG_ERROR"

class LogWriteError(LogError):
    """日志写入失败"""
    code = "LOG_WRITE_ERROR"

class LogFormatError(LogError):
    """日志格式错误"""
    code = "LOG_FORMAT_ERROR"

# 配置管理异常
class ConfigurationError(InfrastructureError):
    """配置异常"""
    code = "CONFIG_ERROR"

class ConfigLoadError(ConfigurationError):
    """配置加载失败"""
    code = "CONFIG_LOAD_ERROR"

class ConfigValidationError(ConfigurationError):
    """配置验证失败"""
    code = "CONFIG_VALIDATION_ERROR"
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []

# 开发工具异常
class DevToolsError(InfrastructureError):
    """开发工具异常"""
    code = "DEVTOOLS_ERROR"

class DebuggerError(DevToolsError):
    """调试器异常"""
    code = "DEBUGGER_ERROR"

class CLIError(DevToolsError):
    """CLI 工具异常"""
    code = "CLI_ERROR"
```

### 2.2 错误处理策略

| 错误类型 | 处理策略 | 重试机制 |
|----------|----------|----------|
| MetricsCollectionError | 记录错误，继续运行 | 否 |
| MetricsExportError | 缓存指标，下次重试 | 是（3 次） |
| LogWriteError | 降级到备用处理器 | 否 |
| ConfigLoadError | 使用默认配置 | 否 |
| ConfigValidationError | 阻止启动 | 否 |

---

## 3. 模块设计

### 3.1 监控系统 (Monitoring)

```
infrastructure/
├── monitoring/
│   ├── __init__.py
│   ├── types.py          # 类型定义
│   ├── metrics.py        # 指标收集
│   ├── collector.py      # 数据采集器
│   ├── exporter.py       # 数据导出器
│   └── dashboard.py      # 仪表盘数据
```

#### 3.1.1 核心指标

| 指标类型 | 指标名称 | 类型 | 说明 |
|----------|----------|------|------|
| **系统指标** | `system_uptime` | Gauge | 系统运行时间（秒） |
| | `agent_count` | Gauge | Agent 实例数量 |
| | `document_count` | Gauge | 文档总数 |
| | `request_count` | Gauge | 诉求总数 |
| **性能指标** | `iteration_duration` | Histogram | 迭代耗时（秒） |
| | `delivery_duration` | Histogram | 交付耗时（秒） |
| | `feedback_resolution_time` | Histogram | 反馈处理时间（秒） |
| | `document_size_bytes` | Gauge | 文档大小 |
| **业务指标** | `iteration_count` | Counter | 迭代次数 |
| | `setback_count` | Counter | 挫折次数 |
| | `delivery_success_rate` | Gauge | 交付成功率 |
| | `feedback_count` | Counter | 反馈数量 |
| **队列指标** | `request_queue_size` | Gauge | 诉求队列大小 |
| | `error_rate` | Gauge | 错误率 |

#### 3.1.2 类型定义

```python
from enum import Enum

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
    timestamp: int
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    
    def __post_init__(self):
        """验证指标数据"""
        if not self.name or not isinstance(self.name, str):
            raise MetricsError("Metric name must be a non-empty string")
        if not isinstance(self.value, (int, float)):
            raise MetricsError("Metric value must be a number")
        if self.value < 0 and self.metric_type == MetricType.COUNTER:
            raise MetricsError("Counter value cannot be negative")
```

#### 3.1.3 MetricsCollector 设计

```python
class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, prefix: str = "ats"):
        self.prefix = prefix
        self._metrics: Dict[str, List[Metric]] = {}
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
    
    async def increment(self, name: str, value: float = 1.0, labels: Dict = None):
        """计数器增加"""
        async with self._lock:
            full_name = f"{self.prefix}_{name}"
            self._counters[full_name] = self._counters.get(full_name, 0) + value
    
    async def gauge(self, name: str, value: float, labels: Dict = None):
        """设置仪表值"""
        async with self._lock:
            full_name = f"{self.prefix}_{name}"
            self._gauges[full_name] = value
    
    async def histogram(self, name: str, value: float, labels: Dict = None):
        """记录直方图值"""
        async with self._lock:
            full_name = f"{self.prefix}_{name}"
            if full_name not in self._histograms:
                self._histograms[full_name] = []
            self._histograms[full_name].append(value)
    
    def export_prometheus(self) -> str:
        """导出 Prometheus 格式"""
        lines = []
        for name, value in self._counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        for name, value in self._gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        return "\n".join(lines)
```

---

## 4. 实施计划

### 4.1 任务分解

| 任务 | 文件 | 预计工时 | 优先级 |
|------|------|----------|--------|
| 异常处理设计 | infrastructure/exceptions.py | 0.5h | P0 |
| 监控类型定义 | monitoring/types.py | 0.5h | P0 |
| 监控指标收集器 | monitoring/metrics.py | 1.5h | P0 |
| 日志配置模型 | logging/config.py | 0.5h | P0 |
| 结构化日志记录器 | logging/logger.py | 1h | P0 |
| 配置验证器 | config/validators.py | 0.5h | P0 |
| 配置管理器 | config/manager.py | 1h | P0 |
| 监控数据导出 | monitoring/exporter.py | 1h | P1 |
| 日志处理器 | logging/handlers.py | 1h | P1 |
| 性能分析工具 | devtools/profiler.py | 1h | P1 |
| Agent 调试器 | devtools/debugger.py | 1h | P1 |
| CLI 工具 | devtools/cli.py | 1.5h | P1 |
| 集成测试 | tests/test_infrastructure.py | 1h | P0 |

**总计**: 11 小时

### 4.2 实施顺序

```
Day 1: 核心模块与异常处理 (4h)
├── 1. infrastructure/exceptions.py (0.5h) ✅ P0
├── 2. monitoring/types.py + MetricType 定义 (0.5h) ✅ P0
├── 3. monitoring/metrics.py (1.5h) ⬜ P0
├── 4. logging/config.py + LogConfig 定义 (0.5h) ✅ P0
└── 5. logging/logger.py (1h) ⬜ P0

Day 2: 配置与验证 (3.5h)
├── 6. config/validators.py (0.5h) ✅ P0
├── 7. config/manager.py (1h) ⬜ P0
├── 8. monitoring/exporter.py (1h) ⬜ P1
├── 9. logging/handlers.py (1h) ⬜ P1
└── 10. 异常处理集成测试 (0.5h) ⬜ P0

Day 3: 开发工具与测试 (3.5h)
├── 11. devtools/profiler.py + ProfileResult (1h) ⬜ P1
├── 12. devtools/debugger.py (1h) ⬜ P1
├── 13. devtools/cli.py + typer 集成 (1h) ⬜ P1
└── 14. 集成测试 (0.5h) ⬜ P0
```

---

> 设计文档版本：1.1（已修复 P0/P1 问题）
> 审查状态：✅ 通过（4.3/5.0）
> 下一步：开始实施
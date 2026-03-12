"""挫折处理 - 完整版."""

from __future__ import annotations

import hashlib
import time
import asyncio
from enum import Enum
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field


class SetbackType(Enum):
    """挫折类型"""
    TECHNICAL_ERROR = "technical_error"
    TIMEOUT = "timeout"
    NO_RESPONSE = "no_response"
    CONFLICT = "conflict"
    BLOCKED = "blocked"
    QUALITY_ISSUE = "quality_issue"
    OTHER = "other"


class SetbackSeverity(Enum):
    """挫折严重程度"""
    LOW = "low"              # 低 - 自动恢复
    MEDIUM = "medium"        # 中 - 需要重试
    HIGH = "high"            # 高 - 需要人工介入
    CRITICAL = "critical"    # 严重 - 终止迭代


@dataclass
class Setback:
    """挫折记录"""
    id: str
    type: SetbackType
    severity: SetbackSeverity
    agent: str
    iteration: int
    description: str
    error_message: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: int = field(default_factory=lambda: int(time.time()))
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class RecoveryStrategy:
    """恢复策略"""
    name: str
    description: str
    applicable_types: List[SetbackType]
    max_retries: int = 3
    cooldown_seconds: int = 60
    action: Optional[Callable] = None


class SetbackHandler:
    """
    挫折处理器
    
    实现完整的挫折管理：
    - 记录和分类
    - 自动恢复策略
    - 模式分析
    - 可视化报告
    """
    
    def __init__(self):
        self._setbacks: List[Setback] = []
        self._patterns: Dict[str, int] = {}
        self._recovery_strategies: Dict[SetbackType, RecoveryStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认恢复策略"""
        
        # 1. 自动重试策略
        self._recovery_strategies[SetbackType.TECHNICAL_ERROR] = RecoveryStrategy(
            name="自动重试",
            description="遇到技术错误时自动重试",
            applicable_types=[SetbackType.TECHNICAL_ERROR],
            max_retries=3,
            cooldown_seconds=5,
        )
        
        # 2. 超时重试策略
        self._recovery_strategies[SetbackType.TIMEOUT] = RecoveryStrategy(
            name="超时重试",
            description="超时时增加超时时间后重试",
            applicable_types=[SetbackType.TIMEOUT],
            max_retries=2,
            cooldown_seconds=10,
        )
        
        # 3. 无响应处理
        self._recovery_strategies[SetbackType.NO_RESPONSE] = RecoveryStrategy(
            name="无响应处理",
            description="无响应时切换到备用方案",
            applicable_types=[SetbackType.NO_RESPONSE],
            max_retries=1,
            cooldown_seconds=30,
        )
        
        # 4. 冲突解决
        self._recovery_strategies[SetbackType.CONFLICT] = RecoveryStrategy(
            name="冲突解决",
            description="冲突时合并变更",
            applicable_types=[SetbackType.CONFLICT],
            max_retries=2,
            cooldown_seconds=15,
        )
        
        # 5. 阻塞解除
        self._recovery_strategies[SetbackType.BLOCKED] = RecoveryStrategy(
            name="阻塞解除",
            description="阻塞时寻求其他 Agent 帮助",
            applicable_types=[SetbackType.BLOCKED],
            max_retries=3,
            cooldown_seconds=60,
        )
        
        # 6. 质量问题处理
        self._recovery_strategies[SetbackType.QUALITY_ISSUE] = RecoveryStrategy(
            name="质量问题处理",
            description="质量问题时重新执行并审查",
            applicable_types=[SetbackType.QUALITY_ISSUE],
            max_retries=2,
            cooldown_seconds=30,
        )
    
    async def record_setback(
        self,
        agent: Any,
        iteration: int,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> Setback:
        """
        记录挫折
        
        Args:
            agent: 发生挫折的 Agent
            iteration: 当前迭代次数
            error: 异常对象
            context: 上下文信息
            
        Returns:
            挫折记录
        """
        # 1. 分类挫折
        setback_type = self._classify_setback(error)
        
        # 2. 评估严重程度
        severity = self._assess_severity(setback_type, error)
        
        # 3. 创建挫折记录
        setback = Setback(
            id=self._generate_id(),
            type=setback_type,
            severity=severity,
            agent=agent.role if hasattr(agent, 'role') else str(agent),
            iteration=iteration,
            description=str(error),
            error_message=str(error),
            context=context or {},
        )
        
        # 4. 保存记录
        self._setbacks.append(setback)
        
        # 5. 分析模式
        self._analyze_pattern(setback)
        
        return setback
    
    def _classify_setback(self, error: Exception) -> SetbackType:
        """分类挫折"""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return SetbackType.TIMEOUT
        
        if "no response" in error_str or "not found" in error_str:
            return SetbackType.NO_RESPONSE
        
        if "conflict" in error_str or "collision" in error_str:
            return SetbackType.CONFLICT
        
        if "blocked" in error_str or "deadlock" in error_str:
            return SetbackType.BLOCKED
        
        if "quality" in error_str or "invalid" in error_str or "failed validation" in error_str:
            return SetbackType.QUALITY_ISSUE
        
        if "error" in error_str or "exception" in error_str:
            return SetbackType.TECHNICAL_ERROR
        
        return SetbackType.OTHER
    
    def _assess_severity(
        self,
        setback_type: SetbackType,
        error: Exception,
    ) -> SetbackSeverity:
        """评估严重程度"""
        # 根据类型和错误消息评估
        if setback_type == SetbackType.TIMEOUT:
            return SetbackSeverity.MEDIUM
        
        if setback_type == SetbackType.NO_RESPONSE:
            return SetbackSeverity.MEDIUM
        
        if setback_type == SetbackType.CONFLICT:
            return SetbackSeverity.HIGH
        
        if setback_type == SetbackType.BLOCKED:
            return SetbackSeverity.HIGH
        
        if setback_type == SetbackType.QUALITY_ISSUE:
            return SetbackSeverity.MEDIUM
        
        if setback_type == SetbackType.TECHNICAL_ERROR:
            # 检查是否是关键错误
            error_str = str(error).lower()
            if "critical" in error_str or "fatal" in error_str:
                return SetbackSeverity.CRITICAL
            return SetbackSeverity.MEDIUM
        
        return SetbackSeverity.LOW
    
    async def attempt_recovery(
        self,
        setback: Setback,
        agent: Any,
        action: Callable,
    ) -> bool:
        """
        尝试恢复
        
        Args:
            setback: 挫折记录
            agent: Agent 实例
            action: 要重试的操作
            
        Returns:
            是否恢复成功
        """
        # 获取恢复策略
        strategy = self._recovery_strategies.get(setback.type)
        
        if not strategy:
            # 没有策略，尝试通用恢复
            return await self._generic_recovery(setback, action)
        
        # 检查重试次数
        if setback.retry_count >= strategy.max_retries:
            setback.resolved = False
            setback.resolution = f"超过最大重试次数 ({strategy.max_retries})"
            return False
        
        # 执行恢复
        try:
            # 冷却时间
            if strategy.cooldown_seconds > 0:
                await asyncio.sleep(strategy.cooldown_seconds)
            
            # 执行重试
            setback.retry_count += 1
            await action()
            
            # 恢复成功
            setback.resolved = True
            setback.resolution = f"通过 {strategy.name} 恢复成功 (重试 {setback.retry_count}/{strategy.max_retries})"
            setback.resolved_at = int(time.time())
            
            return True
            
        except Exception as e:
            # 恢复失败
            setback.description = f"{setback.description}; 恢复失败：{str(e)}"
            return False
    
    async def _generic_recovery(
        self,
        setback: Setback,
        action: Callable,
    ) -> bool:
        """通用恢复策略"""
        # 简单重试 3 次
        for i in range(3):
            try:
                await asyncio.sleep(5 * (i + 1))  # 递增延迟
                await action()
                setback.resolved = True
                setback.resolution = f"通用恢复成功 (重试 {i+1}/3)"
                setback.resolved_at = int(time.time())
                return True
            except Exception:
                continue
        
        return False
    
    def _analyze_pattern(self, setback: Setback):
        """分析挫折模式"""
        # 按 Agent 统计
        agent_key = f"agent:{setback.agent}"
        self._patterns[agent_key] = self._patterns.get(agent_key, 0) + 1
        
        # 按类型统计
        type_key = f"type:{setback.type.value}"
        self._patterns[type_key] = self._patterns.get(type_key, 0) + 1
        
        # 按迭代统计
        iteration_key = f"iteration:{setback.iteration}"
        self._patterns[iteration_key] = self._patterns.get(iteration_key, 0) + 1
    
    def get_patterns(self) -> Dict[str, int]:
        """获取挫折模式"""
        return self._patterns.copy()
    
    def get_setbacks(
        self,
        agent: Optional[str] = None,
        type: Optional[SetbackType] = None,
        severity: Optional[SetbackSeverity] = None,
        limit: int = 100,
    ) -> List[Setback]:
        """获取挫折记录"""
        results = self._setbacks
        
        if agent:
            results = [s for s in results if s.agent == agent]
        if type:
            results = [s for s in results if s.type == type]
        if severity:
            results = [s for s in results if s.severity == severity]
        
        return results[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._setbacks)
        resolved = sum(1 for s in self._setbacks if s.resolved)
        
        by_type = {}
        by_severity = {}
        by_agent = {}
        
        for setback in self._setbacks:
            # 按类型统计
            type_key = setback.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # 按严重程度统计
            severity_key = setback.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1
            
            # 按 Agent 统计
            agent_key = setback.agent
            by_agent[agent_key] = by_agent.get(agent_key, 0) + 1
        
        return {
            "total": total,
            "resolved": resolved,
            "unresolved": total - resolved,
            "resolution_rate": resolved / total if total > 0 else 0,
            "by_type": by_type,
            "by_severity": by_severity,
            "by_agent": by_agent,
            "patterns": self._patterns,
        }
    
    def generate_report(self) -> str:
        """生成挫折报告"""
        stats = self.get_statistics()
        
        report = []
        report.append("# 挫折处理报告")
        report.append("")
        report.append("## 总体统计")
        report.append(f"- 总挫折数：{stats['total']}")
        report.append(f"- 已解决：{stats['resolved']}")
        report.append(f"- 未解决：{stats['unresolved']}")
        report.append(f"- 解决率：{stats['resolution_rate']:.1%}")
        report.append("")
        
        report.append("## 按类型统计")
        for type_key, count in stats['by_type'].items():
            report.append(f"- {type_key}: {count}")
        report.append("")
        
        report.append("## 按严重程度统计")
        for severity_key, count in stats['by_severity'].items():
            report.append(f"- {severity_key}: {count}")
        report.append("")
        
        report.append("## 按 Agent 统计")
        for agent_key, count in stats['by_agent'].items():
            report.append(f"- {agent_key}: {count}")
        report.append("")
        
        if stats['patterns']:
            report.append("## 模式分析")
            for pattern_key, count in stats['patterns'].items():
                report.append(f"- {pattern_key}: {count}")
        
        return "\n".join(report)
    
    def _generate_id(self) -> str:
        """生成挫折 ID"""
        timestamp = int(time.time() * 1000)
        data = f"setback:{timestamp}"
        return "setback_" + hashlib.md5(data.encode()).hexdigest()[:12]

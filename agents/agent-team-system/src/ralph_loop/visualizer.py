"""迭代过程可视化."""

from __future__ import annotations

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class IterationMetrics:
    """迭代指标"""
    iteration_number: int
    start_time: int
    end_time: Optional[int] = None
    duration_seconds: float = 0.0
    agents_active: int = 0
    documents_read: int = 0
    documents_produced: int = 0
    requests_processed: int = 0
    requests_posted: int = 0
    setbacks_count: int = 0
    completion_score: float = 0.0
    status: str = "running"


@dataclass
class AgentMetrics:
    """Agent 指标"""
    role: str
    iterations_participated: int = 0
    documents_produced: int = 0
    requests_processed: int = 0
    setbacks_encountered: int = 0
    average_completion_time: float = 0.0


class IterationVisualizer:
    """
    迭代过程可视化
    
    提供：
    - 实时进度追踪
    - 指标统计
    - 可视化报告
    - 性能分析
    """
    
    def __init__(self):
        self._iterations: List[IterationMetrics] = []
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._current_iteration: Optional[IterationMetrics] = None
        self._start_time: Optional[int] = None
        self._end_time: Optional[int] = None
    
    def start_iteration(self, agents: List[Any]) -> IterationMetrics:
        """开始一次迭代"""
        import time
        
        self._current_iteration = IterationMetrics(
            iteration_number=len(self._iterations) + 1,
            start_time=int(time.time()),
            agents_active=len(agents),
        )
        
        # 初始化 Agent 指标
        for agent in agents:
            role = agent.role if hasattr(agent, 'role') else str(agent)
            if role not in self._agent_metrics:
                self._agent_metrics[role] = AgentMetrics(role=role)
        
        return self._current_iteration
    
    def update_iteration(self, **kwargs):
        """更新当前迭代指标"""
        if not self._current_iteration:
            return
        
        for key, value in kwargs.items():
            if hasattr(self._current_iteration, key):
                setattr(self._current_iteration, key, value)
    
    def end_iteration(self, completion_score: float = 0.0):
        """结束当前迭代"""
        if not self._current_iteration:
            return
        
        import time
        
        self._current_iteration.end_time = int(time.time())
        self._current_iteration.duration_seconds = (
            self._current_iteration.end_time - self._current_iteration.start_time
        )
        self._current_iteration.completion_score = completion_score
        self._current_iteration.status = "completed"
        
        # 更新 Agent 指标
        self._update_agent_metrics()
        
        # 保存迭代记录
        self._iterations.append(self._current_iteration)
        self._current_iteration = None
    
    def _update_agent_metrics(self):
        """更新 Agent 指标"""
        # 简化实现，实际应该从迭代结果中提取
        pass
    
    def record_setback(self, agent_role: str):
        """记录挫折"""
        if self._current_iteration:
            self._current_iteration.setbacks_count += 1
        
        if agent_role in self._agent_metrics:
            self._agent_metrics[agent_role].setbacks_encountered += 1
    
    def get_current_iteration(self) -> Optional[IterationMetrics]:
        """获取当前迭代"""
        return self._current_iteration
    
    def get_iterations(self) -> List[IterationMetrics]:
        """获取所有迭代"""
        return self._iterations.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._iterations:
            return {}
        
        total_iterations = len(self._iterations)
        total_duration = sum(i.duration_seconds for i in self._iterations)
        total_documents = sum(i.documents_produced for i in self._iterations)
        total_setbacks = sum(i.setbacks_count for i in self._iterations)
        
        avg_completion = sum(i.completion_score for i in self._iterations) / total_iterations
        
        return {
            "total_iterations": total_iterations,
            "total_duration_seconds": total_duration,
            "avg_duration_seconds": total_duration / total_iterations,
            "total_documents_produced": total_documents,
            "total_setbacks": total_setbacks,
            "avg_completion_score": avg_completion,
            "agents_count": len(self._agent_metrics),
        }
    
    def generate_progress_chart(self) -> str:
        """生成进度图表 (ASCII)"""
        if not self._iterations:
            return "暂无迭代数据"
        
        chart = []
        chart.append("迭代进度图")
        chart.append("=" * 60)
        
        for iteration in self._iterations:
            # 进度条
            progress = int(iteration.completion_score * 50)
            bar = "█" * progress + "░" * (50 - progress)
            
            # 状态
            status = "✓" if iteration.status == "completed" else "⏳"
            
            chart.append(
                f"Iter {iteration.iteration_number:2d} |{bar}| "
                f"{iteration.completion_score:.1%} {status}"
            )
        
        chart.append("=" * 60)
        return "\n".join(chart)
    
    def generate_metrics_report(self) -> str:
        """生成指标报告"""
        stats = self.get_statistics()
        
        if not stats:
            return "暂无数据"
        
        report = []
        report.append("# 迭代指标报告")
        report.append("")
        report.append("## 总体统计")
        report.append(f"- 总迭代次数：{stats['total_iterations']}")
        report.append(f"- 总耗时：{stats['total_duration_seconds']:.1f} 秒")
        report.append(f"- 平均迭代时间：{stats['avg_duration_seconds']:.1f} 秒")
        report.append(f"- 产出文档数：{stats['total_documents_produced']}")
        report.append(f"- 挫折次数：{stats['total_setbacks']}")
        report.append(f"- 平均完成度：{stats['avg_completion_score']:.1%}")
        report.append(f"- 参与 Agent 数：{stats['agents_count']}")
        report.append("")
        
        # Agent 指标
        report.append("## Agent 表现")
        for role, metrics in self._agent_metrics.items():
            report.append(f"### {role}")
            report.append(f"- 参与迭代：{metrics.iterations_participated}")
            report.append(f"- 产出文档：{metrics.documents_produced}")
            report.append(f"- 处理诉求：{metrics.requests_processed}")
            report.append(f"- 遇到挫折：{metrics.setbacks_encountered}")
            report.append("")
        
        return "\n".join(report)
    
    def generate_json_export(self) -> str:
        """生成 JSON 导出"""
        data = {
            "iterations": [asdict(i) for i in self._iterations],
            "agent_metrics": {k: asdict(v) for k, v in self._agent_metrics.items()},
            "statistics": self.get_statistics(),
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def save_report(self, filepath: str):
        """保存报告到文件"""
        report = self.generate_metrics_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def save_json(self, filepath: str):
        """保存 JSON 数据"""
        json_data = self.generate_json_export()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_data)


class RealTimeMonitor:
    """
    实时监控器
    
    提供实时进度显示
    """
    
    def __init__(self, visualizer: IterationVisualizer):
        self.visualizer = visualizer
        self._enabled = True
    
    def display_status(self):
        """显示当前状态"""
        if not self._enabled:
            return
        
        iteration = self.visualizer.get_current_iteration()
        if not iteration:
            print("当前无活跃迭代")
            return
        
        print(f"\r迭代 {iteration.iteration_number}: "
              f"完成度 {iteration.completion_score:.1%} | "
              f"文档 {iteration.documents_produced} | "
              f"挫折 {iteration.setbacks_count}",
              end="", flush=True)
    
    def enable(self):
        """启用监控"""
        self._enabled = True
    
    def disable(self):
        """禁用监控"""
        self._enabled = False

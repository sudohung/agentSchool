"""Agent 调试器模块."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class DebugStatus(str, Enum):
    """调试状态"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class BreakpointType(str, Enum):
    """断点类型"""
    METHOD_ENTRY = "method_entry"
    METHOD_EXIT = "method_exit"
    CONDITION = "condition"
    EXCEPTION = "exception"


@dataclass
class Breakpoint:
    """断点"""
    
    id: str
    breakpoint_type: BreakpointType
    agent_id: Optional[str] = None
    method_name: Optional[str] = None
    condition: Optional[str] = None
    enabled: bool = True
    hit_count: int = 0
    max_hits: int = 0
    created_at: float = field(default_factory=time.time)
    
    def should_trigger(self, agent_id: str, method_name: str, context: Dict[str, Any]) -> bool:
        """检查是否应该触发断点"""
        if not self.enabled:
            return False
        
        if self.agent_id and self.agent_id != agent_id:
            return False
        
        if self.method_name and self.method_name != method_name:
            return False
        
        if self.max_hits > 0 and self.hit_count >= self.max_hits:
            return False
        
        if self.condition:
            try:
                result = eval(self.condition, {}, context)
                if not result:
                    return False
            except Exception:
                return False
        
        return True
    
    def hit(self):
        """触发断点"""
        self.hit_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.breakpoint_type.value,
            "agent_id": self.agent_id,
            "method_name": self.method_name,
            "condition": self.condition,
            "enabled": self.enabled,
            "hit_count": self.hit_count,
            "max_hits": self.max_hits,
        }


@dataclass
class DebugSession:
    """调试会话"""
    
    session_id: str
    agent_id: str
    status: DebugStatus = DebugStatus.RUNNING
    current_step: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    call_stack: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    paused_at: Optional[float] = None
    
    def add_log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
    
    def push_stack(self, method_name: str):
        """压入调用栈"""
        self.call_stack.append(method_name)
        self.current_step = method_name
    
    def pop_stack(self):
        """弹出调用栈"""
        if self.call_stack:
            self.call_stack.pop()
            self.current_step = self.call_stack[-1] if self.call_stack else None
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "variables": self.variables,
            "call_stack": self.call_stack,
            "log_count": len(self.logs),
            "created_at": self.created_at,
        }


@dataclass
class WatchExpression:
    """监视表达式"""
    
    id: str
    expression: str
    value: Optional[Any] = None
    error: Optional[str] = None
    
    def evaluate(self, context: Dict[str, Any]):
        """计算表达式"""
        try:
            self.value = eval(self.expression, {}, context)
            self.error = None
        except Exception as e:
            self.error = str(e)
            self.value = None


class AgentDebugger:
    """
    Agent 调试器
    
    功能：
    1. 附加到 Agent 进行调试
    2. 设置断点
    3. 单步执行
    4. 查看变量和调用栈
    5. 日志记录
    """
    
    def __init__(self):
        self._sessions: Dict[str, DebugSession] = {}
        self._breakpoints: Dict[str, Breakpoint] = {}
        self._watch_expressions: Dict[str, WatchExpression] = {}
        self._step_mode: Dict[str, bool] = {}
        self._step_over: Dict[str, bool] = {}
        self._pause_events: Dict[str, asyncio.Event] = {}
        self._debug_hooks: List[Callable[[str, str, Dict[str, Any]], None]] = []
    
    def attach(self, agent_id: str) -> DebugSession:
        """附加到 Agent"""
        session_id = f"debug_{agent_id}_{uuid.uuid4().hex[:8]}"
        
        session = DebugSession(
            session_id=session_id,
            agent_id=agent_id,
            status=DebugStatus.RUNNING,
        )
        
        self._sessions[session_id] = session
        self._step_mode[session_id] = False
        self._step_over[session_id] = False
        self._pause_events[session_id] = asyncio.Event()
        self._pause_events[session_id].set()
        
        logger.info(f"Debug session created: {session_id} for agent {agent_id}")
        return session
    
    def detach(self, session_id: str):
        """分离调试"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.status = DebugStatus.STOPPED
            self._resume_session(session_id)
            del self._sessions[session_id]
            logger.info(f"Debug session detached: {session_id}")
    
    def add_breakpoint(
        self,
        agent_id: Optional[str] = None,
        method_name: Optional[str] = None,
        condition: Optional[str] = None,
        breakpoint_type: BreakpointType = BreakpointType.METHOD_ENTRY,
        max_hits: int = 0,
    ) -> Breakpoint:
        """添加断点"""
        breakpoint_id = f"bp_{uuid.uuid4().hex[:8]}"
        
        breakpoint = Breakpoint(
            id=breakpoint_id,
            breakpoint_type=breakpoint_type,
            agent_id=agent_id,
            method_name=method_name,
            condition=condition,
            max_hits=max_hits,
        )
        
        self._breakpoints[breakpoint_id] = breakpoint
        logger.info(f"Breakpoint added: {breakpoint_id}")
        return breakpoint
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点"""
        if breakpoint_id in self._breakpoints:
            del self._breakpoints[breakpoint_id]
            logger.info(f"Breakpoint removed: {breakpoint_id}")
            return True
        return False
    
    def enable_breakpoint(self, breakpoint_id: str, enabled: bool = True):
        """启用/禁用断点"""
        if breakpoint_id in self._breakpoints:
            self._breakpoints[breakpoint_id].enabled = enabled
    
    def list_breakpoints(self) -> List[Breakpoint]:
        """列出所有断点"""
        return list(self._breakpoints.values())
    
    def step_over(self, session_id: str):
        """单步跳过"""
        if session_id in self._sessions:
            self._step_mode[session_id] = True
            self._step_over[session_id] = True
            self._resume_session(session_id)
    
    def step_into(self, session_id: str):
        """单步进入"""
        if session_id in self._sessions:
            self._step_mode[session_id] = True
            self._step_over[session_id] = False
            self._resume_session(session_id)
    
    def continue_execution(self, session_id: str):
        """继续执行"""
        if session_id in self._sessions:
            self._step_mode[session_id] = False
            self._resume_session(session_id)
    
    def pause(self, session_id: str):
        """暂停执行"""
        if session_id in self._sessions:
            self._sessions[session_id].status = DebugStatus.PAUSED
            self._sessions[session_id].paused_at = time.time()
            self._pause_events[session_id].clear()
            logger.info(f"Session paused: {session_id}")
    
    def get_variables(self, session_id: str) -> Dict[str, Any]:
        """获取变量"""
        if session_id in self._sessions:
            return self._sessions[session_id].variables.copy()
        return {}
    
    def set_variable(self, session_id: str, name: str, value: Any):
        """设置变量"""
        if session_id in self._sessions:
            self._sessions[session_id].set_variable(name, value)
    
    def get_call_stack(self, session_id: str) -> List[str]:
        """获取调用栈"""
        if session_id in self._sessions:
            return self._sessions[session_id].call_stack.copy()
        return []
    
    def get_logs(self, session_id: str, limit: int = 100) -> List[str]:
        """获取日志"""
        if session_id in self._sessions:
            return self._sessions[session_id].logs[-limit:]
        return []
    
    def add_watch(self, expression: str) -> WatchExpression:
        """添加监视表达式"""
        watch_id = f"watch_{uuid.uuid4().hex[:8]}"
        watch = WatchExpression(id=watch_id, expression=expression)
        self._watch_expressions[watch_id] = watch
        return watch
    
    def remove_watch(self, watch_id: str) -> bool:
        """移除监视表达式"""
        if watch_id in self._watch_expressions:
            del self._watch_expressions[watch_id]
            return True
        return False
    
    def evaluate_watches(self, session_id: str) -> Dict[str, Any]:
        """计算所有监视表达式"""
        if session_id not in self._sessions:
            return {}
        
        context = self._sessions[session_id].variables
        results = {}
        
        for watch_id, watch in self._watch_expressions.items():
            watch.evaluate(context)
            results[watch_id] = {
                "expression": watch.expression,
                "value": str(watch.value) if watch.value is not None else None,
                "error": watch.error,
            }
        
        return results
    
    async def on_method_entry(
        self,
        session_id: str,
        method_name: str,
        context: Dict[str, Any],
    ):
        """方法入口钩子"""
        if session_id not in self._sessions:
            return
        
        session = self._sessions[session_id]
        session.push_stack(method_name)
        session.add_log(f"→ {method_name}")
        
        for var_name, var_value in context.items():
            session.set_variable(var_name, var_value)
        
        triggered_breakpoints = []
        for bp in self._breakpoints.values():
            if bp.should_trigger(session.agent_id, method_name, context):
                bp.hit()
                triggered_breakpoints.append(bp)
        
        if triggered_breakpoints:
            session.status = DebugStatus.PAUSED
            session.paused_at = time.time()
            self._pause_events[session_id].clear()
            session.add_log(f"⏸ Breakpoint hit: {[bp.id for bp in triggered_breakpoints]}")
        
        elif self._step_mode.get(session_id, False):
            session.status = DebugStatus.PAUSED
            session.paused_at = time.time()
            self._pause_events[session_id].clear()
            session.add_log(f"⏸ Step pause at: {method_name}")
        
        await self._pause_events[session_id].wait()
        
        if session.status == DebugStatus.PAUSED:
            session.status = DebugStatus.RUNNING
    
    async def on_method_exit(
        self,
        session_id: str,
        method_name: str,
        result: Any = None,
        error: Optional[str] = None,
    ):
        """方法出口钩子"""
        if session_id not in self._sessions:
            return
        
        session = self._sessions[session_id]
        
        if error:
            session.add_log(f"← {method_name} (error: {error})")
            
            for bp in self._breakpoints.values():
                if bp.breakpoint_type == BreakpointType.EXCEPTION:
                    if bp.should_trigger(session.agent_id, method_name, {}):
                        bp.hit()
                        session.status = DebugStatus.PAUSED
                        self._pause_events[session_id].clear()
        else:
            session.add_log(f"← {method_name}")
        
        session.pop_stack()
    
    def add_debug_hook(self, hook: Callable[[str, str, Dict[str, Any]], None]):
        """添加调试钩子"""
        self._debug_hooks.append(hook)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        if session_id in self._sessions:
            return self._sessions[session_id].to_dict()
        return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        return [s.to_dict() for s in self._sessions.values()]
    
    def _resume_session(self, session_id: str):
        """恢复会话执行"""
        if session_id in self._pause_events:
            self._pause_events[session_id].set()
    
    @property
    def active_sessions(self) -> int:
        return len(self._sessions)
    
    @property
    def active_breakpoints(self) -> int:
        return sum(1 for bp in self._breakpoints.values() if bp.enabled)


def create_debugger() -> AgentDebugger:
    """创建调试器实例"""
    return AgentDebugger()
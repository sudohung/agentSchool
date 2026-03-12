"""Agent 状态机."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel


class AgentState(Enum):
    """Agent 状态"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    BLOCKED = "blocked"
    DONE = "done"


class StateTransition(BaseModel):
    """状态转换"""
    from_state: AgentState
    to_state: AgentState
    condition: str
    action: Optional[str] = None


class AgentStateMachine:
    """
    Agent 状态机
    
    管理 Agent 的生命周期状态转换
    """
    
    # 定义允许的状态转换
    transitions: List[StateTransition] = [
        StateTransition(
            from_state=AgentState.IDLE,
            to_state=AgentState.WORKING,
            condition="有新文档或诉求",
            action="开始处理",
        ),
        StateTransition(
            from_state=AgentState.WORKING,
            to_state=AgentState.WAITING,
            condition="需要其他 Agent 协作",
            action="发布诉求并等待",
        ),
        StateTransition(
            from_state=AgentState.WAITING,
            to_state=AgentState.WORKING,
            condition="诉求已响应",
            action="继续工作",
        ),
        StateTransition(
            from_state=AgentState.WORKING,
            to_state=AgentState.BLOCKED,
            condition="遇到无法解决的问题",
            action="标记为阻塞",
        ),
        StateTransition(
            from_state=AgentState.BLOCKED,
            to_state=AgentState.WORKING,
            condition="问题已解决",
            action="解除阻塞",
        ),
        StateTransition(
            from_state=AgentState.WORKING,
            to_state=AgentState.DONE,
            condition="任务完成",
            action="标记为完成",
        ),
    ]
    
    def __init__(self, initial_state: AgentState = AgentState.IDLE):
        self.current_state = initial_state
        self.history: List[StateTransition] = []
    
    def can_transition_to(self, target_state: AgentState) -> bool:
        """检查是否可以转换到目标状态"""
        for transition in self.transitions:
            if (
                transition.from_state == self.current_state
                and transition.to_state == target_state
            ):
                return True
        return False
    
    def transition_to(
        self,
        target_state: AgentState,
        reason: str,
    ) -> bool:
        """执行状态转换"""
        if not self.can_transition_to(target_state):
            return False
        
        # 找到对应的转换
        for transition in self.transitions:
            if (
                transition.from_state == self.current_state
                and transition.to_state == target_state
            ):
                # 执行转换
                self.current_state = target_state
                self.history.append(transition)
                return True
        
        return False
    
    def get_current_state(self) -> AgentState:
        """获取当前状态"""
        return self.current_state
    
    def get_history(self) -> List[StateTransition]:
        """获取状态历史"""
        return self.history

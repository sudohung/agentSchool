"""挫折处理 (简化版)."""

from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, List


class SetbackType(Enum):
    """挫折类型"""
    TECHNICAL_ERROR = "technical_error"
    TIMEOUT = "timeout"
    NO_RESPONSE = "no_response"
    OTHER = "other"


class Setback:
    """挫折记录"""
    
    def __init__(
        self,
        id: str,
        type: SetbackType,
        agent: str,
        description: str,
    ):
        self.id = id
        self.type = type
        self.agent = agent
        self.description = description


class SetbackHandler:
    """挫折处理器"""
    
    def __init__(self):
        self._setbacks: List[Setback] = []
    
    async def record_setback(self, agent, iteration: int, error: Exception) -> Setback:
        """记录挫折"""
        import hashlib
        import time
        
        setback = Setback(
            id="setback_" + hashlib.md5(str(time.time()).encode()).hexdigest()[:12],
            type=SetbackType.TECHNICAL_ERROR,
            agent=agent.role,
            description=str(error),
        )
        
        self._setbacks.append(setback)
        return setback
    
    def get_setbacks(self) -> List[Setback]:
        """获取挫折记录"""
        return self._setbacks

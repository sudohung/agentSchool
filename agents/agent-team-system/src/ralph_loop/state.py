"""Ralph Loop 状态."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class LoopStatus(Enum):
    """Loop 状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class IterationState(BaseModel):
    """迭代状态"""
    iteration_number: int
    start_time: int
    end_time: Optional[int] = None
    status: LoopStatus
    agents_participating: List[str]
    documents_read: int = 0
    requests_processed: int = 0
    documents_produced: int = 0
    requests_posted: int = 0
    setbacks_encountered: int = 0
    completion_score: float = 0.0

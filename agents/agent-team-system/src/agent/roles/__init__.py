"""Agent 角色模块."""

from .pm import ProductManagerAgent
from .architect import SystemArchitectAgent
from .tech_lead import TechLeadAgent
from .others import (
    FrontendDeveloperAgent,
    BackendDeveloperAgent,
    FullStackDeveloperAgent,
    QAAgent,
    CodeReviewerAgent,
    DocWriterAgent,
    DevOpsAgent,
    SecurityAgent,
    CoordinatorAgent,
)

__all__ = [
    "ProductManagerAgent",
    "SystemArchitectAgent",
    "TechLeadAgent",
    "FrontendDeveloperAgent",
    "BackendDeveloperAgent",
    "FullStackDeveloperAgent",
    "QAAgent",
    "CodeReviewerAgent",
    "DocWriterAgent",
    "DevOpsAgent",
    "SecurityAgent",
    "CoordinatorAgent",
]

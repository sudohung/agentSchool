"""Agent 角色模块."""

from .pm import ProductManagerAgent
from .architect import SystemArchitectAgent
from .tech_lead import TechLeadAgent
from .frontend import FrontendDeveloperAgent
from .backend import BackendDeveloperAgent
from .fullstack import FullStackDeveloperAgent
from .qa import QAAgent
from .reviewer import CodeReviewerAgent
from .doc import DocWriterAgent
from .devops import DevOpsAgent
from .security import SecurityAgent
from .coordinator import CoordinatorAgent

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

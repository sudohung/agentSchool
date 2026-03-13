"""Agent 角色模块."""

from .pm import ProductManagerAgent
from .architect import SystemArchitectAgent
from .tech_lead import TechLeadAgent
from .coordinator import CoordinatorAgent
from .frontend_developer import FrontendDeveloperAgent
from .backend_developer import BackendDeveloperAgent
from .fullstack_developer import FullStackDeveloperAgent
from .qa_engineer import QAAgent
from .code_reviewer import CodeReviewerAgent
from .doc_writer import DocWriterAgent
from .devops import DevOpsAgent
from .security import SecurityAgent
from .loader import (
    get_agent_definition,
    list_all_agent_roles,
    AgentDefinitionLoader,
    initialize_agents,
)

__all__ = [
    "ProductManagerAgent",
    "SystemArchitectAgent",
    "TechLeadAgent",
    "CoordinatorAgent",
    "FrontendDeveloperAgent",
    "BackendDeveloperAgent",
    "FullStackDeveloperAgent",
    "QAAgent",
    "CodeReviewerAgent",
    "DocWriterAgent",
    "DevOpsAgent",
    "SecurityAgent",
    "get_agent_definition",
    "list_all_agent_roles",
    "AgentDefinitionLoader",
    "initialize_agents",
]
"""Agent 角色模块."""

from .pm import ProductManagerAgent
from .architect import SystemArchitectAgent
from .tech_lead import TechLeadAgent
from .coordinator import CoordinatorAgent
from .others import (
    FrontendDeveloperAgent,
    BackendDeveloperAgent,
    FullStackDeveloperAgent,
    QAAgent,
    CodeReviewerAgent,
    DocWriterAgent,
    DevOpsAgent,
    SecurityAgent,
)
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

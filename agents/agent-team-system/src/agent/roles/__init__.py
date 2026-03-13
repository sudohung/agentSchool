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
from agent.registry import AgentRegistry

# 注册所有 Agent 角色到注册表
def _register_all_roles():
    """注册所有角色"""
    # 核心角色
    AgentRegistry.register("Product Manager", ProductManagerAgent, "core")
    AgentRegistry.register("System Architect", SystemArchitectAgent, "core")
    AgentRegistry.register("Tech Lead", TechLeadAgent, "core")
    AgentRegistry.register("Coordinator", CoordinatorAgent, "core")
    
    # 开发角色
    AgentRegistry.register("Frontend Developer", FrontendDeveloperAgent, "development")
    AgentRegistry.register("Backend Developer", BackendDeveloperAgent, "development")
    AgentRegistry.register("Full Stack Developer", FullStackDeveloperAgent, "development")
    
    # 质量角色
    AgentRegistry.register("QA Engineer", QAAgent, "quality")
    AgentRegistry.register("Code Reviewer", CodeReviewerAgent, "quality")
    
    # 支持角色
    AgentRegistry.register("Doc Writer", DocWriterAgent, "support")
    AgentRegistry.register("DevOps Engineer", DevOpsAgent, "support")
    AgentRegistry.register("Security Engineer", SecurityAgent, "support")

# 自动注册
_register_all_roles()

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
    "AgentRegistry",
]
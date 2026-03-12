"""Agent 定义加载器 - 从 MD 文件动态加载 Agent 配置."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


AGENT_DEFINITIONS_DIR = Path(__file__).parent / "agent"


@dataclass
class RalphLoopConfig:
    """Ralph Loop 配置"""
    read: str = ""
    act: str = ""
    leverage_prompt: str = ""
    produce_path: str = ""
    produce_doc_type: str = ""
    produce_tags: List[str] = field(default_factory=list)
    produce_template: str = ""
    help_requests: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class AgentDefinition:
    """Agent 定义"""
    role: str = ""
    category: str = ""
    description: str = ""
    responsibilities: List[str] = field(default_factory=list)
    expertise: List[str] = field(default_factory=list)
    collaborations: Dict[str, str] = field(default_factory=dict)
    ralph_loop: RalphLoopConfig = field(default_factory=RalphLoopConfig)


class AgentDefinitionLoader:
    """Agent 定义加载器 (带缓存)"""
    
    _cache: Dict[str, AgentDefinition] = {}
    _initialized: bool = False
    
    @classmethod
    def initialize(cls) -> None:
        """预加载所有 Agent 定义 (项目启动时调用)"""
        if cls._initialized:
            return
        
        cls._cache.clear()
        for md_file in AGENT_DEFINITIONS_DIR.glob("*.md"):
            role = md_file.stem.replace("_", " ")
            try:
                definition = cls._load_from_file(role)
                cls._cache[role] = definition
            except Exception as e:
                print(f"Warning: Failed to load agent {role}: {e}")
        
        cls._initialized = True
    
    @classmethod
    def load(cls, role: str) -> AgentDefinition:
        """
        加载 Agent 定义
        
        Args:
            role: 角色名称
            
        Returns:
            AgentDefinition: Agent 定义
        """
        if role in cls._cache:
            return cls._cache[role]
        
        definition = cls._load_from_file(role)
        cls._cache[role] = definition
        return definition
    
    @classmethod
    def _load_from_file(cls, role: str) -> AgentDefinition:
        """从 MD 文件加载"""
        file_path = AGENT_DEFINITIONS_DIR / f"{cls._to_filename(role)}.md"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Agent definition not found: {role}")
        
        content = file_path.read_text(encoding="utf-8")
        return cls._parse_md(content)
    
    @classmethod
    def _to_filename(cls, role: str) -> str:
        """将角色名转换为文件名"""
        return role.lower().replace(" ", "_").replace("/", "_")
    
    @classmethod
    def _parse_md(cls, content: str) -> AgentDefinition:
        """解析 MD 内容"""
        lines = content.strip().split("\n")
        
        definition = AgentDefinition()
        current_section = ""
        section_content = []
        in_leverage = False
        in_template = False
        template_lines = []
        
        # Track which main section we're in
        section_map = {
            "## 角色定义": "meta",
            "## 职责": "responsibilities",
            "## 专业技能": "expertise",
            "## 协作关系": "collaborations",
            "## Ralph Loop": "ralph_loop",
        }
        
        sub_section_map = {
            "### Read": "read",
            "### Act": "act",
            "### Leverage": "leverage",
            "### Produce": "produce",
            "### Help": "help",
        }
        
        for i, line in enumerate(lines):
            line = line.rstrip()
            
            # Check for main sections
            if line in section_map:
                current_section = section_map[line]
                section_content = []
                continue
            elif line in sub_section_map:
                # Save previous section content
                cls._save_section(definition, current_section, section_content, in_leverage, template_lines)
                current_section = sub_section_map[line]
                section_content = []
                in_leverage = False
                in_template = False
                template_lines = []
                continue
            
            # Parse based on current section
            if current_section == "meta":
                if line.startswith("role:"):
                    definition.role = line.split(":", 1)[1].strip()
                elif line.startswith("category:"):
                    definition.category = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    definition.description = line.split(":", 1)[1].strip()
            
            elif current_section == "responsibilities":
                if line.startswith("- "):
                    definition.responsibilities.append(line[2:])
            
            elif current_section == "expertise":
                if line.startswith("- "):
                    definition.expertise.append(line[2:])
            
            elif current_section == "collaborations":
                if ":" in line and not line.startswith("#"):
                    parts = line.split(":", 1)
                    if parts[0].strip():
                        definition.collaborations[parts[0].strip()] = parts[1].strip()
            
            elif current_section == "read":
                section_content.append(line)
            
            elif current_section == "act":
                section_content.append(line)
            
            elif current_section == "leverage":
                if line == "```prompt":
                    in_leverage = True
                elif line == "```":
                    in_leverage = False
                elif in_leverage:
                    definition.ralph_loop.leverage_prompt += line + "\n"
            
            elif current_section == "produce":
                if line.startswith("- path:"):
                    definition.ralph_loop.produce_path = line.split(":", 1)[1].strip()
                elif line.startswith("- doc_type:"):
                    definition.ralph_loop.produce_doc_type = line.split(":", 1)[1].strip()
                elif line.startswith("- tags:"):
                    tags_str = line.split(":", 1)[1].strip()
                    definition.ralph_loop.produce_tags = [t.strip() for t in tags_str.strip("[]").split(",")]
                elif line.startswith("- template:"):
                    in_template = True
                elif in_template:
                    if line and not line.startswith(" "):
                        in_template = False
                    elif line:
                        template_lines.append(line.lstrip())
            
            elif current_section == "help":
                if line.startswith("- to:"):
                    help_req = {"to": line.split(":", 1)[1].strip()}
                    definition.ralph_loop.help_requests.append(help_req)
                elif line.startswith("  subject:") and definition.ralph_loop.help_requests:
                    definition.ralph_loop.help_requests[-1]["subject"] = line.split(":", 1)[1].strip()
                elif line.startswith("  content:") and definition.ralph_loop.help_requests:
                    definition.ralph_loop.help_requests[-1]["content"] = line.split(":", 1)[1].strip()
                elif line.startswith("  priority:") and definition.ralph_loop.help_requests:
                    definition.ralph_loop.help_requests[-1]["priority"] = line.split(":", 1)[1].strip()
        
        # Save last section
        cls._save_section(definition, current_section, section_content, in_leverage, template_lines)
        
        return definition
    
    @classmethod
    def _save_section(cls, definition: AgentDefinition, section: str, content: List[str], in_leverage: bool, template: List[str]):
        """保存解析的section内容"""
        text = "\n".join(content).strip()
        
        if section == "read":
            definition.ralph_loop.read = text
        elif section == "act":
            definition.ralph_loop.act = text
        
        if template:
            definition.ralph_loop.produce_template = "\n".join(template).strip()
    
    @classmethod
    def list_roles(cls) -> List[str]:
        """列出所有可用角色"""
        roles = []
        for f in AGENT_DEFINITIONS_DIR.glob("*.md"):
            name = f.stem.replace("_", " ")
            roles.append(name)
        return roles
    
    @classmethod
    def get_categories(cls) -> Dict[str, List[str]]:
        """获取角色分类"""
        categories: Dict[str, List[str]] = {}
        for role in cls.list_roles():
            definition = cls.load(role)
            if definition.category not in categories:
                categories[definition.category] = []
            categories[definition.category].append(role)
        return categories


def get_agent_definition(role: str) -> AgentDefinition:
    """获取 Agent 定义"""
    return AgentDefinitionLoader.load(role)


def list_all_agent_roles() -> List[str]:
    """列出所有 Agent 角色"""
    return AgentDefinitionLoader.list_roles()


def initialize_agents() -> None:
    """初始化所有 Agent 定义 (项目启动时调用)"""
    AgentDefinitionLoader.initialize()
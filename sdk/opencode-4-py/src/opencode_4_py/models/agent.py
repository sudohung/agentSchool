"""Agent models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any, Union


class AgentPermission(BaseModel):
    """Agent permission rule."""
    permission: str
    action: Literal["allow", "deny", "ask"]
    pattern: str


PermissionRuleset = List[AgentPermission]


class AgentModel(BaseModel):
    """Agent model reference."""
    provider_id: str = Field(..., alias="providerID")
    model_id: str = Field(..., alias="modelID")
    
    class Config:
        populate_by_name = True


class Agent(BaseModel):
    """AI Agent information."""
    name: str
    description: Optional[str] = None
    mode: Literal["subagent", "primary", "all"]
    native: Optional[bool] = None
    hidden: Optional[bool] = None
    model: Optional[AgentModel] = None
    variant: Optional[str] = None
    prompt: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    permission: Optional[PermissionRuleset] = None
    temperature: Optional[float] = Field(None, alias="temperature")
    top_p: Optional[float] = Field(None, alias="topP")
    color: Optional[str] = None
    steps: Optional[int] = None
    
    class Config:
        populate_by_name = True

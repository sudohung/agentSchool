"""Provider models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any, Union


class ModelCost(BaseModel):
    """Model cost information."""
    input: float
    output: float
    cache_read: Optional[float] = None
    cache_write: Optional[float] = None


class ModelLimit(BaseModel):
    """Model limit information."""
    context: int
    output: int
    input: Optional[int] = None


class ModelModalities(BaseModel):
    """Model modalities."""
    input: List[str]
    output: List[str]


class Model(BaseModel):
    """AI Model information."""
    id: str
    name: str
    family: Optional[str] = None
    release_date: Optional[str] = Field(None, alias="release_date")
    attachment: Optional[bool] = None
    reasoning: Optional[bool] = None
    temperature: Optional[bool] = None
    tool_call: Optional[bool] = Field(None, alias="tool_call")
    limit: Optional[ModelLimit] = None
    cost: Optional[ModelCost] = None
    modalities: Optional[ModelModalities] = None
    experimental: Optional[bool] = None
    status: Optional[Literal["alpha", "beta", "deprecated", "active"]] = None
    options: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    variants: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class Provider(BaseModel):
    """AI Provider information."""
    id: str
    name: str
    source: Literal["env", "config", "custom", "api"]
    env: List[str]
    key: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    models: Dict[str, Model] = Field(default_factory=dict)
    api: Optional[str] = None
    npm: Optional[str] = None


class ProviderAuthMethod(BaseModel):
    """Provider authentication method."""
    type: Literal["oauth", "api"]
    label: str


class ProviderAuthAuthorization(BaseModel):
    """Provider OAuth authorization result."""
    url: str
    method: Literal["auto", "code"]
    instructions: str


class ProviderListResponse(BaseModel):
    """Provider list response."""
    all: List[Dict[str, Any]] = Field(default_factory=list, alias="all")
    default: Dict[str, str] = Field(default_factory=dict)
    connected: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True


class ConfigProvidersResponse(BaseModel):
    """Config providers response."""
    providers: List[Provider]
    default: Dict[str, str]


class OAuthAuthorizeRequest(BaseModel):
    """OAuth authorize request."""
    method: int


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""
    method: int
    code: Optional[str] = None
"""Config models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any, Union


class ServerConfig(BaseModel):
    """Server configuration."""
    hostname: Optional[str] = None
    port: Optional[int] = None
    password: Optional[str] = None


class CommandConfig(BaseModel):
    """Command configuration."""
    template: str
    description: Optional[str] = None
    agent: Optional[str] = None
    model: Optional[str] = None
    subtask: Optional[bool] = None


class SkillsConfig(BaseModel):
    """Skills configuration."""
    paths: Optional[List[str]] = None
    urls: Optional[List[str]] = None


class WatcherConfig(BaseModel):
    """Watcher configuration."""
    ignore: Optional[List[str]] = None


class Config(BaseModel):
    """OpenCode configuration."""
    schema: Optional[str] = Field(None, alias="$schema")
    log_level: Optional[Literal["DEBUG", "INFO", "WARN", "ERROR"]] = Field(None, alias="logLevel")
    server: Optional[ServerConfig] = None
    command: Optional[Dict[str, CommandConfig]] = None
    skills: Optional[SkillsConfig] = None
    watcher: Optional[WatcherConfig] = None
    plugin: Optional[List[str]] = None
    snapshot: Optional[bool] = None
    share: Optional[Literal["manual", "auto", "disabled"]] = None
    autoshare: Optional[bool] = None
    autoupdate: Optional[Union[bool, Literal["notify"]]] = None
    disabled_providers: Optional[List[str]] = None
    enabled_providers: Optional[List[str]] = None
    
    class Config:
        populate_by_name = True


class ConfigUpdateRequest(BaseModel):
    """Request to update configuration."""
    schema: Optional[str] = Field(None, alias="$schema")
    log_level: Optional[Literal["DEBUG", "INFO", "WARN", "ERROR"]] = Field(None, alias="logLevel")
    server: Optional[ServerConfig] = None
    command: Optional[Dict[str, CommandConfig]] = None
    skills: Optional[SkillsConfig] = None
    watcher: Optional[WatcherConfig] = None
    plugin: Optional[List[str]] = None
    snapshot: Optional[bool] = None
    share: Optional[Literal["manual", "auto", "disabled"]] = None
    autoupdate: Optional[Union[bool, Literal["notify"]]] = None
    disabled_providers: Optional[List[str]] = None
    enabled_providers: Optional[List[str]] = None
    
    class Config:
        populate_by_name = True
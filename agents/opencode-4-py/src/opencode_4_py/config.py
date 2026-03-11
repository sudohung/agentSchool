"""Client configuration."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClientConfig:
    """Configuration for OpenCode client."""
    
    base_url: str = "http://127.0.0.1:4096"
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: float = 30.0
    directory: Optional[str] = None
    workspace: Optional[str] = None
    
    def __post_init__(self) -> None:
        if self.password and not self.username:
            self.username = "opencode"

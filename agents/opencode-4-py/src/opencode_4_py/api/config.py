"""Config API implementation."""

from __future__ import annotations

from typing import Optional, Dict, Any

from ..utils.http import HTTPClient
from ..models.config import Config, ConfigUpdateRequest
from ..models.provider import Provider, ConfigProvidersResponse


class ConfigAPI:
    """Config API client."""
    
    def __init__(
        self,
        http_client: HTTPClient,
        directory: Optional[str] = None,
        workspace: Optional[str] = None,
    ):
        self.http = http_client
        self.directory = directory
        self.workspace = workspace
    
    def _get_params(self) -> Dict[str, Any]:
        """Get default query parameters."""
        params = {}
        if self.directory:
            params["directory"] = self.directory
        if self.workspace:
            params["workspace"] = self.workspace
        return params
    
    def get(self) -> Config:
        """Get configuration.
        
        Returns:
            Current OpenCode configuration settings.
        """
        response = self.http.get("/config", params=self._get_params())
        data = response.json()
        return Config(**data)
    
    def update(self, config: ConfigUpdateRequest) -> Config:
        """Update configuration.
        
        Args:
            config: Configuration update request.
            
        Returns:
            Updated configuration.
        """
        response = self.http.patch(
            "/config",
            json=config.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        data = response.json()
        return Config(**data)
    
    def providers(self) -> ConfigProvidersResponse:
        """Get configured providers.
        
        Returns:
            List of configured providers and default models.
        """
        response = self.http.get("/config/providers", params=self._get_params())
        data = response.json()
        providers = [Provider(**p) for p in data.get("providers", [])]
        return ConfigProvidersResponse(
            providers=providers,
            default=data.get("default", {}),
        )
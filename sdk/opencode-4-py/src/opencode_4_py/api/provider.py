"""Provider API implementation."""

from __future__ import annotations

from typing import Optional, Dict, Any

from ..utils.http import HTTPClient
from ..models.provider import (
    ProviderListResponse,
    ProviderAuthMethod,
    ProviderAuthAuthorization,
    OAuthAuthorizeRequest,
    OAuthCallbackRequest,
)


class ProviderAPI:
    """Provider API client."""
    
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
    
    def list(self) -> ProviderListResponse:
        """List all providers.
        
        Returns:
            List of all available providers, default models, and connected providers.
        """
        response = self.http.get("/provider", params=self._get_params())
        data = response.json()
        return ProviderListResponse(**data)
    
    def auth(self) -> Dict[str, list]:
        """Get provider authentication methods.
        
        Returns:
            Dictionary mapping provider IDs to their available auth methods.
        """
        response = self.http.get("/provider/auth", params=self._get_params())
        data = response.json()
        result = {}
        for provider_id, methods in data.items():
            result[provider_id] = [ProviderAuthMethod(**m) for m in methods]
        return result
    
    def oauth_authorize(
        self,
        provider_id: str,
        method: int,
    ) -> ProviderAuthAuthorization:
        """Initiate OAuth authorization.
        
        Args:
            provider_id: Provider ID.
            method: Auth method index.
            
        Returns:
            Authorization URL and instructions.
        """
        request = OAuthAuthorizeRequest(method=method)
        response = self.http.post(
            f"/provider/{provider_id}/oauth/authorize",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        data = response.json()
        return ProviderAuthAuthorization(**data)
    
    def oauth_callback(
        self,
        provider_id: str,
        method: int,
        code: Optional[str] = None,
    ) -> bool:
        """Handle OAuth callback.
        
        Args:
            provider_id: Provider ID.
            method: Auth method index.
            code: OAuth authorization code.
            
        Returns:
            True if OAuth callback was processed successfully.
        """
        request = OAuthCallbackRequest(method=method, code=code)
        response = self.http.post(
            f"/provider/{provider_id}/oauth/callback",
            json=request.model_dump(by_alias=True, exclude_none=True),
            params=self._get_params(),
        )
        return response.json()
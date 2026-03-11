"""HTTP client utilities for OpenCode SDK."""

from __future__ import annotations

import httpx
from typing import Optional, Dict, Any, AsyncIterator, Iterator


class HTTPClient:
    """Synchronous HTTP client wrapper."""
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:4096",
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        
        auth = None
        if username and password:
            auth = (username, password)
        
        self.client = httpx.Client(
            base_url=self.base_url,
            auth=auth,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
    
    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make HTTP request."""
        response = self.client.request(method, path, params=params, json=json)
        response.raise_for_status()
        return response
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make GET request."""
        return self.request("GET", path, params=params)
    
    def post(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make POST request."""
        return self.request("POST", path, params=params, json=json)
    
    def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make DELETE request."""
        return self.request("DELETE", path, params=params)
    
    def patch(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make PATCH request."""
        return self.request("PATCH", path, params=params, json=json)
    
    def put(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make PUT request."""
        return self.request("PUT", path, params=params, json=json)
    
    def stream_sse(self, path: str, params: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """Stream Server-Sent Events."""
        with self.client.stream("GET", path, params=params) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        yield json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
    
    def close(self) -> None:
        """Close the client."""
        self.client.close()
    
    def __enter__(self) -> "HTTPClient":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()


class AsyncHTTPClient:
    """Asynchronous HTTP client wrapper."""
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:4096",
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        
        auth = None
        if username and password:
            auth = (username, password)
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=auth,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
    
    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make HTTP request."""
        response = await self.client.request(method, path, params=params, json=json)
        response.raise_for_status()
        return response
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make GET request."""
        return await self.request("GET", path, params=params)
    
    async def post(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make POST request."""
        return await self.request("POST", path, params=params, json=json)
    
    async def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make DELETE request."""
        return await self.request("DELETE", path, params=params)
    
    async def patch(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make PATCH request."""
        return await self.request("PATCH", path, params=params, json=json)
    
    async def put(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make PUT request."""
        return await self.request("PUT", path, params=params, json=json)
    
    async def stream_sse(self, path: str, params: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        """Stream Server-Sent Events."""
        async with self.client.stream("GET", path, params=params) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        yield json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
    
    async def close(self) -> None:
        """Close the client."""
        await self.client.aclose()
    
    async def __aenter__(self) -> "AsyncHTTPClient":
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.close()

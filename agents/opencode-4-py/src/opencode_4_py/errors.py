"""Error types for OpenCode SDK."""

from typing import Optional, Dict, Any


class OpenCodeError(Exception):
    """Base exception for OpenCode SDK."""
    pass


class ConnectionError(OpenCodeError):
    """Connection error."""
    pass


class AuthenticationError(OpenCodeError):
    """Authentication error."""
    pass


class NotFoundError(OpenCodeError):
    """Resource not found."""
    pass


class ValidationError(OpenCodeError):
    """Validation error."""
    pass


class APIError(OpenCodeError):
    """API error with status code."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        is_retryable: bool = False,
        response_headers: Optional[Dict[str, str]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.is_retryable = is_retryable
        self.response_headers = response_headers
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.status_code:
            return f"APIError {self.status_code}: {self.message}"
        return f"APIError: {self.message}"


class ProviderAuthError(OpenCodeError):
    """Provider authentication error."""
    
    def __init__(self, provider_id: str, message: str):
        self.provider_id = provider_id
        self.message = message
        super().__init__(f"Provider {provider_id}: {message}")


class MessageAbortedError(OpenCodeError):
    """Message was aborted."""
    pass


class ContextOverflowError(OpenCodeError):
    """Context window overflow."""
    pass

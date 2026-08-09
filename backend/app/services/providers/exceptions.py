class LLMProviderError(Exception):
    """Base exception for LLM provider gateway errors."""

    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message)
        self.message = message
        self.provider = provider

class ProviderNotConfiguredError(LLMProviderError):
    """Raised when an API key is missing for the requested provider."""

class ProviderTimeoutError(LLMProviderError):
    """Raised when provider API call times out."""

class ProviderRateLimitError(LLMProviderError):
    """Raised when provider returns a rate limit error (429)."""

class ProviderAuthenticationError(LLMProviderError):
    """Raised when provider API key is invalid or unauthorized (401/403)."""

class ProviderRequestError(LLMProviderError):
    """Raised for invalid provider requests or 4xx client errors."""

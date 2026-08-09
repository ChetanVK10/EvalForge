from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field

class LLMResponse(BaseModel):
    text: str = Field(..., description="Generated text completion")
    provider: str = Field(..., description="Provider name: groq or gemini")
    model: str = Field(..., description="Model identifier used")

    latency_ms: int = Field(..., description="Wall-clock latency in milliseconds")

    input_tokens: Optional[int] = Field(None, description="Input/prompt token count")
    output_tokens: Optional[int] = Field(None, description="Output/completion token count")
    total_tokens: Optional[int] = Field(None, description="Total token count")

    estimated_cost: Optional[float] = Field(None, description="Estimated total run cost in USD")
    finish_reason: Optional[str] = Field(None, description="Stop/finish reason from provider")
    retry_count: int = Field(0, description="Number of retries executed")

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> LLMResponse:
        """Generate text completion from provider."""
        pass

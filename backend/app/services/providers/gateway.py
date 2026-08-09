from typing import Optional

from app.services.providers.base import BaseLLMProvider, LLMResponse
from app.services.providers.exceptions import LLMProviderError
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider

class ModelGateway:
    def __init__(
        self,
        groq_provider: Optional[BaseLLMProvider] = None,
        gemini_provider: Optional[BaseLLMProvider] = None,
    ):
        self.groq_provider = groq_provider or GroqProvider()
        self.gemini_provider = gemini_provider or GeminiProvider()

    async def generate(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> LLMResponse:
        """Route generation request to the appropriate LLM provider."""
        prov = (provider or "").strip().lower()

        if prov == "groq":
            return await self.groq_provider.generate(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        elif prov == "gemini":
            return await self.gemini_provider.generate(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        else:
            raise LLMProviderError(
                f"Unsupported provider '{provider}'. Supported providers: groq, gemini",
                provider=provider,
            )

import asyncio
import time
from typing import List, Optional

from groq import AsyncGroq, APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, RateLimitError

from app.core.config import settings
from app.services.providers.base import BaseLLMProvider, LLMResponse
from app.services.providers.exceptions import (
    LLMProviderError,
    ProviderAuthenticationError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderTimeoutError,
)
from app.services.providers.pricing import calculate_estimated_cost

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key

    def _get_api_key(self) -> str:
        key = self._api_key or settings.GROQ_API_KEY
        if not key or not key.strip():
            raise ProviderNotConfiguredError(
                "Groq API key is not configured in environment.", provider="groq"
            )
        return key.strip()

    async def generate(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> LLMResponse:
        api_key = self._get_api_key()
        client = AsyncGroq(api_key=api_key)

        messages: List[dict] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": user_prompt})

        max_retries = 2
        last_exception: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            start_time = time.perf_counter()
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                choice = response.choices[0]
                text = choice.message.content or ""
                finish_reason = getattr(choice, "finish_reason", None)

                input_tokens = getattr(response.usage, "prompt_tokens", None) if response.usage else None
                output_tokens = getattr(response.usage, "completion_tokens", None) if response.usage else None
                total_tokens = getattr(response.usage, "total_tokens", None) if response.usage else None

                cost = calculate_estimated_cost(model, input_tokens, output_tokens)

                return LLMResponse(
                    text=text,
                    provider="groq",
                    model=model,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    estimated_cost=cost,
                    finish_reason=finish_reason,
                    retry_count=attempt,
                )

            except AuthenticationError as e:
                raise ProviderAuthenticationError(
                    f"Groq authentication failed: {str(e)}", provider="groq"
                ) from e
            except RateLimitError as e:
                last_exception = ProviderRateLimitError(
                    f"Groq rate limit exceeded: {str(e)}", provider="groq"
                )
            except APITimeoutError as e:
                last_exception = ProviderTimeoutError(
                    f"Groq request timed out: {str(e)}", provider="groq"
                )
            except (APIConnectionError, APIStatusError) as e:
                status_code = getattr(e, "status_code", None)
                if status_code and 400 <= status_code < 500 and status_code not in (429, 408):
                    raise ProviderRequestError(
                        f"Groq request error ({status_code}): {str(e)}", provider="groq"
                    ) from e
                last_exception = LLMProviderError(
                    f"Groq provider error ({status_code}): {str(e)}", provider="groq"
                )
            except Exception as e:
                raise LLMProviderError(f"Unexpected Groq error: {str(e)}", provider="groq") from e

            # If transient error, delay before retry
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))

        if last_exception:
            raise last_exception
        raise LLMProviderError("Groq request failed after retries.", provider="groq")

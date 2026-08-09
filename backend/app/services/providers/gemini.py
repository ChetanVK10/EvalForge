import asyncio
import re
import time
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

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


def sanitize_error(message: str, api_key: Optional[str] = None) -> str:
    """Sanitize error messages to redact sensitive API keys or credentials."""
    if not message:
        return ""
    clean = message
    if api_key and api_key.strip():
        clean = clean.replace(api_key.strip(), "[REDACTED_API_KEY]")
    clean = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", clean)
    clean = re.sub(r"key=[0-9A-Za-z-_]+", "key=[REDACTED_API_KEY]", clean)
    return clean


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key

    def _get_api_key(self) -> str:
        key = self._api_key or settings.GEMINI_API_KEY
        if not key or not key.strip():
            raise ProviderNotConfiguredError(
                "Gemini API key is not configured in environment.", provider="gemini"
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
        client = genai.Client(api_key=api_key)

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_prompt and system_prompt.strip():
            config.system_instruction = system_prompt.strip()

        max_retries = 2
        last_exception: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            start_time = time.perf_counter()
            try:
                # Execute async call with timeout limit
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model,
                        contents=user_prompt,
                        config=config,
                    ),
                    timeout=timeout,
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                text = getattr(response, "text", "") or ""

                # Extract finish_reason if available
                finish_reason = None
                if getattr(response, "candidates", None) and len(response.candidates) > 0:
                    cand = response.candidates[0]
                    finish_reason = str(getattr(cand, "finish_reason", "")) or None

                # Extract token usage metadata
                input_tokens = None
                output_tokens = None
                total_tokens = None
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    input_tokens = getattr(usage, "prompt_token_count", None)
                    output_tokens = getattr(usage, "candidates_token_count", None)
                    total_tokens = getattr(usage, "total_token_count", None)

                cost = calculate_estimated_cost(model, input_tokens, output_tokens)

                return LLMResponse(
                    text=text,
                    provider="gemini",
                    model=model,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    estimated_cost=cost,
                    finish_reason=finish_reason,
                    retry_count=attempt,
                )

            except asyncio.TimeoutError as e:
                last_exception = ProviderTimeoutError(
                    f"Gemini request timed out after {timeout} seconds.", provider="gemini"
                )
            except APIError as e:
                code = getattr(e, "code", None)
                msg = str(e)
                safe_msg = sanitize_error(msg, api_key)
                if code == 404 or "not_found" in msg.lower() or "not found" in msg.lower() or "is no longer available" in msg.lower():
                    raise ProviderRequestError(
                        f"Gemini model unavailable (404): {safe_msg}", provider="gemini"
                    ) from e
                elif code in (401, 403) or "unauthorized" in msg.lower() or "api_key" in msg.lower():
                    raise ProviderAuthenticationError(
                        f"Gemini authentication failed (401/403): {safe_msg}", provider="gemini"
                    ) from e
                elif code == 429 or "resource_exhausted" in msg.lower() or "quota" in msg.lower():
                    raise ProviderRateLimitError(
                        f"Gemini rate limit / quota exceeded (429 RESOURCE_EXHAUSTED): {safe_msg}", provider="gemini"
                    ) from e
                elif code and 400 <= code < 500:
                    raise ProviderRequestError(
                        f"Gemini request error ({code}): {safe_msg}", provider="gemini"
                    ) from e
                else:
                    last_exception = LLMProviderError(
                        f"Gemini API error ({code}): {safe_msg}", provider="gemini"
                    )
            except Exception as e:
                safe_msg = sanitize_error(str(e), api_key)
                raise LLMProviderError(f"Unexpected Gemini error: {safe_msg}", provider="gemini") from e

            # Retry transient failures
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))

        if last_exception:
            raise last_exception
        raise LLMProviderError("Gemini request failed after retries.", provider="gemini")

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.providers.base import LLMResponse
from app.services.providers.exceptions import (
    LLMProviderError,
    ProviderAuthenticationError,
    ProviderNotConfiguredError,
    ProviderTimeoutError,
)
from app.services.providers.gateway import ModelGateway

router = APIRouter()
gateway = ModelGateway()

class ProviderTestRequest(BaseModel):
    provider: str = Field(..., description="LLM provider: groq or gemini")
    model: str = Field(..., description="Model identifier")
    prompt: str = Field("Reply with exactly: OK", description="Test user prompt")
    system_prompt: Optional[str] = Field("You are a helpful assistant.", description="Optional system prompt")
    temperature: float = Field(0.0, description="Sampling temperature")
    max_tokens: int = Field(64, description="Max tokens")

@router.post(
    "/test",
    response_model=LLMResponse,
    status_code=status.HTTP_200_OK,
    summary="Test provider connectivity",
)
async def test_provider(payload: ProviderTestRequest):
    """Test LLM provider connectivity and receive normalized response telemetry."""
    try:
        response = await gateway.generate(
            provider=payload.provider,
            model=payload.model,
            system_prompt=payload.system_prompt or "",
            user_prompt=payload.prompt,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
        return response
    except ProviderNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except ProviderAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        ) from e
    except ProviderTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=e.message,
        ) from e
    except LLMProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=e.message,
        ) from e

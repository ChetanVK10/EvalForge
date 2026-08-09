from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.providers.base import LLMResponse
from app.services.providers.exceptions import (
    LLMProviderError,
    ProviderAuthenticationError,
    ProviderNotConfiguredError,
)
from app.services.providers.gateway import ModelGateway
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider

from google.genai.errors import APIError

@pytest.mark.asyncio
async def test_gateway_routing():
    mock_groq = MagicMock()
    mock_groq.generate = AsyncMock(return_value=LLMResponse(
        text="Groq OK", provider="groq", model="llama-3.3-70b-versatile", latency_ms=120
    ))

    mock_gemini = MagicMock()
    mock_gemini.generate = AsyncMock(return_value=LLMResponse(
        text="Gemini OK", provider="gemini", model="gemini-3.6-flash", latency_ms=150
    ))

    gateway = ModelGateway(groq_provider=mock_groq, gemini_provider=mock_gemini)

    # Test Groq routing
    res_groq = await gateway.generate(
        provider="groq", model="llama-3.3-70b-versatile", system_prompt="", user_prompt="Hi"
    )
    assert res_groq.text == "Groq OK"
    assert res_groq.provider == "groq"
    mock_groq.generate.assert_called_once()

    # Test Gemini routing
    res_gemini = await gateway.generate(
        provider="gemini", model="gemini-3.6-flash", system_prompt="", user_prompt="Hi"
    )
    assert res_gemini.text == "Gemini OK"
    assert res_gemini.provider == "gemini"
    mock_gemini.generate.assert_called_once()

@pytest.mark.asyncio
async def test_gateway_unsupported_provider():
    gateway = ModelGateway()
    with pytest.raises(LLMProviderError) as exc:
        await gateway.generate(provider="unsupported", model="m", system_prompt="", user_prompt="Hi")
    assert "Unsupported provider" in str(exc.value)

@pytest.mark.asyncio
async def test_groq_missing_api_key(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.GROQ_API_KEY", "")
    provider = GroqProvider()
    with pytest.raises(ProviderNotConfiguredError):
        await provider.generate(model="m", system_prompt="", user_prompt="Hi")

@pytest.mark.asyncio
async def test_gemini_missing_api_key(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "")
    provider = GeminiProvider()
    with pytest.raises(ProviderNotConfiguredError):
        await provider.generate(model="m", system_prompt="", user_prompt="Hi")

@pytest.mark.asyncio
async def test_groq_successful_response():
    provider = GroqProvider(api_key="gsk_mock")

    mock_choice = MagicMock()
    mock_choice.message.content = "Groq test answer"
    mock_choice.finish_reason = "stop"

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_usage.total_tokens = 15

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    with patch("app.services.providers.groq.AsyncGroq") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        res = await provider.generate(
            model="llama-3.3-70b-versatile",
            system_prompt="You are helpful.",
            user_prompt="Hello",
        )

        assert res.text == "Groq test answer"
        assert res.provider == "groq"
        assert res.input_tokens == 10
        assert res.output_tokens == 5
        assert res.total_tokens == 15
        assert res.finish_reason == "stop"
        assert res.latency_ms >= 0
        assert res.estimated_cost is not None

@pytest.mark.asyncio
async def test_gemini_successful_response():
    provider = GeminiProvider(api_key="AIzaSyTESTSECRETKEY1234567890ABCDEF")

    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"

    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 12
    mock_usage.candidates_token_count = 8
    mock_usage.total_token_count = 20

    mock_response = MagicMock()
    mock_response.text = "Gemini test answer"
    mock_response.candidates = [mock_candidate]
    mock_response.usage_metadata = mock_usage

    with patch("app.services.providers.gemini.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        res = await provider.generate(
            model="gemini-3.6-flash",
            system_prompt="System instructions",
            user_prompt="Hello Gemini",
        )

        assert res.text == "Gemini test answer"
        assert res.provider == "gemini"
        assert res.input_tokens == 12
        assert res.output_tokens == 8
        assert res.total_tokens == 20
        assert res.latency_ms >= 0
        assert res.estimated_cost is None  # Unverified pricing returns None safely

class MockAPIError(APIError):
    def __init__(self, code: int, message: str):
        Exception.__init__(self, message)
        self.code = code
        self.message = message

    def __str__(self):
        return self.message

@pytest.mark.asyncio
async def test_gemini_404_model_unavailable():
    secret_key = "AIzaSyTESTSECRETKEY1234567890ABCDEF"
    provider = GeminiProvider(api_key=secret_key)
    err = MockAPIError(404, f"This model models/gemini-2.5-flash is no longer available?key={secret_key}")

    with patch("app.services.providers.gemini.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=err)
        mock_client_cls.return_value = mock_client

        from app.services.providers.exceptions import ProviderRequestError
        with pytest.raises(ProviderRequestError) as exc:
            await provider.generate(model="gemini-2.5-flash", system_prompt="", user_prompt="Test")

        err_text = str(exc.value)
        assert "Gemini model unavailable (404)" in err_text
        assert secret_key not in err_text
        assert "[REDACTED_API_KEY]" in err_text

@pytest.mark.asyncio
async def test_gemini_429_rate_limit():
    secret_key = "AIzaSyTESTSECRETKEY1234567890ABCDEF"
    provider = GeminiProvider(api_key=secret_key)
    err = MockAPIError(429, f"RESOURCE_EXHAUSTED: Quota exceeded for AIzaSyTESTSECRETKEY1234567890ABCDEF")

    with patch("app.services.providers.gemini.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=err)
        mock_client_cls.return_value = mock_client

        from app.services.providers.exceptions import ProviderRateLimitError
        with pytest.raises(ProviderRateLimitError) as exc:
            await provider.generate(model="gemini-3.6-flash", system_prompt="", user_prompt="Test")

        err_text = str(exc.value)
        assert "RESOURCE_EXHAUSTED" in err_text
        assert secret_key not in err_text
        assert "[REDACTED_API_KEY]" in err_text

@pytest.mark.asyncio
async def test_gemini_401_authentication_error():
    secret_key = "AIzaSyTESTSECRETKEY1234567890ABCDEF"
    provider = GeminiProvider(api_key=secret_key)
    err = MockAPIError(401, f"API_KEY_INVALID: key={secret_key}")

    with patch("app.services.providers.gemini.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=err)
        mock_client_cls.return_value = mock_client

        with pytest.raises(ProviderAuthenticationError) as exc:
            await provider.generate(model="gemini-3.6-flash", system_prompt="", user_prompt="Test")

        err_text = str(exc.value)
        assert "Gemini authentication failed" in err_text
        assert secret_key not in err_text

def test_provider_test_endpoint_mock(client):
    mock_res = LLMResponse(
        text="OK",
        provider="groq",
        model="llama-3.3-70b-versatile",
        latency_ms=110,
        input_tokens=5,
        output_tokens=2,
        total_tokens=7,
        finish_reason="stop",
    )
    with patch("app.api.v1.providers.gateway.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_res

        payload = {
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "prompt": "Reply with exactly: OK"
        }
        response = client.post("/api/v1/providers/test", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "OK"
        assert data["provider"] == "groq"
        assert data["latency_ms"] == 110

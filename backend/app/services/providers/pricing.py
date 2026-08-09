from typing import Optional

# Static estimated pricing per 1,000,000 tokens (in USD)
# Note: gemini-3.6-flash pricing is not officially configured/verified, so unlisted models
# return None to safely treat estimated cost as unknown (preserves token accounting).
MODEL_PRICING = {
    # Groq models
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
    # Historical Gemini models retained for legacy experiment calculations
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
}

def calculate_estimated_cost(
    model: str, input_tokens: Optional[int], output_tokens: Optional[int]
) -> Optional[float]:
    """Calculate estimated token cost based on static pricing registry."""
    if input_tokens is None or output_tokens is None or model not in MODEL_PRICING:
        return None
    pricing = MODEL_PRICING[model]
    input_cost = (input_tokens / 1_000_000.0) * pricing["input"]
    output_cost = (output_tokens / 1_000_000.0) * pricing["output"]
    return round(input_cost + output_cost, 6)

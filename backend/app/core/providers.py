from typing import Dict, List

PROVIDER_MODELS: Dict[str, List[str]] = {
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ],
    "gemini": [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ],
}

PROVIDER_LABELS: Dict[str, str] = {
    "groq": "Groq",
    "gemini": "Google Gemini",
}

def is_valid_provider_model(provider: str, model: str) -> bool:
    prov = (provider or "").strip().lower()
    mod = (model or "").strip()
    return prov in PROVIDER_MODELS and mod in PROVIDER_MODELS[prov]

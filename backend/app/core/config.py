import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "LLM EvalOps API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/llm_evalops"
    FRONTEND_ORIGIN: str = "http://localhost:8080"
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001,"
        "http://localhost:3002,http://127.0.0.1:3002,"
        "http://localhost:3003,http://127.0.0.1:3003,"
        "http://localhost:8080,http://127.0.0.1:8080"
    )

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    DASHBOARD_CACHE_TTL_SECONDS: int = 60

    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        origins: set = set()
        if self.FRONTEND_ORIGIN and self.FRONTEND_ORIGIN != "*":
            origins.add(self.FRONTEND_ORIGIN.strip())
        if self.CORS_ORIGINS:
            for item in self.CORS_ORIGINS.split(","):
                cleaned = item.strip()
                if cleaned:
                    origins.add(cleaned)
        return sorted(list(origins))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

settings = Settings()

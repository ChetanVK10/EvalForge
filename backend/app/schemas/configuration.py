from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.providers import PROVIDER_MODELS

VALID_PROMPT_STATUSES = {"active", "draft", "archived"}

class ModelConfigurationCreate(BaseModel):
    name: str = Field(..., description="Configuration name")
    provider: str = Field(..., description="LLM provider: groq or gemini")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(0.2, description="Sampling temperature (0.0 to 2.0)")
    max_tokens: int = Field(1024, description="Maximum token limit")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Configuration name is required.")
        return v.strip()

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        prov = (v or "").strip().lower()
        if prov not in PROVIDER_MODELS:
            raise ValueError(f"Invalid provider '{v}'. Supported providers: {', '.join(sorted(PROVIDER_MODELS.keys()))}")
        return prov

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Model identifier is required.")
        return v.strip()

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if v < 0.0 or v > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Max tokens must be greater than 0")
        return v

    @model_validator(mode="after")
    def validate_provider_model_combination(self) -> "ModelConfigurationCreate":
        prov = self.provider.strip().lower()
        mod = self.model.strip()
        valid_models = PROVIDER_MODELS.get(prov, [])
        if mod not in valid_models:
            raise ValueError(
                f"Model '{mod}' is not compatible with provider '{prov}'. "
                f"Supported models for provider '{prov}': {', '.join(valid_models)}"
            )
        return self

class ModelConfigurationUpdate(BaseModel):
    name: str = Field(..., description="Configuration name")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(0.2, description="Sampling temperature (0.0 to 2.0)")
    max_tokens: int = Field(1024, description="Maximum token limit")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Configuration name is required.")
        return v.strip()

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Model identifier is required.")
        return v.strip()

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if v < 0.0 or v > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Max tokens must be greater than 0")
        return v

class ModelConfigurationResponse(BaseModel):
    id: str
    name: str
    provider: str
    model: str
    temperature: float
    max_tokens: int
    created_at: datetime

    model_config = {"from_attributes": True}

class PromptVersionCreate(BaseModel):
    system_prompt: str = Field(..., description="System prompt content")
    user_template: str = Field("{{input}}", description="User prompt template with {{input}} placeholder")
    notes: Optional[str] = Field("", description="Version notes or changelog")

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("System prompt is required.")
        return v.strip()

class PromptVersionResponse(BaseModel):
    id: str
    version: int
    system_prompt: str
    user_template: str
    notes: Optional[str] = ""
    created_at: datetime

    model_config = {"from_attributes": True}

class PromptCreate(BaseModel):
    name: str = Field(..., description="Prompt name")
    status: str = Field("draft", description="Prompt status: active, draft, archived")
    system_prompt: str = Field(..., description="Initial version system prompt")
    user_template: str = Field("{{input}}", description="User prompt template")
    notes: Optional[str] = Field("", description="Version notes")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Prompt name is required.")
        return v.strip()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        st = (v or "draft").strip().lower()
        if st not in VALID_PROMPT_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed: {', '.join(sorted(VALID_PROMPT_STATUSES))}")
        return st

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("System prompt is required.")
        return v.strip()

class PromptUpdate(BaseModel):
    name: str = Field(..., description="Prompt configuration name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Prompt name is required.")
        return v.strip()

class PromptResponse(BaseModel):
    id: str
    name: str
    status: str
    latest_version: int
    versions: List[PromptVersionResponse]
    created_at: datetime

    model_config = {"from_attributes": True}

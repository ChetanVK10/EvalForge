from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, joinedload

from app.models.configuration import ModelConfiguration, Prompt, PromptVersion
from app.models.experiment import Experiment
from app.schemas.configuration import (
    ModelConfigurationCreate,
    ModelConfigurationUpdate,
    ModelConfigurationResponse,
    PromptCreate,
    PromptResponse,
    PromptUpdate,
    PromptVersionCreate,
    PromptVersionResponse,
)

def _build_prompt_response(prompt: Prompt) -> PromptResponse:
    versions_sorted = sorted(prompt.versions, key=lambda v: v.version)
    latest_version = versions_sorted[-1].version if versions_sorted else 0
    return PromptResponse(
        id=prompt.id,
        name=prompt.name,
        status=prompt.status,
        latest_version=latest_version,
        versions=[PromptVersionResponse.model_validate(v) for v in versions_sorted],
        created_at=prompt.created_at,
    )

def create_model_configuration(
    db: Session, payload: ModelConfigurationCreate
) -> ModelConfigurationResponse:
    config = ModelConfiguration(
        name=payload.name,
        provider=payload.provider,
        model=payload.model,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return ModelConfigurationResponse.model_validate(config)

def list_model_configurations(db: Session) -> List[ModelConfigurationResponse]:
    stmt = select(ModelConfiguration).order_by(ModelConfiguration.created_at.desc())
    configs = db.scalars(stmt).all()
    return [ModelConfigurationResponse.model_validate(c) for c in configs]

def update_model_configuration(
    db: Session, config_id: str, payload: ModelConfigurationUpdate
) -> ModelConfigurationResponse:
    config = db.get(ModelConfiguration, config_id)
    if not config:
        raise KeyError(f"Model configuration with ID '{config_id}' not found.")

    from app.core.providers import PROVIDER_MODELS

    valid_models = PROVIDER_MODELS.get(config.provider, [])
    if payload.model not in valid_models:
        raise ValueError(
            f"Model '{payload.model}' is not compatible with provider '{config.provider}'. "
            f"Supported models for provider '{config.provider}': {', '.join(valid_models)}"
        )

    config.name = payload.name
    config.model = payload.model
    config.temperature = payload.temperature
    config.max_tokens = payload.max_tokens

    db.commit()
    db.refresh(config)
    return ModelConfigurationResponse.model_validate(config)

def delete_model_configuration(db: Session, config_id: str) -> None:
    config = db.get(ModelConfiguration, config_id)
    if not config:
        raise KeyError(f"Model configuration with ID '{config_id}' not found.")
    
    ref_exp = db.scalars(select(Experiment).where(Experiment.model_config_id == config_id)).first()
    if ref_exp:
        raise ValueError(
            f"Cannot delete model configuration '{config.name}' because it is referenced by existing experiment history."
        )

    db.delete(config)
    db.commit()

def create_prompt_configuration(db: Session, payload: PromptCreate) -> PromptResponse:
    prompt = Prompt(
        name=payload.name,
        status=payload.status,
    )
    db.add(prompt)
    db.flush()

    initial_version = PromptVersion(
        prompt_id=prompt.id,
        version=1,
        system_prompt=payload.system_prompt,
        user_template=payload.user_template or "{{input}}",
        notes=payload.notes or "",
    )
    db.add(initial_version)

    db.commit()
    db.refresh(prompt)
    return _build_prompt_response(prompt)

def list_prompt_configurations(db: Session) -> List[PromptResponse]:
    stmt = (
        select(Prompt)
        .options(joinedload(Prompt.versions))
        .order_by(Prompt.created_at.desc())
    )
    prompts = db.scalars(stmt).unique().all()
    return [_build_prompt_response(p) for p in prompts]

def get_prompt_configuration(db: Session, prompt_id: str) -> Optional[PromptResponse]:
    stmt = (
        select(Prompt)
        .options(joinedload(Prompt.versions))
        .where(Prompt.id == prompt_id)
    )
    prompt = db.scalars(stmt).first()
    if not prompt:
        return None
    return _build_prompt_response(prompt)

def create_prompt_version(
    db: Session, prompt_id: str, payload: PromptVersionCreate
) -> Optional[PromptVersionResponse]:
    prompt = db.get(Prompt, prompt_id)
    if not prompt:
        return None

    # Calculate next version = max(existing) + 1
    existing_versions = db.scalars(
        select(PromptVersion.version).where(PromptVersion.prompt_id == prompt_id)
    ).all()
    next_version = (max(existing_versions) + 1) if existing_versions else 1

    new_version = PromptVersion(
        prompt_id=prompt_id,
        version=next_version,
        system_prompt=payload.system_prompt,
        user_template=payload.user_template or "{{input}}",
        notes=payload.notes or "",
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return PromptVersionResponse.model_validate(new_version)

def update_prompt_version(
    db: Session, prompt_id: str, version: int, payload: PromptVersionCreate
) -> Optional[PromptVersionResponse]:
    stmt = select(PromptVersion).where(
        PromptVersion.prompt_id == prompt_id, PromptVersion.version == version
    )
    prompt_version = db.scalars(stmt).first()
    if not prompt_version:
        return None

    prompt_version.system_prompt = payload.system_prompt
    prompt_version.user_template = payload.user_template or "{{input}}"
    prompt_version.notes = payload.notes or ""

    db.commit()
    db.refresh(prompt_version)
    return PromptVersionResponse.model_validate(prompt_version)

def update_prompt_configuration(
    db: Session, prompt_id: str, payload: PromptUpdate
) -> Optional[PromptResponse]:
    prompt = db.get(Prompt, prompt_id)
    if not prompt:
        return None
    prompt.name = payload.name
    db.commit()
    db.refresh(prompt)
    return _build_prompt_response(prompt)

def delete_prompt_configuration(db: Session, prompt_id: str) -> None:
    prompt = db.get(Prompt, prompt_id)
    if not prompt:
        raise KeyError(f"Prompt configuration with ID '{prompt_id}' not found.")
    
    version_ids = [v.id for v in prompt.versions]
    ref_exp = db.scalars(
        select(Experiment).where(
            or_(
                Experiment.prompt_id == prompt_id,
                Experiment.prompt_version_id.in_(version_ids),
            )
        )
    ).first()
    if ref_exp:
        raise ValueError(
            f"Cannot delete prompt configuration '{prompt.name}' because it is referenced by existing experiment history."
        )

    db.delete(prompt)
    db.commit()

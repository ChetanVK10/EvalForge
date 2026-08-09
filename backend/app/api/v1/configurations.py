from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
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
from app.services import configuration_service

router = APIRouter()

# ---------------------------------------------------------------------------
# Model Configurations Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/models",
    response_model=List[ModelConfigurationResponse],
    status_code=status.HTTP_200_OK,
    summary="List model configurations",
)
def list_model_configurations(db: Session = Depends(get_db)):
    """List all model configurations ordered by creation date."""
    return configuration_service.list_model_configurations(db)

@router.post(
    "/models",
    response_model=ModelConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create model configuration",
)
def create_model_configuration(
    payload: ModelConfigurationCreate,
    db: Session = Depends(get_db),
):
    """Create a new model configuration."""
    return configuration_service.create_model_configuration(db, payload)

@router.put(
    "/models/{config_id}",
    response_model=ModelConfigurationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update model configuration",
)
def update_model_configuration(
    config_id: str,
    payload: ModelConfigurationUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing model configuration."""
    try:
        return configuration_service.update_model_configuration(db, config_id, payload)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete(
    "/models/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete model configuration",
)
def delete_model_configuration(
    config_id: str,
    db: Session = Depends(get_db),
):
    """Delete a model configuration if unreferenced by experiment history."""
    try:
        configuration_service.delete_model_configuration(db, config_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

# ---------------------------------------------------------------------------
# Prompt Configurations Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/prompts",
    response_model=List[PromptResponse],
    status_code=status.HTTP_200_OK,
    summary="List prompt configurations",
)
def list_prompt_configurations(db: Session = Depends(get_db)):
    """List all versioned prompt configurations."""
    return configuration_service.list_prompt_configurations(db)

@router.post(
    "/prompts",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create prompt configuration",
)
def create_prompt_configuration(
    payload: PromptCreate,
    db: Session = Depends(get_db),
):
    """Create a new prompt configuration and its initial version (version 1)."""
    return configuration_service.create_prompt_configuration(db, payload)

@router.delete(
    "/prompts/{prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete prompt configuration",
)
def delete_prompt_configuration(
    prompt_id: str,
    db: Session = Depends(get_db),
):
    """Delete a prompt configuration if unreferenced by experiment history."""
    try:
        configuration_service.delete_prompt_configuration(db, prompt_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.args[0])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get(
    "/prompts/{prompt_id}",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Get prompt configuration",
)
def get_prompt_configuration(
    prompt_id: str,
    db: Session = Depends(get_db),
):
    """Get detailed prompt configuration by ID."""
    result = configuration_service.get_prompt_configuration(db, prompt_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt configuration with ID '{prompt_id}' not found.",
        )
    return result

@router.put(
    "/prompts/{prompt_id}",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
    summary="Update prompt configuration metadata",
)
def update_prompt_configuration(
    prompt_id: str,
    payload: PromptUpdate,
    db: Session = Depends(get_db),
):
    """Update prompt configuration metadata (e.g. name)."""
    result = configuration_service.update_prompt_configuration(db, prompt_id, payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt configuration with ID '{prompt_id}' not found.",
        )
    return result

@router.post(
    "/prompts/{prompt_id}/versions",
    response_model=PromptVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add prompt version",
)
def create_prompt_version(
    prompt_id: str,
    payload: PromptVersionCreate,
    db: Session = Depends(get_db),
):
    """Add a new version to an existing prompt configuration (auto-incrementing version number)."""
    result = configuration_service.create_prompt_version(db, prompt_id, payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt configuration with ID '{prompt_id}' not found.",
        )
    return result

@router.put(
    "/prompts/{prompt_id}/versions/{version}",
    response_model=PromptVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update prompt version",
)
def update_prompt_version(
    prompt_id: str,
    version: int,
    payload: PromptVersionCreate,
    db: Session = Depends(get_db),
):
    """Update system prompt, user template, or notes for a specific prompt version."""
    result = configuration_service.update_prompt_version(db, prompt_id, version, payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt version {version} for prompt ID '{prompt_id}' not found.",
        )
    return result

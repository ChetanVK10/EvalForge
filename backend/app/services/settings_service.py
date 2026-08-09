from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.core.providers import PROVIDER_LABELS, PROVIDER_MODELS
from app.models.settings import WorkspaceSettings
from app.schemas.settings import (
    EvaluationDefaults,
    ProviderStatusResponse,
    RegressionThresholds,
    SettingsResponse,
)

DEFAULT_EVALUATION_DEFAULTS = {
    "default_metrics": ["semantic_similarity", "llm_judge", "response_completeness"],
    "concurrency": 5,
    "judge_model": "llama-3.3-70b-versatile",
}

DEFAULT_REGRESSION_THRESHOLDS = {
    "max_quality_regression_pct": 3.0,
    "max_factuality_regression_pct": 2.0,
    "max_latency_increase_pct": 15.0,
    "max_cost_increase_pct": 20.0,
    "critical_categories": ["billing"],
}

STATIC_PROVIDERS = [
    {
        "provider": prov,
        "label": PROVIDER_LABELS[prov],
        "models": models,
    }
    for prov, models in PROVIDER_MODELS.items()
]

def get_or_create_settings(db: Session) -> WorkspaceSettings:
    settings_obj = db.get(WorkspaceSettings, "default")
    if not settings_obj:
        settings_obj = WorkspaceSettings(
            id="default",
            evaluation_defaults_json=DEFAULT_EVALUATION_DEFAULTS,
            regression_thresholds_json=DEFAULT_REGRESSION_THRESHOLDS,
        )
        db.add(settings_obj)
        db.commit()
        db.refresh(settings_obj)
    return settings_obj

def get_settings(db: Session) -> SettingsResponse:
    settings_obj = get_or_create_settings(db)
    
    groq_configured = bool(app_settings.GROQ_API_KEY and app_settings.GROQ_API_KEY.strip())
    gemini_configured = bool(app_settings.GEMINI_API_KEY and app_settings.GEMINI_API_KEY.strip())
    status_map = {
        "groq": groq_configured,
        "gemini": gemini_configured,
    }

    providers = [
        ProviderStatusResponse(
            provider=prov,
            label=PROVIDER_LABELS[prov],
            configured=status_map.get(prov, False),
            models=models,
        )
        for prov, models in PROVIDER_MODELS.items()
    ]

    return SettingsResponse(
        evaluation_defaults=EvaluationDefaults.model_validate(settings_obj.evaluation_defaults_json),
        regression_thresholds=RegressionThresholds.model_validate(settings_obj.regression_thresholds_json),
        providers=providers,
    )

def update_evaluation_defaults(db: Session, payload: EvaluationDefaults) -> EvaluationDefaults:
    settings_obj = get_or_create_settings(db)
    settings_obj.evaluation_defaults_json = payload.model_dump()
    db.commit()
    db.refresh(settings_obj)
    return EvaluationDefaults.model_validate(settings_obj.evaluation_defaults_json)

def update_regression_thresholds(db: Session, payload: RegressionThresholds) -> RegressionThresholds:
    settings_obj = get_or_create_settings(db)
    settings_obj.regression_thresholds_json = payload.model_dump()
    db.commit()
    db.refresh(settings_obj)
    return RegressionThresholds.model_validate(settings_obj.regression_thresholds_json)

from fastapi import APIRouter
from app.api.v1 import configurations, dashboard, datasets, evaluations, evaluators, experiments, health, providers, ready, regressions, settings

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["System"])
api_v1_router.include_router(ready.router, tags=["System"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_v1_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_v1_router.include_router(configurations.router, prefix="/configurations", tags=["Configurations"])
api_v1_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_v1_router.include_router(providers.router, prefix="/providers", tags=["Providers"])
api_v1_router.include_router(evaluators.router, prefix="/evaluators", tags=["Evaluators"])
api_v1_router.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluations"])
api_v1_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])
api_v1_router.include_router(regressions.router, prefix="/regressions", tags=["Regressions"])

# Additional router aliases for frontend endpoint parity
prompts_alias_router = APIRouter(prefix="/prompts", tags=["Prompts"])
prompts_alias_router.add_api_route("", configurations.list_prompt_configurations, methods=["GET"])
prompts_alias_router.add_api_route("", configurations.create_prompt_configuration, methods=["POST"], status_code=201)
prompts_alias_router.add_api_route("/{prompt_id}", configurations.get_prompt_configuration, methods=["GET"])
prompts_alias_router.add_api_route("/{prompt_id}", configurations.update_prompt_configuration, methods=["PUT"])
prompts_alias_router.add_api_route("/{prompt_id}", configurations.delete_prompt_configuration, methods=["DELETE"])
prompts_alias_router.add_api_route("/{prompt_id}/versions", configurations.create_prompt_version, methods=["POST"], status_code=201)
prompts_alias_router.add_api_route("/{prompt_id}/versions/{version}", configurations.update_prompt_version, methods=["PUT"])

models_alias_router = APIRouter(prefix="/models", tags=["Models"])
models_alias_router.add_api_route("", configurations.list_model_configurations, methods=["GET"])
models_alias_router.add_api_route("", configurations.create_model_configuration, methods=["POST"], status_code=201)
models_alias_router.add_api_route("/{config_id}", configurations.delete_model_configuration, methods=["DELETE"])

api_v1_router.include_router(prompts_alias_router)
api_v1_router.include_router(models_alias_router)

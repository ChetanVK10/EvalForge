from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.core.database import SessionLocal
from app.models.configuration import ModelConfiguration, Prompt, PromptVersion
from app.models.dataset import Dataset
from app.models.experiment import EvaluationScore, Experiment, TestCaseResult
from app.services.cache_service import cache_service
from app.schemas.experiment import (
    CategoryPerformanceResponse,
    CreateEvaluationPayload,
    EvaluationProgressResponse,
    EvaluationScoreResponse,
    ExperimentDetailResponse,
    ExperimentResponse,
    TestCaseResultResponse,
)
from app.services.experiment_runner import ExperimentRunner
from app.services.settings_service import get_settings

from app.services.experiment_runner import CASE_PASS_THRESHOLD, ExperimentRunner

runner = ExperimentRunner()

def _build_experiment_response(exp: Experiment) -> ExperimentResponse:
    snapshots = exp.snapshots_json or {}
    dataset_name = snapshots.get("dataset_name", "Dataset")
    model_config_name = snapshots.get("model_config_name", "Model Config")
    provider = snapshots.get("provider", "groq")
    model = snapshots.get("model", "llama-3.3-70b-versatile")
    prompt_name = snapshots.get("prompt_name", "Prompt")
    prompt_version = snapshots.get("prompt_version", 1)

    if exp.status == "failed":
        result_status = "FAIL"
    elif exp.status == "completed":
        valid_cases = [r for r in (exp.case_results or []) if r.case_quality_score is not None]
        if valid_cases:
            passed_cnt = sum(
                1 for r in valid_cases
                if r.status == "completed" and r.case_quality_score >= CASE_PASS_THRESHOLD
            )
            total_valid = len(valid_cases)
            if passed_cnt == total_valid and (exp.failed_cases or 0) == 0:
                result_status = "PASS"
            elif passed_cnt > 0:
                result_status = "WARNING"
            else:
                result_status = "FAIL"
        elif exp.pass_rate is not None and exp.completed_cases > 0:
            if exp.pass_rate == 100.0 and (exp.failed_cases or 0) == 0:
                result_status = "PASS"
            elif exp.pass_rate > 0.0:
                result_status = "WARNING"
            else:
                result_status = "FAIL"
        else:
            result_status = "FAIL"
    else:
        result_status = "PASS"

    return ExperimentResponse(
        id=exp.id,
        name=exp.name,
        dataset_id=exp.dataset_id,
        dataset_name=dataset_name,
        model_config_id=exp.model_config_id,
        model_config_name=model_config_name,
        provider=provider,
        model=model,
        prompt_id=exp.prompt_id,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        metrics=exp.metrics_json or [],
        quality_score=exp.quality_score,
        pass_rate=exp.pass_rate,
        avg_latency_ms=exp.avg_latency_ms,
        p95_latency_ms=exp.p95_latency_ms,
        total_tokens=exp.total_tokens or 0,
        estimated_cost=exp.estimated_cost,
        result_status=result_status,
        regression_status=result_status,
        status=exp.status,
        total_cases=exp.total_cases or 0,
        completed_cases=exp.completed_cases or 0,
        failed_cases=exp.failed_cases or 0,
        created_at=exp.created_at or datetime.utcnow(),
        started_at=exp.started_at,
        completed_at=exp.completed_at,
    )

def create_evaluation(
    db: Session,
    payload: CreateEvaluationPayload,
    background_tasks: BackgroundTasks,
) -> ExperimentResponse:
    dataset = db.get(Dataset, payload.dataset_id)
    if not dataset:
        raise ValueError(f"Dataset with ID '{payload.dataset_id}' not found.")

    model_config = db.get(ModelConfiguration, payload.model_config_id)
    if not model_config:
        raise ValueError(f"Model configuration with ID '{payload.model_config_id}' not found.")

    prompt = db.get(Prompt, payload.prompt_id)
    if not prompt:
        raise ValueError(f"Prompt configuration with ID '{payload.prompt_id}' not found.")

    prompt_version = None
    if payload.prompt_version_id:
        pv_stmt = select(PromptVersion).where(
            PromptVersion.prompt_id == payload.prompt_id,
            PromptVersion.id == payload.prompt_version_id,
        )
        prompt_version = db.scalars(pv_stmt).first()
        if not prompt_version:
            raise ValueError(
                f"Prompt version ID '{payload.prompt_version_id}' for prompt ID '{payload.prompt_id}' not found."
            )
    elif payload.prompt_version is not None:
        pv_stmt = select(PromptVersion).where(
            PromptVersion.prompt_id == payload.prompt_id,
            PromptVersion.version == payload.prompt_version,
        )
        prompt_version = db.scalars(pv_stmt).first()
        if not prompt_version:
            raise ValueError(
                f"Prompt version {payload.prompt_version} for prompt ID '{payload.prompt_id}' not found."
            )
    else:
        pv_stmt = (
            select(PromptVersion)
            .where(PromptVersion.prompt_id == payload.prompt_id)
            .order_by(PromptVersion.version.desc())
        )
        prompt_version = db.scalars(pv_stmt).first()
        if not prompt_version:
            raise ValueError(f"No prompt versions found for prompt ID '{payload.prompt_id}'.")

    settings_data = get_settings(db)
    concurrency = settings_data.evaluation_defaults.concurrency

    snapshots_json = {
        "dataset_name": dataset.name,
        "model_config_name": model_config.name,
        "provider": model_config.provider,
        "model": model_config.model,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
        "prompt_name": prompt.name,
        "prompt_version": prompt_version.version,
        "system_prompt": prompt_version.system_prompt,
        "user_template": prompt_version.user_template or "{{input}}",
        "concurrency": concurrency,
    }

    experiment = Experiment(
        name=payload.name,
        dataset_id=payload.dataset_id,
        model_config_id=payload.model_config_id,
        prompt_id=payload.prompt_id,
        prompt_version_id=prompt_version.id,
        status="pending",
        total_cases=len(dataset.cases),
        metrics_json=payload.metrics,
        snapshots_json=snapshots_json,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    cache_service.delete("dashboard:summary:v1")

    # Schedule background execution task using active engine sessionmaker
    session_factory = sessionmaker(bind=db.get_bind())
    background_tasks.add_task(runner.run_experiment, experiment.id, session_factory)

    return _build_experiment_response(experiment)

def get_evaluation_status(db: Session, experiment_id: str) -> Optional[EvaluationProgressResponse]:
    exp = db.get(Experiment, experiment_id)
    if not exp:
        return None

    total = max(1, exp.total_cases)
    done = exp.completed_cases + exp.failed_cases
    pct = round(min(100.0, (done / total) * 100.0), 1)

    if exp.status == "pending":
        stage = "preparing"
        msg = "Preparing evaluation..."
    elif exp.status == "running":
        stage = "running"
        msg = f"Running {done} / {exp.total_cases} cases"
    elif exp.status == "completed":
        stage = "complete"
        msg = "Evaluation complete"
    else:
        stage = "failed"
        msg = "Evaluation failed"

    return EvaluationProgressResponse(
        experiment_id=exp.id,
        status=exp.status,
        stage=stage,
        message=msg,
        total_cases=exp.total_cases,
        completed_cases=exp.completed_cases,
        failed_cases=exp.failed_cases,
        progress_pct=pct,
    )

def list_experiments(
    db: Session,
    search: Optional[str] = None,
    dataset_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    prompt_version: Optional[int] = None,
    status_filter: Optional[str] = None,
    since: Optional[str] = None,
    date_str: Optional[str] = None,
) -> List[ExperimentResponse]:
    stmt = select(Experiment).options(joinedload(Experiment.case_results)).order_by(Experiment.created_at.desc())
    experiments = db.scalars(stmt).unique().all()
    responses = [_build_experiment_response(e) for e in experiments]

    filtered = responses
    if search:
        q = search.strip().lower()
        filtered = [
            e for e in filtered
            if q in e.name.lower()
            or q in e.id.lower()
            or q in (e.dataset_name or "").lower()
            or q in (e.prompt_name or "").lower()
            or q in e.model.lower()
        ]
    if dataset_id and dataset_id != "all":
        filtered = [e for e in filtered if e.dataset_id == dataset_id]
    if provider and provider != "all":
        p_low = provider.strip().lower()
        filtered = [e for e in filtered if e.provider.lower() == p_low]
    if model and model != "all":
        m_low = model.strip().lower()
        filtered = [e for e in filtered if e.model.lower() == m_low]
    if prompt_version is not None and str(prompt_version) != "all":
        filtered = [e for e in filtered if e.prompt_version == int(prompt_version)]
    if status_filter and status_filter != "all":
        s_up = status_filter.strip().upper()
        filtered = [e for e in filtered if e.result_status == s_up or e.regression_status == s_up]

    def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    if date_str:
        try:
            raw_date = date_str.strip()
            if "T" in raw_date:
                dt_parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                cal_date = dt_parsed.date()
            else:
                cal_date = datetime.strptime(raw_date, "%Y-%m-%d").date()

            start_dt = datetime(cal_date.year, cal_date.month, cal_date.day, 0, 0, 0, tzinfo=timezone.utc)
            end_dt = start_dt + timedelta(days=1)

            filtered = [
                e for e in filtered
                if (e_dt := _ensure_utc(e.created_at)) is not None and start_dt <= e_dt < end_dt
            ]
        except (ValueError, TypeError) as err:
            raise ValueError(f"Invalid date parameter '{date_str}': {err}")
    elif since:
        try:
            raw_since = since.strip()
            if "T" not in raw_since and len(raw_since) == 10:
                raw_since += "T00:00:00"
            since_dt = datetime.fromisoformat(raw_since.replace("Z", "+00:00"))
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=timezone.utc)

            filtered = [
                e for e in filtered
                if (e_dt := _ensure_utc(e.created_at)) is not None and e_dt >= since_dt
            ]
        except (ValueError, TypeError) as err:
            raise ValueError(f"Invalid since parameter '{since}': {err}")

    return filtered

def delete_experiment(db: Session, experiment_id: str) -> bool:
    exp = db.get(Experiment, experiment_id)
    if not exp:
        return False
    db.delete(exp)
    db.commit()
    cache_service.delete("dashboard:summary:v1")
    return True

def get_experiment_detail(
    db: Session,
    experiment_id: str,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> Optional[ExperimentDetailResponse]:
    stmt = (
        select(Experiment)
        .options(
            joinedload(Experiment.case_results).joinedload(TestCaseResult.scores)
        )
        .where(Experiment.id == experiment_id)
    )
    exp = db.scalars(stmt).unique().first()
    if not exp:
        return None

    base_resp = _build_experiment_response(exp)
    all_results = exp.case_results

    # Calculate category performance breakdown
    cat_groups: Dict[str, List[TestCaseResult]] = {}
    for r in all_results:
        cat = r.category or "general"
        cat_groups.setdefault(cat, []).append(r)

    category_scores_map: Dict[str, float] = {}
    category_breakdown_list: List[CategoryPerformanceResponse] = []

    for cat, items in cat_groups.items():
        valid_scores = [i.case_quality_score for i in items if i.case_quality_score is not None]
        avg_cat_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0.0
        failed_cat_cnt = sum(1 for i in items if i.status == "failed")

        category_scores_map[cat] = avg_cat_score
        category_breakdown_list.append(
            CategoryPerformanceResponse(
                category=cat,
                score=avg_cat_score,
                case_count=len(items),
                failed_cases=failed_cat_cnt,
            )
        )

    # Apply filters to case results list
    filtered_results = all_results
    if category:
        c_low = category.strip().lower()
        filtered_results = [r for r in filtered_results if r.category.lower() == c_low]
    if status_filter:
        s_low = status_filter.strip().lower()
        filtered_results = [r for r in filtered_results if r.status.lower() == s_low]
    if search:
        q = search.strip().lower()
        filtered_results = [
            r for r in filtered_results
            if q in r.input.lower() or q in r.expected_output.lower() or q in r.model_output.lower()
        ]

    case_result_responses = [
        TestCaseResultResponse(
            id=r.id,
            test_case_id=r.test_case_id,
            input=r.input,
            expected_output=r.expected_output,
            model_output=r.model_output,
            category=r.category,
            status=r.status,
            error=r.error,
            provider=r.provider,
            model=r.model,
            latency_ms=r.latency_ms,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            total_tokens=r.total_tokens,
            estimated_cost=r.estimated_cost,
            case_quality_score=r.case_quality_score,
            scores=[
                EvaluationScoreResponse(
                    id=s.id,
                    metric=s.metric,
                    score=s.score,
                    passed=s.passed,
                    reasoning=s.reasoning,
                    status=s.status,
                    error=s.error,
                    details=s.details_json or {},
                )
                for s in r.scores
            ],
        )
        for r in filtered_results
    ]

    return ExperimentDetailResponse(
        **base_resp.model_dump(),
        snapshots=exp.snapshots_json or {},
        category_scores=category_scores_map,
        category_breakdown=category_breakdown_list,
        case_results=case_result_responses,
    )

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.experiment import Experiment
from app.schemas.dashboard import DashboardAlert, DashboardSummaryResponse, MetricOverTime
from app.services.cache_service import cache_service
from app.services.experiment_service import _build_experiment_response

router = APIRouter()

DASHBOARD_CACHE_KEY = "dashboard:summary:v1"

@router.get(
    "",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workspace dashboard summary",
)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Retrieve aggregate workspace metrics, trends, recent experiments, and regression alerts with Redis caching."""
    # 1. Attempt Redis cache lookup
    cached_payload = cache_service.get(DASHBOARD_CACHE_KEY)
    if cached_payload:
        try:
            return DashboardSummaryResponse.model_validate_json(cached_payload)
        except Exception:
            # On deserialization error, fallback to DB query
            pass

    # 2. Database query & aggregation on cache miss
    stmt = select(Experiment).order_by(Experiment.created_at.desc())
    experiments = db.scalars(stmt).all()

    total_experiments = len(experiments)

    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        return dt.replace(tzinfo=None) if hasattr(dt, "tzinfo") and dt.tzinfo else dt

    evaluations_this_week = sum(
        1 for e in experiments if _normalize_dt(e.created_at) and _normalize_dt(e.created_at) >= seven_days_ago
    )

    valid_quality = [e.quality_score for e in experiments if e.quality_score is not None]
    avg_quality_score = round(sum(valid_quality) / len(valid_quality), 1) if valid_quality else 0.0

    valid_latency = [e.avg_latency_ms for e in experiments if e.avg_latency_ms is not None]
    avg_latency_ms = int(round(sum(valid_latency) / len(valid_latency))) if valid_latency else 0

    total_cost = sum(e.estimated_cost or 0.0 for e in experiments)
    estimated_cost = round(total_cost, 2)
    sorted_experiments = sorted(experiments, key=lambda e: _normalize_dt(e.created_at) or datetime.min)

    quality_over_time = [
        MetricOverTime(
            date=e.created_at.strftime("%b %d") if e.created_at else "—",
            score=e.quality_score,
        )
        for e in sorted_experiments
        if e.quality_score is not None
    ]

    latency_over_time = [
        MetricOverTime(
            date=e.created_at.strftime("%b %d") if e.created_at else "—",
            latency=e.avg_latency_ms,
        )
        for e in sorted_experiments
        if e.avg_latency_ms is not None
    ]

    cost_over_time = [
        MetricOverTime(
            date=e.created_at.strftime("%b %d") if e.created_at else "—",
            cost=e.estimated_cost or 0.0,
        )
        for e in sorted_experiments
    ]

    recent_experiments = [_build_experiment_response(e) for e in experiments[:6]]

    all_exp_responses = [_build_experiment_response(e) for e in experiments]
    passing_count = sum(1 for exp_resp in all_exp_responses if exp_resp.result_status == "PASS")
    regression_pass_rate = round((passing_count / len(all_exp_responses)) * 100.0, 1) if all_exp_responses else 100.0

    alerts: List[DashboardAlert] = []
    for idx, exp in enumerate(experiments[:10]):
        exp_resp = _build_experiment_response(exp)
        qual = exp.quality_score or 0.0
        if exp_resp.result_status == "FAIL":
            alerts.append(
                DashboardAlert(
                    id=f"alert-{idx + 1}",
                    severity="FAIL",
                    message=f"Experiment '{exp.name}' failed evaluation criteria (quality: {qual:.1f}%).",
                    experiment_id=exp.id,
                    created_at=exp.created_at.isoformat() if exp.created_at else now.isoformat(),
                )
            )
        elif exp_resp.result_status == "WARNING":
            alerts.append(
                DashboardAlert(
                    id=f"alert-{idx + 1}",
                    severity="WARNING",
                    message=f"Experiment '{exp.name}' quality warning (quality: {qual:.1f}%).",
                    experiment_id=exp.id,
                    created_at=exp.created_at.isoformat() if exp.created_at else now.isoformat(),
                )
            )

    response = DashboardSummaryResponse(
        total_experiments=total_experiments,
        evaluations_this_week=evaluations_this_week,
        avg_quality_score=avg_quality_score,
        avg_latency_ms=avg_latency_ms,
        estimated_cost=estimated_cost,
        regression_pass_rate=regression_pass_rate,
        quality_over_time=quality_over_time,
        latency_over_time=latency_over_time,
        cost_over_time=cost_over_time,
        recent_experiments=recent_experiments,
        alerts=alerts,
    )

    # 3. Cache the computed result in Redis
    cache_service.set(DASHBOARD_CACHE_KEY, response.model_dump_json(), ttl_seconds=settings.DASHBOARD_CACHE_TTL_SECONDS)

    return response

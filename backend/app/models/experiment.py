import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.dataset import JSONType

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id"), nullable=False)
    model_config_id: Mapped[str] = mapped_column(String(64), ForeignKey("model_configs.id"), nullable=False)
    prompt_id: Mapped[str] = mapped_column(String(64), ForeignKey("prompts.id"), nullable=False)
    prompt_version_id: Mapped[str] = mapped_column(String(64), ForeignKey("prompt_versions.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")  # pending, running, completed, failed

    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pass_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    p95_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    total_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    metrics_json: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    snapshots_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    case_results: Mapped[List["TestCaseResult"]] = relationship(
        "TestCaseResult",
        back_populates="experiment",
        cascade="all, delete-orphan",
        order_by="TestCaseResult.created_at.asc()",
    )

    __table_args__ = (
        Index("idx_experiments_status", status),
        Index("idx_experiments_created_at", created_at),
    )

class TestCaseResult(Base):
    __tablename__ = "test_case_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    experiment_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    test_case_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    model_output: Mapped[str] = mapped_column(Text, nullable=False, default="")

    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")  # completed, failed
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)

    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    case_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="case_results")
    scores: Mapped[List["EvaluationScore"]] = relationship(
        "EvaluationScore",
        back_populates="case_result",
        cascade="all, delete-orphan",
        order_by="EvaluationScore.created_at.asc()",
    )

    __table_args__ = (
        Index("idx_test_case_results_experiment_id", experiment_id),
        Index("idx_test_case_results_category", category),
    )

class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    test_case_result_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("test_case_results.id", ondelete="CASCADE"), nullable=False
    )

    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")  # success, error
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    details_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    case_result: Mapped["TestCaseResult"] = relationship("TestCaseResult", back_populates="scores")

    __table_args__ = (
        Index("idx_evaluation_scores_result_id", test_case_result_id),
        Index("idx_evaluation_scores_metric", metric),
    )

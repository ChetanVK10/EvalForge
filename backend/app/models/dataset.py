import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Cross-dialect JSON type: uses JSONB in PostgreSQL, JSON in SQLite/other dialects
JSONType = JSONB().with_variant(JSON(), "sqlite")

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    cases: Mapped[List["TestCase"]] = relationship(
        "TestCase",
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="TestCase.created_at.asc()",
    )

class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    dataset_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="cases")

__table_args__ = (
    Index("idx_test_cases_dataset_id", TestCase.dataset_id),
    Index("idx_test_cases_category", TestCase.category),
)

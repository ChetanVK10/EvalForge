from datetime import datetime
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.dataset import JSONType

class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default="default")
    evaluation_defaults_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    regression_thresholds_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

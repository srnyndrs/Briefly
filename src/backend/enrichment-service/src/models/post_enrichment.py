from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class PostEnrichment(Base):
    __tablename__ = "post_enrichments"

    post_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    enrichment_version: Mapped[str] = mapped_column(String(100), nullable=False)
    category_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('completed', 'abstained', 'failed')",
            name="ck_post_enrichments_status",
        ),
    )

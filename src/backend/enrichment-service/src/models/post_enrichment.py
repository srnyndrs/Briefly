from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.config.database import Base


class PostEnrichment(Base):
    __tablename__ = "post_enrichments"

    post_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    post_revision: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    enrichment_version: Mapped[str] = mapped_column(String(100), nullable=False)
    category_ids: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"),
        nullable=False,
        default=list,
    )
    enrichment_revision: Mapped[int] = mapped_column(
        nullable=False, default=1, server_default=text("1")
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    result_event: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=True
    )
    publication_pending: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('completed', 'abstained', 'failed')",
            name="ck_post_enrichments_status",
        ),
        CheckConstraint(
            "(status = 'completed' AND cardinality(category_ids) BETWEEN 1 AND 2) "
            "OR (status IN ('abstained', 'failed') AND cardinality(category_ids) = 0)",
            name="ck_post_enrichments_categories_status",
        ).ddl_if(dialect="postgresql"),
    )

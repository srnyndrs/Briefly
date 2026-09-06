from datetime import UTC, datetime

from sqlalchemy import (
    ARRAY,
    JSON,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    consumer_name: Mapped[str] = mapped_column(
        String(100), primary_key=True
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class PostProjection(Base):
    __tablename__ = "post_projections"

    post_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str | None] = mapped_column(
        String(64), index=True
    )
    source_title: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    canonical_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    title: Mapped[str] = mapped_column(String(1024), default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    language: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"), default=list
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_ref: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    sentiment: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    topics: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"), default=list
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        UniqueConstraint(
            "canonical_url",
            name="uq_post_projection_canonical_url",
        ),
        Index(
            "ix_post_projections_published_updated",
            "published_at",
            "updated_at",
        ),
        Index(
            "ix_post_projections_source_published",
            "source_id",
            "published_at",
        ),
        Index(
            "ix_post_projections_lang_published",
            "language",
            "published_at",
        ),
        Index(
            "ix_post_projections_keywords_gin",
            "keywords",
            postgresql_using="gin",
        ),
        Index(
            "ix_post_projections_topics_gin",
            "topics",
            postgresql_using="gin",
        ),
    )


class UserPreferencesProjection(Base):
    __tablename__ = "user_preferences_projections"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    muted_keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"), default=list
    )
    muted_categories: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"), default=list
    )
    blocked_source_ids: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"), default=list
    )
    languages: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"), default=list
    )
    category_interests: Mapped[list[str]] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"), default=list
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

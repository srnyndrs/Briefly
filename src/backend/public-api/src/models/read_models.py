from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    consumer_name: Mapped[str] = mapped_column(
        String(100), primary_key=True
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ArticleProjection(Base):
    __tablename__ = "article_projections"

    article_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    source_id: Mapped[str | None] = mapped_column(
        String(64), index=True
    )
    canonical_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    title: Mapped[str] = mapped_column(String(1024), default="")
    language: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    categories: Mapped[list[str]] = mapped_column(
        JSON, default=list
    )
    from sqlalchemy import Text

    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_ref: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    image_ref: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    sentiment: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    cluster_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    model_version: Mapped[str | None] = mapped_column(
        String(64), nullable=True
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
            name="uq_article_projection_canonical_url",
        ),
    )


class UserPreferencesProjection(Base):
    __tablename__ = "user_preferences_projections"

    user_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    preferred_categories: Mapped[list[str]] = mapped_column(
        JSON, default=list
    )
    preferred_languages: Mapped[list[str]] = mapped_column(
        JSON, default=list
    )
    excluded_languages: Mapped[list[str]] = mapped_column(
        JSON, default=list
    )
    blocked_source_ids: Mapped[list[str]] = mapped_column(
        JSON, default=list
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class UserSubscriptionProjection(Base):
    __tablename__ = "user_subscription_projections"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "source_id",
            name="uq_user_subscription_projection",
        ),
    )

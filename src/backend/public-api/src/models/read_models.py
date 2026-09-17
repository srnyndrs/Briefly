from datetime import UTC, datetime

from sqlalchemy import (
    ARRAY,
    JSON,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    literal_column,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement

from src.config.database import Base


def post_search_document(
    title: ColumnElement,
    description: ColumnElement,
    keywords: ColumnElement,
) -> ColumnElement:
    configuration = literal_column("'simple'")
    title_vector = func.setweight(
        func.to_tsvector(
            configuration, func.coalesce(title, literal_column("''"))
        ),
        literal_column("'A'"),
    )
    description_vector = func.setweight(
        func.to_tsvector(
            configuration,
            func.coalesce(description, literal_column("''")),
        ),
        literal_column("'B'"),
    )
    keywords_vector = func.setweight(
        func.to_tsvector(
            configuration,
            func.coalesce(
                func.array_to_string(keywords, literal_column("' '")),
                literal_column("''"),
            ),
        ),
        literal_column("'C'"),
    )
    return title_vector.op("||")(description_vector).op("||")(
        keywords_vector
    )


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class PostProjection(Base):
    __tablename__ = "post_projections"

    post_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    source_title: Mapped[str] = mapped_column(
        String(255), nullable=False
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


POST_SEARCH_INDEX = Index(
    "ix_post_projections_search_vector",
    post_search_document(
        PostProjection.__table__.c.title,
        PostProjection.__table__.c.description,
        PostProjection.__table__.c.keywords,
    ),
    postgresql_using="gin",
).ddl_if(dialect="postgresql")
PostProjection.__table__.append_constraint(POST_SEARCH_INDEX)

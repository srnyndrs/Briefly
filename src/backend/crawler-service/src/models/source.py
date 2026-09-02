import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class Source(Base):
    __tablename__ = "sources"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    url: Mapped[str] = mapped_column(
        String(2048), unique=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    favicon: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    website_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )

    last_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_crawl_scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_crawl_succeeded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    health_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0
    )

    etag: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    enrich_with_ai: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_sources_next_crawl_scheduled_at",
            "next_crawl_scheduled_at",
        ),
        Index("ix_sources_health_score", "health_score"),
    )

    def __repr__(self) -> str:
        return f"<Source source_id={self.source_id} url={self.url!r}>"

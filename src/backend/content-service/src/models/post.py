import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.config.database import Base


class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    source_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )
    item_guid: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    source_title: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    category: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    author: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    parsed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    image_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    language: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    keywords: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
        default=list,
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id", "item_guid", name="uix_source_guid"
        ),
    )

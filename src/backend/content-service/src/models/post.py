import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from src.config.database import Base


class Post(Base):
    __tablename__ = "posts"

    post_id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    source_id = Column(String, nullable=False, index=True)
    item_guid = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    crawled_at = Column(DateTime(timezone=True), nullable=True)
    parsed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    image_url = Column(String, nullable=True)
    language = Column(String, nullable=True)
    keywords = Column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
        default=list,
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id", "item_guid", name="uix_source_guid"
        ),
        UniqueConstraint("source_id", "url", name="uix_source_url"),
    )

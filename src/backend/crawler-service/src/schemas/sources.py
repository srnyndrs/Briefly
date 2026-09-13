import uuid
from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_serializer,
    field_validator,
)


class SourceCreate(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    favicon: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Title must not be blank")
        return normalized


class SourcePatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl | None = None
    description: str | None = None
    favicon: str | None = None


class SourceDiscoverRequest(BaseModel):
    url: HttpUrl


class SourceDiscoverResult(BaseModel):
    url: str
    title: str | None = None
    content_type: str | None = None
    favicon: str | None = None
    description: str | None = None


class SourceResponse(BaseModel):
    source_id: uuid.UUID
    url: str
    title: str
    description: str | None = None
    favicon: str | None = None
    website_url: str | None = None
    last_crawled_at: datetime | None = None
    next_crawl_scheduled_at: datetime
    last_crawl_succeeded: bool = False
    consecutive_failures: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer(
        "last_crawled_at",
        "next_crawl_scheduled_at",
        "created_at",
        "updated_at",
    )
    def serialize_datetimes(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

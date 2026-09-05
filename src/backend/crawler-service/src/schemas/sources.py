import uuid
from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    field_serializer,
)


class SourceCreate(BaseModel):
    url: HttpUrl
    title: str | None = None
    description: str | None = None
    favicon: str | None = None
    enrich_with_ai: bool = False


class SourcePatchRequest(BaseModel):
    url: HttpUrl | None = None
    title: str | None = None
    description: str | None = None
    favicon: str | None = None
    enrich_with_ai: bool | None = None


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
    title: str | None = None
    description: str | None = None
    favicon: str | None = None
    website_url: str | None = None
    last_crawled_at: datetime | None = None
    next_crawl_scheduled_at: datetime
    last_crawl_succeeded: bool = False
    consecutive_failures: int = 0
    enrich_with_ai: bool = False
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

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    field_serializer,
)


class FeedCreate(BaseModel):
    url: HttpUrl
    title: str | None = None
    description: str | None = None
    favicon: str | None = None


class FeedPatchRequest(BaseModel):
    url: HttpUrl | None = None
    title: str | None = None
    description: str | None = None
    favicon: str | None = None


class ExploreRequest(BaseModel):
    url: HttpUrl


class ExploreResult(BaseModel):
    url: str
    title: str | None = None
    content_type: str | None = None
    favicon: str | None = None
    description: str | None = None


class FeedResponse(BaseModel):
    feed_id: uuid.UUID
    user_id: uuid.UUID
    url: str
    title: str | None
    description: str | None
    favicon: str | None
    website_url: str | None
    last_crawled_at: datetime | None
    next_crawl_scheduled_at: datetime
    last_crawl_succeeded: bool
    consecutive_failures: int
    health_score: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer(
        "last_crawled_at",
        "next_crawl_scheduled_at",
        "created_at",
        "updated_at",
    )
    def serialize_datetimes(
        self, value: datetime | None
    ) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class EventTrace(BaseModel):
    trace_id: str
    span_id: str


class EventEnvelope(BaseModel):
    event_id: uuid.UUID
    event_type: str
    schema_version: int = 1
    occurred_at: datetime
    producer: str
    correlation_id: uuid.UUID
    partition_key: str
    trace: EventTrace


class FeedRawFetchedPayload(BaseModel):
    feed_id: uuid.UUID
    feed_url: str
    source_title: str | None = None
    raw_xml: str


class FeedRawFetchedEvent(EventEnvelope):
    payload: FeedRawFetchedPayload


class FeedFetchFailedPayload(BaseModel):
    feed_id: uuid.UUID
    feed_url: str
    error_code: Literal[
        "TIMEOUT",
        "NETWORK_ERROR",
        "HTTP_ERROR",
        "INVALID_XML",
        "UNKNOWN_ERROR",
    ]
    error_message: str
    retry_count: int


class FeedFetchFailedEvent(EventEnvelope):
    payload: FeedFetchFailedPayload


class HealthResponse(BaseModel):
    status: str
    service: str

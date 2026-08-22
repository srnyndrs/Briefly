from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PostResponse(BaseModel):
    post_id: str
    source_id: str
    item_guid: str
    url: str
    title: str
    description: str | None = None
    category: str | None = None
    content: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    crawled_at: datetime | None = None
    parsed_at: datetime
    image_url: str | None = None
    language: str | None = None
    keywords: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("published_at", "crawled_at", "parsed_at")
    def serialize_datetime(
        self, value: datetime | None
    ) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class PostCountResponse(BaseModel):
    count: int

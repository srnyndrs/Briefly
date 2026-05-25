from datetime import datetime, timezone

from pydantic import BaseModel, field_serializer


class ArticleResponse(BaseModel):
    id: str
    feed_id: str
    item_guid: str
    url: str
    title: str
    description: str | None
    category: str | None
    content: str | None
    author: str | None
    published_at: datetime | None
    crawled_at: datetime | None
    parsed_at: datetime
    image_url: str | None
    language: str | None
    keywords: list[str]

    model_config = {"from_attributes": True}

    @field_serializer("published_at", "crawled_at", "parsed_at")
    def serialize_datetime(
        self, value: datetime | None
    ) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class ArticleCountResponse(BaseModel):
    count: int

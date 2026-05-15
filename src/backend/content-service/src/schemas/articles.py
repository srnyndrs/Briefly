from datetime import datetime

from pydantic import BaseModel


class ArticleResponse(BaseModel):
    id: str
    feed_id: str
    item_guid: str
    url: str
    title: str
    description: str | None
    content: str | None
    author: str | None
    published_at: datetime | None
    crawled_at: datetime | None
    parsed_at: datetime
    image_url: str | None
    language: str | None
    categories: list[str]

    model_config = {"from_attributes": True}


class ArticleCountResponse(BaseModel):
    count: int

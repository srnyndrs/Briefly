from datetime import datetime, timezone
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: UUID
    post_revision: int = Field(gt=0)
    source_id: UUID
    source_title: str
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

    @field_serializer("published_at", "crawled_at", "parsed_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value.isoformat()


class PostCountResponse(BaseModel):
    count: int


class PostPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    content: str | None = None
    author: str | None = None
    language: str | None = Field(default=None, max_length=35)
    keywords: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    image_url: str | None = None
    category: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value: object) -> object:
        if value is None:
            raise ValueError("title must not be null")
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_changes(self) -> "PostPatchRequest":
        if not self.model_fields_set:
            raise ValueError("At least one editable field is required")
        return self


class PostPatchResponse(PostResponse):
    publication_status: str

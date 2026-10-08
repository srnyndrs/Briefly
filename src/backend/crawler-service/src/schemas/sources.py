from datetime import datetime, timezone
from uuid import UUID

import langcodes
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_serializer,
    field_validator,
)


def normalize_source_language(value: str | None) -> str | None:
    if value is None or not (candidate := value.strip()):
        return None

    try:
        language = langcodes.get(candidate.replace("_", "-"))
    except ValueError:
        return None

    primary = language.language
    if not language.is_valid() or primary not in langcodes.LANGUAGE_ALPHA3:
        return None
    return primary


def _validated_language(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = normalize_source_language(value)
    if normalized is None:
        raise ValueError("A valid language tag is required")
    return normalized


class SourceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    favicon: HttpUrl | None = Field(default=None, max_length=2048)
    site_url: HttpUrl | None = Field(default=None, max_length=2048)
    site_name: str | None = Field(default=None, max_length=255)
    language: str | None = Field(default=None, max_length=35)
    submitted_by_user_id: UUID | None = None

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str | None) -> str | None:
        return _validated_language(value)


class SourcePatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    favicon: HttpUrl | None = Field(default=None, max_length=2048)
    site_url: HttpUrl | None = Field(default=None, max_length=2048)
    site_name: str | None = Field(default=None, max_length=255)
    language: str | None = Field(default=None, max_length=35)
    verified: bool | None = None

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str | None) -> str | None:
        return _validated_language(value)

    @field_validator("url", "title", "verified")
    @classmethod
    def reject_null(
        cls, value: HttpUrl | str | bool | None
    ) -> HttpUrl | str | bool:
        if value is None:
            raise ValueError("URL, title, and verified must not be null")
        return value


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_id: UUID
    url: str
    title: str
    description: str | None = None
    favicon: str | None = None
    site_url: str | None = None
    site_name: str | None = None
    language: str | None = None
    verified: bool = False
    last_crawled_at: datetime | None = None
    next_crawl_scheduled_at: datetime
    last_crawl_succeeded: bool = False
    consecutive_failures: int = 0
    created_at: datetime
    updated_at: datetime

    @field_serializer(
        "last_crawled_at",
        "next_crawl_scheduled_at",
        "created_at",
        "updated_at",
    )
    def serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class SourceDiscoverRequest(BaseModel):
    url: str = Field(min_length=1)


class SourceDiscoverResponse(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    content_type: str | None = None
    favicon: str | None = None
    site_url: str | None = None
    site_name: str | None = None
    language: str | None = None

    @field_validator("url")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "title",
        "description",
        "content_type",
        "favicon",
        "site_url",
        "site_name",
        "language",
    )
    @classmethod
    def normalize_discovered_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str | None) -> str | None:
        return normalize_source_language(value)

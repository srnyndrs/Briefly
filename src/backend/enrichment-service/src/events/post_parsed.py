"""Validated ``post.parsed.v1`` event contract."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParsedPostPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    post_id: UUID
    source_id: UUID
    post_revision: int = Field(gt=0, strict=True)
    item_guid: str
    url: str
    title: str
    description: str | None = None
    content: str | None = None
    language: str | None = None

    @field_validator("item_guid", "url")
    @classmethod
    def require_nonblank_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized


class ParsedPostEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_type: Literal["post.parsed.v1"]
    correlation_id: str = Field(min_length=1)
    payload: ParsedPostPayload

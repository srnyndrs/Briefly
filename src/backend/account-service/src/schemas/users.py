from datetime import datetime, timezone
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_serializer,
    field_validator,
)


class UserResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    display_name: str | None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class AccountPatchRequest(BaseModel):
    display_name: str | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("display_name must not be blank")
        if len(trimmed) > 80:
            raise ValueError(
                "display_name must be at most 80 characters"
            )
        return trimmed


class PreferencesUpdateRequest(BaseModel):
    muted_keywords: list[str] = Field(default_factory=list)
    muted_categories: list[str] = Field(default_factory=list)
    blocked_source_ids: list[UUID] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class PreferencesPatchRequest(BaseModel):
    muted_keywords: list[str] | None = None
    muted_categories: list[str] | None = None
    blocked_source_ids: list[UUID] | None = None
    languages: list[str] | None = None


class PreferencesResponse(BaseModel):
    user_id: UUID
    muted_keywords: list[str]
    muted_categories: list[str]
    blocked_source_ids: list[UUID]
    languages: list[str]
    updated_at: datetime

    @field_serializer("updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class SubscriptionCreateRequest(BaseModel):
    source_id: UUID


class SubscriptionResponse(BaseModel):
    user_id: UUID
    source_id: UUID
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

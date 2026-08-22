from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_serializer


class UserResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    status: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


class ProfileResponse(BaseModel):
    user_id: UUID
    display_name: str | None
    bio: str | None
    avatar_url: str | None
    updated_at: datetime

    @field_serializer("updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class PreferencesUpdateRequest(BaseModel):
    muted_keywords: list[str] = Field(default_factory=list)
    muted_categories: list[str] = Field(default_factory=list)
    blocked_source_ids: list[UUID] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    category_interests: list[str] = Field(default_factory=list)


class PreferencesPatchRequest(BaseModel):
    muted_keywords: list[str] | None = None
    muted_categories: list[str] | None = None
    blocked_source_ids: list[UUID] | None = None
    languages: list[str] | None = None
    category_interests: list[str] | None = None


class PreferencesResponse(BaseModel):
    user_id: UUID
    muted_keywords: list[str]
    muted_categories: list[str]
    blocked_source_ids: list[UUID]
    languages: list[str]
    category_interests: list[str]
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

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    status: str
    created_at: datetime


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


class PreferencesUpdateRequest(BaseModel):
    preferred_categories: list[str] = Field(default_factory=list)
    preferred_languages: list[str] = Field(default_factory=list)
    excluded_languages: list[str] = Field(default_factory=list)
    blocked_source_ids: list[UUID] = Field(default_factory=list)


class PreferencesPatchRequest(BaseModel):
    preferred_categories: list[str] | None = None
    preferred_languages: list[str] | None = None
    excluded_languages: list[str] | None = None
    blocked_source_ids: list[UUID] | None = None


class PreferencesResponse(BaseModel):
    user_id: UUID
    preferred_categories: list[str]
    preferred_languages: list[str]
    excluded_languages: list[str]
    blocked_source_ids: list[UUID]
    updated_at: datetime


class SubscriptionCreateRequest(BaseModel):
    source_id: UUID


class SubscriptionResponse(BaseModel):
    user_id: UUID
    source_id: UUID
    created_at: datetime

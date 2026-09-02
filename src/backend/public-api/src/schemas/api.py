from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_serializer


class HealthResponse(BaseModel):
    status: str
    service: str


class AuthContext(BaseModel):
    user_id: UUID
    token_type: str
    token_version: int
    scopes: list[str] = Field(default_factory=list)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
    reason: str = "logout"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=8, max_length=256)


class PasswordResetRequestResponse(BaseModel):
    status: str = "accepted"
    reset_token: str | None = None


class StatusResponse(BaseModel):
    status: str


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


class ProfilePatchRequest(BaseModel):
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


class PreferencesPatchRequest(BaseModel):
    muted_keywords: list[str] | None = None
    muted_categories: list[str] | None = None
    blocked_source_ids: list[UUID] | None = None
    languages: list[str] | None = None
    category_interests: list[str] | None = None


class PreferencesResponse(BaseModel):
    user_id: UUID
    muted_keywords: list[str] = Field(default_factory=list)
    muted_categories: list[str] = Field(default_factory=list)
    blocked_source_ids: list[UUID] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    category_interests: list[str] = Field(default_factory=list)
    updated_at: datetime

    @field_serializer("updated_at")
    def serialize_updated_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class MeDetailsResponse(UserResponse):
    profile: ProfileResponse | None = None
    preferences: PreferencesResponse | None = None


class SourceCreateRequest(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    favicon: str | None = None


class SourceDiscoverRequest(BaseModel):
    url: str


class SourceDiscoverResult(BaseModel):
    url: str
    title: str | None = None
    content_type: str | None = None
    favicon: str | None = None
    description: str | None = None


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


class SourcePatchRequest(BaseModel):
    url: str | None = None
    title: str | None = None
    description: str | None = None
    favicon: str | None = None


class SourceResponse(BaseModel):
    source_id: UUID
    url: str
    title: str | None
    description: str | None
    favicon: str | None
    website_url: str | None
    last_crawled_at: datetime | None
    next_crawl_scheduled_at: datetime
    last_crawl_succeeded: bool
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime
    is_subscribed: bool = False

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


class PostCountResponse(BaseModel):
    count: int


class AdminPostResponse(BaseModel):
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
    parsed_at: datetime | None = None
    image_url: str | None = None
    language: str | None = None
    keywords: list[str] = Field(default_factory=list)


class PostResponse(BaseModel):
    post_id: UUID
    source_id: UUID | None = None
    title: str
    source_title: str | None = None
    description: str | None = None
    canonical_url: str | None = None
    language: str | None = None
    category: str | None = None
    image_ref: str | None = None
    published_at: datetime | None = None
    has_content: bool = False
    content: str | None = None

    @field_serializer("published_at")
    def serialize_published_at(
        self, value: datetime | None
    ) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class FeedResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int = 1
    page_count: int = 1
    page_size: int = 20

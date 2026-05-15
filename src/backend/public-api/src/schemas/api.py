from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class AuthContext(BaseModel):
    user_id: UUID
    token_type: str
    token_version: int
    scopes: list[str] = Field(default_factory=list)


class RegisterRequest(BaseModel):
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


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


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


class PreferencesResponse(BaseModel):
    user_id: UUID
    preferred_categories: list[str] = Field(default_factory=list)
    preferred_languages: list[str] = Field(default_factory=list)
    excluded_languages: list[str] = Field(default_factory=list)
    blocked_source_ids: list[UUID] = Field(default_factory=list)
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


class SourceCreateRequest(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    favicon: str | None = None


class SourceExploreRequest(BaseModel):
    url: str


class SourceExploreResult(BaseModel):
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


class SourcePatchRequest(BaseModel):
    url: str | None = None
    title: str | None = None
    description: str | None = None
    favicon: str | None = None


class SourceResponse(BaseModel):
    feed_id: UUID
    user_id: UUID
    url: str
    title: str | None
    description: str | None
    favicon: str | None
    last_crawled_at: datetime | None
    next_crawl_scheduled_at: datetime
    last_crawl_succeeded: bool
    consecutive_failures: int
    health_score: float
    created_at: datetime
    updated_at: datetime


class ArticleCountResponse(BaseModel):
    count: int


class AdminArticleResponse(BaseModel):
    id: str
    feed_id: str
    item_guid: str
    url: str
    title: str
    description: str | None = None
    content: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    crawled_at: datetime | None = None
    parsed_at: datetime | None = None
    image_url: str | None = None
    language: str | None = None
    categories: list[str] = Field(default_factory=list)


class FeedItemResponse(BaseModel):
    article_id: UUID
    source_id: UUID | None = None
    title: str
    canonical_url: str | None = None
    language: str | None = None
    categories: list[str] = Field(default_factory=list)
    content_ref: str | None = None
    image_ref: str | None = None
    sentiment: str | None = None
    topics: list[str] = Field(default_factory=list)
    published_at: datetime | None = None


class FeedResponse(BaseModel):
    items: list[FeedItemResponse]
    total: int


class ArticleResponse(FeedItemResponse):
    content: str | None = None
    cluster_id: str | None = None
    model_version: str | None = None

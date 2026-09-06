from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.models.read_models import (
    PostProjection,
    UserPreferencesProjection,
)


@dataclass(frozen=True)
class PostDTO:
    post_id: str
    title: str
    source_id: str | None = None
    source_title: str | None = None
    description: str | None = None
    canonical_url: str | None = None
    language: str | None = None
    category: str | None = None
    keywords: list[str] = field(default_factory=list)
    content: str | None = None
    image_ref: str | None = None
    sentiment: str | None = None
    topics: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def rank_published_at(self) -> datetime:
        return self.published_at or datetime.min.replace(tzinfo=UTC)

    @property
    def rank_updated_at(self) -> datetime:
        return self.updated_at or datetime.min.replace(tzinfo=UTC)


@dataclass(frozen=True)
class UserPreferencesDTO:
    muted_keywords: list[str] = field(default_factory=list)
    muted_categories: list[str] = field(default_factory=list)
    blocked_source_ids: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    category_interests: list[str] = field(default_factory=list)

    @property
    def has_category_interests(self) -> bool:
        return bool(self.category_interests)


def post_projection_to_dto(model: PostProjection) -> PostDTO:
    return PostDTO(
        post_id=model.post_id,
        source_id=model.source_id,
        source_title=model.source_title,
        title=model.title,
        description=model.description,
        canonical_url=model.canonical_url,
        language=model.language,
        category=model.category,
        keywords=model.keywords or [],
        content=model.content,
        image_ref=model.image_ref,
        sentiment=model.sentiment,
        topics=model.topics or [],
        published_at=model.published_at,
        updated_at=model.updated_at,
    )


def user_preferences_projection_to_dto(
    model: UserPreferencesProjection | None,
) -> UserPreferencesDTO:
    if model is None:
        return UserPreferencesDTO()
    return UserPreferencesDTO(
        muted_keywords=model.muted_keywords or [],
        muted_categories=model.muted_categories or [],
        blocked_source_ids=model.blocked_source_ids or [],
        languages=model.languages or [],
        category_interests=model.category_interests or [],
    )

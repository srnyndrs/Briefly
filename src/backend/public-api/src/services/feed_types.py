from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class PostEntity:
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
class UserPreferencesVO:
    muted_keywords: list[str] = field(default_factory=list)
    muted_categories: list[str] = field(default_factory=list)
    blocked_source_ids: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    category_interests: list[str] = field(default_factory=list)

    @property
    def has_category_interests(self) -> bool:
        return bool(self.category_interests)

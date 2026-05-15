from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class ArticleEntity:
    article_id: str
    source_id: str | None
    title: str
    canonical_url: str | None
    language: str | None
    categories: list[str] = field(default_factory=list)
    content: str | None = None
    content_ref: str | None = None
    image_ref: str | None = None
    sentiment: str | None = None
    topics: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    updated_at: datetime | None = None
    cluster_id: str | None = None
    model_version: str | None = None

    @property
    def rank_published_at(self) -> datetime:
        return self.published_at or datetime.min.replace(tzinfo=UTC)

    @property
    def rank_updated_at(self) -> datetime:
        return self.updated_at or datetime.min.replace(tzinfo=UTC)


@dataclass(frozen=True)
class UserPreferencesVO:
    preferred_categories: list[str] = field(default_factory=list)
    preferred_languages: list[str] = field(default_factory=list)
    excluded_languages: list[str] = field(default_factory=list)
    blocked_source_ids: list[str] = field(default_factory=list)

    @property
    def has_preferred_categories(self) -> bool:
        return bool(self.preferred_categories)

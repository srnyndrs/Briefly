from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PostDTO:
    post_id: str
    source_id: str | None
    source_title: str | None
    title: str
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


@dataclass(frozen=True)
class UserPreferencesDTO:
    muted_keywords: list[str] = field(default_factory=list)
    muted_categories: list[str] = field(default_factory=list)
    blocked_source_ids: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    category_interests: list[str] = field(default_factory=list)

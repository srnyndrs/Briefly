from dataclasses import dataclass, field
from datetime import datetime

from src.services.feed_dtos import UserPreferencesDTO


@dataclass(frozen=True)
class PersonalizationQueryOverrides:
    include_categories: list[str] | None = None
    include_languages: list[str] | None = None
    include_source_ids: list[str] | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    sort: str | None = None


@dataclass(frozen=True)
class EffectivePersonalizationContext:
    muted_keywords: list[str] = field(default_factory=list)
    muted_categories: list[str] = field(default_factory=list)
    blocked_source_ids: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    category_interests: list[str] = field(default_factory=list)
    include_categories: list[str] | None = None
    include_languages: list[str] | None = None
    include_source_ids: list[str] | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    sort: str | None = None


class PersonalizationMergeService:
    def merge(
        self,
        *,
        profile: UserPreferencesDTO,
        use_profile: bool,
        overrides: PersonalizationQueryOverrides,
    ) -> EffectivePersonalizationContext:
        if use_profile:
            muted_keywords = list(profile.muted_keywords)
            muted_categories = list(profile.muted_categories)
            blocked_source_ids = list(profile.blocked_source_ids)
            languages = list(profile.languages)
            category_interests = list(profile.category_interests)
        else:
            muted_keywords = []
            muted_categories = []
            blocked_source_ids = []
            languages = []
            category_interests = []

        return EffectivePersonalizationContext(
            muted_keywords=muted_keywords,
            muted_categories=muted_categories,
            blocked_source_ids=blocked_source_ids,
            languages=languages,
            category_interests=category_interests,
            include_categories=overrides.include_categories,
            include_languages=overrides.include_languages,
            include_source_ids=overrides.include_source_ids,
            published_from=overrides.published_from,
            published_to=overrides.published_to,
            sort=overrides.sort,
        )


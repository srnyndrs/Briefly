from dataclasses import dataclass, field
from datetime import datetime

from src.services.feed_dtos import UserPreferencesDTO


@dataclass(frozen=True)
class PersonalizationQueryOverrides:
    include_categories: list[str] | None = None
    include_languages: list[str] | None = None
    exclude_languages: list[str] | None = None
    include_source_ids: list[str] | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    sort: str | None = None


@dataclass(frozen=True)
class EffectivePersonalizationContext:
    preferred_categories: list[str] = field(default_factory=list)
    preferred_languages: list[str] = field(default_factory=list)
    excluded_languages: list[str] = field(default_factory=list)
    blocked_source_ids: list[str] = field(default_factory=list)
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
            preferred_categories = list(
                profile.preferred_categories
            )
            preferred_languages = list(profile.preferred_languages)
            excluded_languages = list(profile.excluded_languages)
            blocked_source_ids = list(profile.blocked_source_ids)
        else:
            preferred_categories = []
            preferred_languages = []
            excluded_languages = []
            blocked_source_ids = []

        if overrides.exclude_languages is not None:
            excluded_languages = list(overrides.exclude_languages)

        return EffectivePersonalizationContext(
            preferred_categories=preferred_categories,
            preferred_languages=preferred_languages,
            excluded_languages=excluded_languages,
            blocked_source_ids=blocked_source_ids,
            include_categories=overrides.include_categories,
            include_languages=overrides.include_languages,
            include_source_ids=overrides.include_source_ids,
            published_from=overrides.published_from,
            published_to=overrides.published_to,
            sort=overrides.sort,
        )

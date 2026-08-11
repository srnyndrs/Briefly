from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.repositories.feed_repository import (
    ArticleRepository,
    UserPreferencesRepository,
)
from src.services.feed_dtos import FeedItemDTO, UserPreferencesDTO
from src.services.feed_mappers import (
    entity_to_feed_item_dto,
    user_preferences_dto_to_vo,
)
from src.services.feed_scoring import FeedScoringService
from src.services.personalization import (
    PersonalizationMergeService,
    PersonalizationQueryOverrides,
)


@dataclass(frozen=True)
class ListFeedInput:
    user_id: UUID
    limit: int
    offset: int
    use_profile: bool = True
    categories: list[str] | None = None
    languages: list[str] | None = None
    exclude_languages: list[str] | None = None
    source_ids: list[str] | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    sort: str | None = None


@dataclass(frozen=True)
class ListFeedOutput:
    items: list[FeedItemDTO]
    total: int


@dataclass(frozen=True)
class SearchFeedInput:
    user_id: UUID
    q: str
    limit: int
    offset: int
    use_profile: bool = True
    categories: list[str] | None = None
    languages: list[str] | None = None
    exclude_languages: list[str] | None = None
    source_ids: list[str] | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    sort: str | None = None


@dataclass(frozen=True)
class SearchFeedOutput:
    items: list[FeedItemDTO]
    total: int


@dataclass(frozen=True)
class GetArticleInput:
    article_id: UUID


class FeedService:
    def __init__(
        self,
        article_repository: ArticleRepository,
        preferences_repository: UserPreferencesRepository,
        scoring_service: FeedScoringService | None = None,
        merge_service: PersonalizationMergeService | None = None,
    ) -> None:
        self._article_repository = article_repository
        self._preferences_repository = preferences_repository
        self._scoring_service = (
            scoring_service or FeedScoringService()
        )
        self._merge_service = (
            merge_service or PersonalizationMergeService()
        )

    def list_feed(self, data: ListFeedInput) -> ListFeedOutput:
        prefs_dto: UserPreferencesDTO = (
            self._preferences_repository.get_preferences(
                data.user_id
            )
        )
        context = self._merge_service.merge(
            profile=prefs_dto,
            use_profile=data.use_profile,
            overrides=PersonalizationQueryOverrides(
                include_categories=data.categories,
                include_languages=data.languages,
                exclude_languages=data.exclude_languages,
                include_source_ids=data.source_ids,
                published_from=data.published_from,
                published_to=data.published_to,
                sort=data.sort,
            ),
        )

        prefs_vo = user_preferences_dto_to_vo(
            UserPreferencesDTO(
                preferred_categories=context.preferred_categories,
                preferred_languages=context.preferred_languages,
                excluded_languages=context.excluded_languages,
                blocked_source_ids=context.blocked_source_ids,
            )
        )
        candidates, total = (
            self._article_repository.list_feed_candidates(
                user_id=data.user_id,
                excluded_languages=context.excluded_languages,
                blocked_source_ids=context.blocked_source_ids,
                include_languages=context.include_languages,
                include_source_ids=context.include_source_ids,
                include_categories=context.include_categories,
                published_from=context.published_from,
                published_to=context.published_to,
                sort=context.sort,
                limit=data.limit,
                offset=data.offset,
            )
        )
        ranked = self._scoring_service.rank(
            articles=candidates,
            preferences=prefs_vo,
            limit=data.limit,
        )
        return ListFeedOutput(
            items=[
                entity_to_feed_item_dto(article)
                for article in ranked
            ],
            total=total,
        )

    def search_feed(
        self, data: SearchFeedInput
    ) -> SearchFeedOutput:
        prefs = self._preferences_repository.get_preferences(
            data.user_id
        )
        context = self._merge_service.merge(
            profile=prefs,
            use_profile=data.use_profile,
            overrides=PersonalizationQueryOverrides(
                include_categories=data.categories,
                include_languages=data.languages,
                exclude_languages=data.exclude_languages,
                include_source_ids=data.source_ids,
                published_from=data.published_from,
                published_to=data.published_to,
                sort=data.sort,
            ),
        )
        items, total = self._article_repository.search_feed(
            user_id=data.user_id,
            q=data.q,
            excluded_languages=context.excluded_languages,
            blocked_source_ids=context.blocked_source_ids,
            include_languages=context.include_languages,
            include_source_ids=context.include_source_ids,
            include_categories=context.include_categories,
            published_from=context.published_from,
            published_to=context.published_to,
            sort=context.sort,
            limit=data.limit,
            offset=data.offset,
        )
        return SearchFeedOutput(
            items=[
                entity_to_feed_item_dto(article)
                for article in items
            ],
            total=total,
        )

    def get_article(
        self, data: GetArticleInput
    ) -> FeedItemDTO | None:
        entity = self._article_repository.get_article(
            data.article_id
        )
        if entity is None:
            return None
        return entity_to_feed_item_dto(entity)

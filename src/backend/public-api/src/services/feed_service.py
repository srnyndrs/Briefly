from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.repositories.feed_repository import (
    PostRepository,
    UserPreferencesRepository,
)
from src.services.feed_models import PostDTO, UserPreferencesDTO
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
    source_ids: list[str] | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    sort: str | None = None


@dataclass(frozen=True)
class ListFeedOutput:
    items: list[PostDTO]
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
    source_ids: list[str] | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    sort: str | None = None


@dataclass(frozen=True)
class SearchFeedOutput:
    items: list[PostDTO]
    total: int


@dataclass(frozen=True)
class GetPostInput:
    post_id: UUID


class FeedService:
    def __init__(
        self,
        post_repository: PostRepository,
        preferences_repository: UserPreferencesRepository,
        scoring_service: FeedScoringService | None = None,
        merge_service: PersonalizationMergeService | None = None,
    ) -> None:
        self._post_repository = post_repository
        self._preferences_repository = preferences_repository
        self._scoring_service = scoring_service or FeedScoringService()
        self._merge_service = (
            merge_service or PersonalizationMergeService()
        )

    def list_feed(self, data: ListFeedInput) -> ListFeedOutput:
        prefs_dto: UserPreferencesDTO = (
            self._preferences_repository.get_preferences(data.user_id)
        )
        context = self._merge_service.merge(
            profile=prefs_dto,
            use_profile=data.use_profile,
            overrides=PersonalizationQueryOverrides(
                include_categories=data.categories,
                include_languages=data.languages,
                include_source_ids=data.source_ids,
                published_from=data.published_from,
                published_to=data.published_to,
                sort=data.sort,
            ),
        )

        candidates, total = self._post_repository.list_feed_candidates(
            user_id=data.user_id,
            languages=context.languages,
            muted_keywords=context.muted_keywords,
            muted_categories=context.muted_categories,
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
        ranked = self._scoring_service.rank(
            articles=candidates,
            preferences=prefs_dto,
            limit=data.limit,
        )
        return ListFeedOutput(
            items=ranked,
            total=total,
        )

    def search_feed(self, data: SearchFeedInput) -> SearchFeedOutput:
        prefs = self._preferences_repository.get_preferences(
            data.user_id
        )
        context = self._merge_service.merge(
            profile=prefs,
            use_profile=data.use_profile,
            overrides=PersonalizationQueryOverrides(
                include_categories=data.categories,
                include_languages=data.languages,
                include_source_ids=data.source_ids,
                published_from=data.published_from,
                published_to=data.published_to,
                sort=data.sort,
            ),
        )
        items, total = self._post_repository.search_feed(
            user_id=data.user_id,
            q=data.q,
            languages=context.languages,
            muted_keywords=context.muted_keywords,
            muted_categories=context.muted_categories,
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
            items=items,
            total=total,
        )

    def get_post(self, data: GetPostInput) -> PostDTO | None:
        return self._post_repository.get_post(data.post_id)

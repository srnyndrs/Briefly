from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.adapters.service_clients import account_list_subscriptions
from src.repositories.feed_repository import (
    PostRepository,
    UserPreferencesRepository,
)
from src.services.feed_models import (
    EffectiveFeedQuery,
    FilterOptionsDTO,
    PostDTO,
)


@dataclass(frozen=True)
class PersonalFeedInput:
    user_id: UUID
    limit: int
    offset: int
    category: str | None = None
    include_filter_options: bool = False


@dataclass(frozen=True)
class ExploreFeedInput:
    user_id: UUID
    limit: int
    offset: int
    categories: list[str] | None = None
    languages: list[str] | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    sort: str | None = None
    include_filter_options: bool = False


@dataclass(frozen=True)
class FeedOutput:
    items: list[PostDTO]
    total: int
    filter_options: FilterOptionsDTO | None = None


@dataclass(frozen=True)
class AdminFeedInput:
    limit: int
    offset: int


@dataclass(frozen=True)
class GetPostInput:
    post_id: UUID


class FeedService:
    def __init__(
        self,
        post_repository: PostRepository,
        preferences_repository: UserPreferencesRepository,
    ) -> None:
        self._post_repository = post_repository
        self._preferences_repository = preferences_repository

    def get_personal_feed(self, data: PersonalFeedInput) -> FeedOutput:
        preferences = self._preferences_repository.get_preferences(
            data.user_id
        )
        subscriptions = account_list_subscriptions(str(data.user_id))
        source_ids = [str(item["source_id"]) for item in subscriptions]
        if not source_ids:
            return FeedOutput(
                items=[],
                total=0,
                filter_options=(
                    FilterOptionsDTO(categories=[], languages=[])
                    if data.include_filter_options
                    else None
                ),
            )

        query = EffectiveFeedQuery(
            blocked_source_ids=preferences.blocked_source_ids,
            muted_keywords=preferences.muted_keywords,
            muted_categories=preferences.muted_categories,
            languages=preferences.languages,
            source_ids=source_ids,
            categories=[data.category] if data.category else None,
            limit=data.limit,
            offset=data.offset,
        )
        return self._execute(query, data.include_filter_options)

    def get_explore_feed(self, data: ExploreFeedInput) -> FeedOutput:
        preferences = self._preferences_repository.get_preferences(
            data.user_id
        )
        query = EffectiveFeedQuery(
            blocked_source_ids=preferences.blocked_source_ids,
            muted_keywords=preferences.muted_keywords,
            muted_categories=preferences.muted_categories,
            languages=data.languages,
            categories=data.categories,
            published_from=data.published_from,
            published_to=data.published_to,
            sort=data.sort or "freshness",
            limit=data.limit,
            offset=data.offset,
        )
        return self._execute(query, data.include_filter_options)

    def get_admin_feed(self, data: AdminFeedInput) -> FeedOutput:
        return self._execute(
            EffectiveFeedQuery(limit=data.limit, offset=data.offset),
            False,
        )

    def _execute(
        self, query: EffectiveFeedQuery, include_options: bool
    ) -> FeedOutput:
        items, total = self._post_repository.list_candidates(query)
        options = (
            self._post_repository.list_filter_options(query)
            if include_options
            else None
        )
        return FeedOutput(
            items=items,
            total=total,
            filter_options=options,
        )

    def get_post(self, data: GetPostInput) -> PostDTO | None:
        return self._post_repository.get_post(data.post_id)

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from src.models.read_models import (
    PostProjection,
    UserPreferencesProjection,
)
from src.services.feed_models import (
    EffectiveFeedQuery,
    FilterOptionsDTO,
    PostDTO,
    UserPreferencesDTO,
    post_projection_to_dto,
    user_preferences_projection_to_dto,
)


class PostRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _apply_common_filters(
        self,
        query,
        *,
        languages: Sequence[str] | None,
        muted_keywords: Sequence[str] | None,
        muted_categories: Sequence[str] | None,
        blocked_source_ids: Sequence[str] | None,
        include_languages: Sequence[str] | None = None,
        include_source_ids: Sequence[str] | None = None,
        include_categories: Sequence[str] | None = None,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
    ):
        normalized_muted_categories = [
            category.lower().strip()
            for category in muted_categories or []
            if category.strip()
        ]

        # 1. Hard Block: Blocked Sources
        if blocked_source_ids:
            query = query.where(
                or_(
                    PostProjection.source_id.is_(None),
                    PostProjection.source_id.not_in(blocked_source_ids),
                )
            )

        # 2. Hard Block: Muted Categories
        if normalized_muted_categories:
            query = query.where(
                or_(
                    PostProjection.category.is_(None),
                    func.lower(
                        func.trim(PostProjection.category)
                    ).not_in(normalized_muted_categories),
                )
            )

        # 3. Hard Block: Muted Keywords
        if muted_keywords:
            normalized_muted = [
                k.lower().strip() for k in muted_keywords if k.strip()
            ]
            if normalized_muted:
                if (
                    self._db.bind
                    and self._db.bind.dialect.name == "sqlite"
                ):
                    for kw in normalized_muted:
                        query = query.where(
                            ~cast(
                                PostProjection.keywords, String
                            ).ilike(f"%{kw}%")
                        )
                else:
                    query = query.where(
                        ~PostProjection.keywords.op("&&")(
                            normalized_muted
                        )
                    )

        # 4. Strict Language Allowlist
        effective_languages = (
            include_languages
            if include_languages is not None
            else languages
        )
        if effective_languages:
            query = query.where(
                PostProjection.language.in_(effective_languages)
            )

        # 5. Ad-hoc query overrides
        if include_source_ids:
            query = query.where(
                PostProjection.source_id.in_(include_source_ids)
            )

        normalized_include_categories = [
            category.lower().strip()
            for category in include_categories or []
            if category.strip()
        ]
        if normalized_include_categories:
            query = query.where(
                func.lower(func.trim(PostProjection.category)).in_(
                    normalized_include_categories
                )
            )

        # 6. Date Range Constraints
        if published_from is not None:
            query = query.where(
                PostProjection.published_at >= published_from
            )

        if published_to is not None:
            query = query.where(
                PostProjection.published_at <= published_to
            )

        return query

    def _order_by(self, sort: str | None):
        normalized = (sort or "freshness").lower()
        if normalized == "oldest":
            return (
                PostProjection.published_at.asc().nullslast(),
                PostProjection.updated_at.asc(),
                PostProjection.post_id.asc(),
            )
        return (
            PostProjection.published_at.desc().nullslast(),
            PostProjection.updated_at.desc(),
            PostProjection.post_id.desc(),
        )

    def list_candidates(
        self, query: EffectiveFeedQuery
    ) -> tuple[list[PostDTO], int]:
        statement = self._apply_query(select(PostProjection), query)
        total = (
            self._db.scalar(
                select(func.count()).select_from(statement.subquery())
            )
            or 0
        )
        rows = self._db.scalars(
            statement.order_by(*self._order_by(query.sort))
            .offset(query.offset)
            .limit(query.limit)
        ).all()
        return [post_projection_to_dto(row) for row in rows], total

    def list_filter_options(
        self, query: EffectiveFeedQuery
    ) -> FilterOptionsDTO:
        category_query = EffectiveFeedQuery(
            blocked_source_ids=query.blocked_source_ids,
            muted_keywords=query.muted_keywords,
            muted_categories=query.muted_categories,
            languages=query.languages,
            source_ids=query.source_ids,
            categories=None,
            published_from=query.published_from,
            published_to=query.published_to,
            sort=query.sort,
        )
        language_query = EffectiveFeedQuery(
            blocked_source_ids=query.blocked_source_ids,
            muted_keywords=query.muted_keywords,
            muted_categories=query.muted_categories,
            languages=None,
            source_ids=query.source_ids,
            categories=query.categories,
            published_from=query.published_from,
            published_to=query.published_to,
            sort=query.sort,
        )
        categories = self._db.scalars(
            self._apply_query(
                select(func.lower(func.trim(PostProjection.category))),
                category_query,
            )
            .where(
                PostProjection.category.is_not(None),
                func.trim(PostProjection.category) != "",
            )
            .distinct()
            .order_by(func.lower(func.trim(PostProjection.category)))
        ).all()
        languages = self._db.scalars(
            self._apply_query(
                select(PostProjection.language), language_query
            )
            .where(
                PostProjection.language.is_not(None),
                func.trim(PostProjection.language) != "",
            )
            .distinct()
            .order_by(PostProjection.language)
        ).all()
        return FilterOptionsDTO(
            categories=list(categories), languages=list(languages)
        )

    def _apply_query(self, statement, query: EffectiveFeedQuery):
        return self._apply_common_filters(
            statement,
            languages=query.languages,
            muted_keywords=query.muted_keywords,
            muted_categories=query.muted_categories,
            blocked_source_ids=query.blocked_source_ids,
            include_languages=None,
            include_source_ids=query.source_ids,
            include_categories=query.categories,
            published_from=query.published_from,
            published_to=query.published_to,
        )

    def get_post(self, post_id: UUID) -> PostDTO | None:
        model = self._db.get(PostProjection, str(post_id))
        if model is None:
            return None
        return post_projection_to_dto(model)


class UserPreferencesRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_user_id(self, user_id: UUID):
        return self._db.get(UserPreferencesProjection, str(user_id))

    def get_preferences(self, user_id: UUID) -> UserPreferencesDTO:
        model = self.get_by_user_id(user_id)
        return user_preferences_projection_to_dto(model)

from collections.abc import Sequence
from datetime import datetime
import re
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from src.models.read_models import (
    PostProjection,
    UserPreferencesProjection,
    post_search_document,
)
from src.services.feed_models import (
    EffectiveFeedQuery,
    FilterOptionsDTO,
    PostDTO,
    SourceOptionDTO,
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
        search_query: str | None = None,
    ):
        normalized_muted_categories = [
            category.lower().strip()
            for category in muted_categories or []
            if category.strip()
        ]

        # 1. Hard Block: Blocked Sources
        if blocked_source_ids:
            query = query.where(
                PostProjection.source_id.not_in(blocked_source_ids)
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

        if search_query:
            query = self._apply_search_filter(query, search_query)

        return query

    def _apply_search_filter(self, query, search_query: str):
        document = post_search_document(
            PostProjection.title,
            PostProjection.description,
            PostProjection.content,
        )
        if self._db.bind and self._db.bind.dialect.name == "postgresql":
            return query.where(
                document.op("@@")(
                    func.websearch_to_tsquery("simple", search_query)
                )
            )

        fields = (
            PostProjection.title,
            PostProjection.description,
            PostProjection.content,
        )
        terms = re.findall(r'"([^"]+)"|([^\s]+)', search_query)
        for phrase, word in terms:
            token = phrase or word
            is_negative = token.startswith("-")
            token = token[1:] if is_negative else token
            if not token or token.upper() == "OR":
                continue
            match = or_(
                *(
                    func.coalesce(field, "").ilike(f"%{token}%")
                    for field in fields
                )
            )
            query = query.where(~match if is_negative else match)
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
        if query.query and self._db.bind.dialect.name == "postgresql":
            document = post_search_document(
                PostProjection.title,
                PostProjection.description,
                PostProjection.content,
            )
            order_by = (
                func.ts_rank_cd(
                    document,
                    func.websearch_to_tsquery("simple", query.query),
                ).desc(),
                PostProjection.published_at.desc().nullslast(),
                PostProjection.post_id.asc(),
            )
        else:
            order_by = self._order_by(query.sort)
        rows = self._db.scalars(
            statement.order_by(*order_by)
            .offset(query.offset)
            .limit(query.limit)
        ).all()
        return [post_projection_to_dto(row) for row in rows], total

    def list_headlines(
        self, query: EffectiveFeedQuery, limit: int
    ) -> list[PostDTO]:
        statement = self._apply_query(select(PostProjection), query)
        rows = self._db.scalars(
            statement.order_by(*self._order_by("freshness")).limit(
                limit
            )
        ).all()
        return [post_projection_to_dto(row) for row in rows]

    def list_filter_options(
        self,
        query: EffectiveFeedQuery,
        *,
        include_sources: bool = False,
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
            query=query.query,
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
            query=query.query,
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
        sources = None
        if include_sources:
            source_query = EffectiveFeedQuery(
                blocked_source_ids=query.blocked_source_ids,
                muted_keywords=query.muted_keywords,
                muted_categories=query.muted_categories,
                languages=query.languages,
                source_ids=None,
                categories=query.categories,
                published_from=query.published_from,
                published_to=query.published_to,
                sort=query.sort,
                query=query.query,
            )
            normalized_title = func.lower(
                func.trim(PostProjection.source_title)
            ).label("source_title_order")
            source_rows = self._db.execute(
                self._apply_query(
                    select(
                        PostProjection.source_id,
                        PostProjection.source_title,
                        normalized_title,
                    ),
                    source_query,
                )
                .distinct()
                .order_by(normalized_title, PostProjection.source_id)
            ).all()
            sources = [
                SourceOptionDTO(source_id=source_id, title=source_title)
                for source_id, source_title, _ in source_rows
            ]

        return FilterOptionsDTO(
            categories=list(categories),
            languages=list(languages),
            sources=sources,
        )

    def list_personal_filter_options(
        self, query: EffectiveFeedQuery
    ) -> FilterOptionsDTO:
        category_query = self._without_category(query)
        normalized_category = func.lower(
            func.trim(PostProjection.category)
        ).label("category")
        category_count = func.count(PostProjection.post_id).label(
            "count"
        )
        category_rows = self._db.execute(
            self._apply_query(
                select(normalized_category, category_count),
                category_query,
            )
            .where(
                PostProjection.category.is_not(None),
                func.trim(PostProjection.category) != "",
            )
            .group_by(normalized_category)
            .order_by(category_count.desc(), normalized_category.asc())
        ).all()
        language_options = self.list_filter_options(query).languages
        return FilterOptionsDTO(
            categories=[category for category, _ in category_rows],
            languages=language_options,
        )

    @staticmethod
    def _without_category(
        query: EffectiveFeedQuery,
    ) -> EffectiveFeedQuery:
        return EffectiveFeedQuery(
            blocked_source_ids=query.blocked_source_ids,
            muted_keywords=query.muted_keywords,
            muted_categories=query.muted_categories,
            languages=query.languages,
            source_ids=query.source_ids,
            query=query.query,
            published_from=query.published_from,
            published_to=query.published_to,
            sort=query.sort,
            excluded_post_ids=query.excluded_post_ids,
            limit=query.limit,
            offset=query.offset,
        )

    def _apply_query(self, statement, query: EffectiveFeedQuery):
        statement = self._apply_common_filters(
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
            search_query=query.query,
        )
        if query.excluded_post_ids:
            statement = statement.where(
                PostProjection.post_id.not_in(query.excluded_post_ids)
            )
        return statement

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

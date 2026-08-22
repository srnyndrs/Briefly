from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from src.models.read_models import (
    ArticleProjection,
    UserPreferencesProjection,
)
from src.services.feed_dtos import UserPreferencesDTO
from src.services.feed_mappers import (
    article_projection_to_entity,
    user_preferences_projection_to_dto,
)


class ArticleRepository:
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
        # 1. Hard Block: Blocked Sources
        if blocked_source_ids:
            query = query.where(
                or_(
                    ArticleProjection.source_id.is_(None),
                    ArticleProjection.source_id.not_in(
                        blocked_source_ids
                    ),
                )
            )

        # 2. Hard Block: Muted Categories
        if muted_categories:
            query = query.where(
                or_(
                    ArticleProjection.category.is_(None),
                    ArticleProjection.category.not_in(
                        muted_categories
                    ),
                )
            )

        # 3. Hard Block: Muted Keywords
        if muted_keywords:
            normalized_muted = [
                k.lower().strip()
                for k in muted_keywords
                if k.strip()
            ]
            if normalized_muted:
                if (
                    self._db.bind
                    and self._db.bind.dialect.name == "sqlite"
                ):
                    for kw in normalized_muted:
                        query = query.where(
                            ~cast(
                                ArticleProjection.keywords, String
                            ).ilike(f"%{kw}%")
                        )
                else:
                    query = query.where(
                        ~ArticleProjection.keywords.op("&&")(
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
                ArticleProjection.language.in_(effective_languages)
            )

        # 5. Ad-hoc query overrides
        if include_source_ids:
            query = query.where(
                ArticleProjection.source_id.in_(include_source_ids)
            )

        if include_categories:
            if (
                self._db.bind
                and self._db.bind.dialect.name == "sqlite"
            ):
                query = query.where(
                    or_(
                        *[
                            cast(
                                ArticleProjection.keywords, String
                            ).ilike(f"%{c}%")
                            for c in include_categories
                        ]
                    )
                )
            else:
                query = query.where(
                    ArticleProjection.keywords.op("&&")(
                        list(include_categories)
                    )
                )

        # 6. Date Range Constraints
        if published_from is not None:
            query = query.where(
                ArticleProjection.published_at >= published_from
            )

        if published_to is not None:
            query = query.where(
                ArticleProjection.published_at <= published_to
            )

        return query

    def _order_by(self, sort: str | None):
        normalized = (sort or "freshness").lower()
        if normalized == "oldest":
            return (
                ArticleProjection.published_at.asc().nullslast(),
                ArticleProjection.updated_at.asc(),
                ArticleProjection.article_id.asc(),
            )
        return (
            ArticleProjection.published_at.desc().nullslast(),
            ArticleProjection.updated_at.desc(),
            ArticleProjection.article_id.desc(),
        )

    def list_feed_candidates(
        self,
        *,
        user_id: UUID,
        languages: Sequence[str] | None,
        muted_keywords: Sequence[str] | None,
        muted_categories: Sequence[str] | None,
        blocked_source_ids: Sequence[str] | None,
        include_languages: Sequence[str] | None,
        include_source_ids: Sequence[str] | None,
        include_categories: Sequence[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
        sort: str | None,
        limit: int,
        offset: int,
    ):
        _ = user_id
        query = select(ArticleProjection)
        query = self._apply_common_filters(
            query,
            languages=languages,
            muted_keywords=muted_keywords,
            muted_categories=muted_categories,
            blocked_source_ids=blocked_source_ids,
            include_languages=include_languages,
            include_source_ids=include_source_ids,
            include_categories=include_categories,
            published_from=published_from,
            published_to=published_to,
        )

        ordered = query.order_by(*self._order_by(sort))
        total = (
            self._db.scalar(
                select(func.count()).select_from(query.subquery())
            )
            or 0
        )
        rows = self._db.scalars(
            ordered.offset(offset).limit(limit)
        ).all()

        return [
            article_projection_to_entity(row) for row in rows
        ], total

    def search_feed(
        self,
        *,
        user_id: UUID,
        q: str,
        languages: Sequence[str] | None,
        muted_keywords: Sequence[str] | None,
        muted_categories: Sequence[str] | None,
        blocked_source_ids: Sequence[str] | None,
        include_languages: Sequence[str] | None,
        include_source_ids: Sequence[str] | None,
        include_categories: Sequence[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
        sort: str | None,
        limit: int,
        offset: int,
    ):
        _ = user_id
        query = select(ArticleProjection).where(
            or_(
                ArticleProjection.title.ilike(f"%{q}%"),
                ArticleProjection.canonical_url.ilike(f"%{q}%"),
            )
        )

        query = self._apply_common_filters(
            query,
            languages=languages,
            muted_keywords=muted_keywords,
            muted_categories=muted_categories,
            blocked_source_ids=blocked_source_ids,
            include_languages=include_languages,
            include_source_ids=include_source_ids,
            include_categories=include_categories,
            published_from=published_from,
            published_to=published_to,
        )

        ordered = query.order_by(*self._order_by(sort))
        total = (
            self._db.scalar(
                select(func.count()).select_from(query.subquery())
            )
            or 0
        )
        rows = self._db.scalars(
            ordered.offset(offset).limit(limit)
        ).all()

        return [
            article_projection_to_entity(row) for row in rows
        ], total

    def get_article(self, article_id: UUID):
        model = self._db.get(ArticleProjection, str(article_id))
        if model is None:
            return None
        return article_projection_to_entity(model)


class UserPreferencesRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_user_id(self, user_id: UUID):
        return self._db.get(UserPreferencesProjection, str(user_id))

    def get_preferences(self, user_id: UUID) -> UserPreferencesDTO:
        model = self.get_by_user_id(user_id)
        return user_preferences_projection_to_dto(model)

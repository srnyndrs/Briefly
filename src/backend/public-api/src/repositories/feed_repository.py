from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
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
        excluded_languages: Sequence[str],
        blocked_source_ids: Sequence[str],
        include_languages: Sequence[str] | None,
        include_source_ids: Sequence[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
    ):
        if excluded_languages:
            query = query.where(
                or_(
                    ArticleProjection.language.is_(None),
                    ArticleProjection.language.not_in(
                        excluded_languages
                    ),
                )
            )

        if blocked_source_ids:
            query = query.where(
                or_(
                    ArticleProjection.source_id.is_(None),
                    ArticleProjection.source_id.not_in(
                        blocked_source_ids
                    ),
                )
            )

        if include_languages:
            query = query.where(
                ArticleProjection.language.in_(include_languages)
            )

        if include_source_ids:
            query = query.where(
                ArticleProjection.source_id.in_(include_source_ids)
            )

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
            )
        return (
            ArticleProjection.published_at.desc().nullslast(),
            ArticleProjection.updated_at.desc(),
        )

    @staticmethod
    def _matches_categories(
        row: ArticleProjection,
        include_categories: Sequence[str] | None,
    ) -> bool:
        if not include_categories:
            return True

        wanted = {
            category.lower() for category in include_categories
        }
        existing = {
            category.lower() for category in (row.categories or [])
        }
        return bool(existing.intersection(wanted))

    def list_feed_candidates(
        self,
        *,
        user_id: UUID,
        excluded_languages: Sequence[str],
        blocked_source_ids: Sequence[str],
        include_languages: Sequence[str] | None,
        include_source_ids: Sequence[str] | None,
        include_categories: Sequence[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
        sort: str | None,
        limit: int,
        offset: int,
        expand_limit: bool,
    ):
        _ = user_id
        query = select(ArticleProjection)
        query = self._apply_common_filters(
            query,
            excluded_languages=excluded_languages,
            blocked_source_ids=blocked_source_ids,
            include_languages=include_languages,
            include_source_ids=include_source_ids,
            published_from=published_from,
            published_to=published_to,
        )

        ordered = query.order_by(*self._order_by(sort))
        read_limit = limit * 4 if expand_limit else limit

        if include_categories:
            all_rows = self._db.scalars(ordered).all()
            filtered_rows = [
                row
                for row in all_rows
                if self._matches_categories(row, include_categories)
            ]
            total = len(filtered_rows)
            rows = filtered_rows[offset : offset + read_limit]
        else:
            total = (
                self._db.scalar(
                    select(func.count()).select_from(
                        query.subquery()
                    )
                )
                or 0
            )
            rows = self._db.scalars(
                ordered.offset(offset).limit(read_limit)
            ).all()

        return [
            article_projection_to_entity(row) for row in rows
        ], total

    def search_feed(
        self,
        *,
        user_id: UUID,
        q: str,
        excluded_languages: Sequence[str],
        blocked_source_ids: Sequence[str],
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
            excluded_languages=excluded_languages,
            blocked_source_ids=blocked_source_ids,
            include_languages=include_languages,
            include_source_ids=include_source_ids,
            published_from=published_from,
            published_to=published_to,
        )

        ordered = query.order_by(*self._order_by(sort))

        if include_categories:
            all_rows = self._db.scalars(ordered).all()
            filtered_rows = [
                row
                for row in all_rows
                if self._matches_categories(row, include_categories)
            ]
            total = len(filtered_rows)
            rows = filtered_rows[offset : offset + limit]
        else:
            total = (
                self._db.scalar(
                    select(func.count()).select_from(
                        query.subquery()
                    )
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

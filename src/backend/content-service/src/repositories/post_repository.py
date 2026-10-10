import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.models.post import Post

logger = logging.getLogger(__name__)

CANONICAL_POST_FIELDS = (
    "url",
    "source_title",
    "title",
    "description",
    "category",
    "content",
    "author",
    "published_at",
    "image_url",
    "language",
    "keywords",
)


class PostRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_posts(
        self,
        *,
        limit: int,
        skip: int,
        source_id: UUID | None = None,
        language: str | None = None,
        category: str | None = None,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
        parsed_from: datetime | None = None,
        parsed_to: datetime | None = None,
    ) -> list[Post]:
        query = self._db.query(Post)

        if source_id:
            query = query.filter(Post.source_id == source_id)
        if language:
            query = query.filter(Post.language == language)
        if category:
            query = query.filter(func.lower(Post.category) == category.lower())
        if published_from:
            query = query.filter(Post.published_at >= published_from)
        if published_to:
            query = query.filter(Post.published_at <= published_to)
        if parsed_from:
            query = query.filter(Post.parsed_at >= parsed_from)
        if parsed_to:
            query = query.filter(Post.parsed_at <= parsed_to)

        query = query.order_by(Post.parsed_at.desc())

        return query.offset(skip).limit(limit).all()

    def get_post_by_id(self, post_id: UUID) -> Post | None:
        return self._db.query(Post).filter(Post.post_id == post_id).first()

    def get_by_guids(self, source_id: UUID, guids: list[str]) -> list[Post]:
        if not guids:
            return []

        return (
            self._db.query(Post)
            .filter(Post.source_id == source_id, Post.item_guid.in_(guids))
            .all()
        )

    def get_posts_count(self) -> int:
        return self._db.query(Post).count()

    def create_post(self, post_data: dict[str, Any]) -> dict[str, Any]:
        insert_statement = insert(Post).values(**post_data)
        excluded = insert_statement.excluded
        update_fields = {
            field: getattr(excluded, field) for field in CANONICAL_POST_FIELDS
        }
        update_fields.update(
            {
                "crawled_at": excluded.crawled_at,
                "parsed_at": excluded.parsed_at,
                "post_revision": Post.post_revision + 1,
            }
        )
        changed_fields = or_(
            *(
                getattr(Post, field).is_distinct_from(getattr(excluded, field))
                for field in CANONICAL_POST_FIELDS
            )
        )
        upsert_statement = (
            insert_statement.on_conflict_do_update(
                index_elements=["source_id", "item_guid"],
                set_=update_fields,
                where=changed_fields,
            )
            .returning(*Post.__table__.columns)
        )

        row = self._db.execute(upsert_statement).mappings().one_or_none()
        if row is not None:
            snapshot = dict(row)
            action = "inserted" if snapshot["post_revision"] == 1 else "updated"
        else:
            existing = (
                self._db.execute(
                    select(*Post.__table__.columns).where(
                        Post.source_id == post_data["source_id"],
                        Post.item_guid == post_data["item_guid"],
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is None:
                raise RuntimeError(
                    "Post upsert matched no row and the existing post could not be read"
                )
            snapshot = dict(existing)
            action = "unchanged"

        self._db.commit()
        logger.debug(
            "Post snapshot %s (post_id=%s, post_revision=%d)",
            action,
            snapshot["post_id"],
            snapshot["post_revision"],
        )
        return snapshot

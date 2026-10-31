import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.models.post import Post

logger = logging.getLogger(__name__)

POST_FIELDS = (
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

    def list_posts(
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
        conditions = [Post.is_deleted.is_(False)]

        if source_id:
            conditions.append(Post.source_id == source_id)
        if language:
            conditions.append(Post.language == language)
        if category:
            conditions.append(func.lower(Post.category) == category.lower())
        if published_from:
            conditions.append(Post.published_at >= published_from)
        if published_to:
            conditions.append(Post.published_at <= published_to)
        if parsed_from:
            conditions.append(Post.parsed_at >= parsed_from)
        if parsed_to:
            conditions.append(Post.parsed_at <= parsed_to)

        statement = select(Post).where(*conditions).order_by(Post.parsed_at.desc())

        return list(self._db.scalars(statement.offset(skip).limit(limit)).all())

    def get_by_id(self, post_id: UUID) -> Post | None:
        return self._db.scalar(
            select(Post)
            .where(Post.post_id == post_id, Post.is_deleted.is_(False))
            .limit(1)
        )

    def get_any_by_id(self, post_id: UUID) -> Post | None:
        return self._db.get(Post, post_id)

    def delete_post(self, post_id: UUID) -> Post | None:
        post = self.get_any_by_id(post_id)
        if post is None:
            return None
        if not post.is_deleted:
            post.is_deleted = True
            post.deleted_at = datetime.now(UTC)
            post.post_revision += 1
            post.parsed_at = post.deleted_at
            self._db.flush()
        return post

    def patch_post(
        self, post_id: UUID, fields: dict[str, Any]
    ) -> dict[str, Any] | None:
        post = self.get_by_id(post_id)
        if post is None:
            return None

        for field, value in fields.items():
            setattr(post, field, value)
        post.post_revision += 1
        post.parsed_at = datetime.now(UTC)
        self._db.flush()
        snapshot = {
            column.name: getattr(post, column.name)
            for column in Post.__table__.columns
        }
        return snapshot

    def get_by_guids(self, source_id: UUID, guids: list[str]) -> list[Post]:
        if not guids:
            return []

        return list(
            self._db.scalars(
                select(Post).where(
                    Post.source_id == source_id,
                    Post.item_guid.in_(guids),
                )
            ).all()
        )

    def count_posts(self) -> int:
        return (
            self._db.scalar(
                select(func.count())
                .select_from(Post)
                .where(Post.is_deleted.is_(False))
            )
            or 0
        )

    def upsert_post(self, post_data: dict[str, Any]) -> dict[str, Any]:
        insert_statement = insert(Post).values(**post_data)
        excluded = insert_statement.excluded
        update_fields = {field: getattr(excluded, field) for field in POST_FIELDS}
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
                for field in POST_FIELDS
            )
        )
        upsert_statement = insert_statement.on_conflict_do_update(
            index_elements=["source_id", "item_guid"],
            set_=update_fields,
            where=and_(Post.is_deleted.is_(False), changed_fields),
        ).returning(*Post.__table__.columns)

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
            action = "deleted" if snapshot["is_deleted"] else "unchanged"

        logger.debug(
            "Post snapshot %s (post_id=%s, post_revision=%d)",
            action,
            snapshot["post_id"],
            snapshot["post_revision"],
        )

        return snapshot

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

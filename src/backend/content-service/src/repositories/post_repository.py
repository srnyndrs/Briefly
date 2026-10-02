from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.models.post import Post


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

    def create_post(self, post_data: dict[str, Any]) -> dict[str, Any] | None:
        insert_statement = insert(Post).values(**post_data)
        update_fields = {
            "item_guid": insert_statement.excluded.item_guid,
            "url": insert_statement.excluded.url,
            "source_title": insert_statement.excluded.source_title,
            "title": insert_statement.excluded.title,
            "description": insert_statement.excluded.description,
            "category": insert_statement.excluded.category,
            "content": insert_statement.excluded.content,
            "author": insert_statement.excluded.author,
            "published_at": insert_statement.excluded.published_at,
            "crawled_at": insert_statement.excluded.crawled_at,
            "parsed_at": insert_statement.excluded.parsed_at,
            "image_url": insert_statement.excluded.image_url,
            "language": insert_statement.excluded.language,
            "keywords": insert_statement.excluded.keywords,
            "post_revision": Post.post_revision + 1,
        }
        upsert_statement = insert_statement.on_conflict_do_update(
            index_elements=["source_id", "item_guid"],
            set_=update_fields,
        ).returning(*Post.__table__.columns)

        row = self._db.execute(upsert_statement).mappings().one_or_none()
        snapshot = dict(row) if row is not None else None
        self._db.commit()

        return snapshot

from datetime import datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.post import Post


class PostRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(self, post_data: dict[str, Any]) -> str | None:
        stmt = insert(Post).values(**post_data)
        update_fields = {
            "item_guid": stmt.excluded.item_guid,
            "title": stmt.excluded.title,
            "description": stmt.excluded.description,
            "category": stmt.excluded.category,
            "content": stmt.excluded.content,
            "author": stmt.excluded.author,
            "published_at": stmt.excluded.published_at,
            "crawled_at": stmt.excluded.crawled_at,
            "parsed_at": stmt.excluded.parsed_at,
            "image_url": stmt.excluded.image_url,
            "language": stmt.excluded.language,
            "keywords": stmt.excluded.keywords,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_id", "url"],
            set_=update_fields,
        ).returning(Post.post_id)
        try:
            inserted_id = self._db.scalar(stmt)
            self._db.commit()
            return str(inserted_id) if inserted_id else None
        except IntegrityError:
            self._db.rollback()
            existing_id = (
                self._db.query(Post.post_id)
                .filter(
                    Post.source_id == post_data["source_id"],
                    Post.item_guid == post_data["item_guid"],
                )
                .scalar()
            )
            return str(existing_id) if existing_id else None

    def get_by_id(self, post_id: str) -> Post | None:
        return (
            self._db.query(Post)
            .filter(Post.post_id == post_id)
            .one_or_none()
        )

    def count(self) -> int:
        return self._db.query(Post).count()

    def list(
        self,
        *,
        limit: int,
        skip: int,
        source_id: str | None = None,
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
        if published_from:
            query = query.filter(
                Post.published_at >= published_from
            )
        if published_to:
            query = query.filter(
                Post.published_at <= published_to
            )
        if parsed_from:
            query = query.filter(Post.parsed_at >= parsed_from)
        if parsed_to:
            query = query.filter(Post.parsed_at <= parsed_to)

        query = query.order_by(Post.parsed_at.desc())

        if category:
            category_lower = category.lower()
            all_docs = query.all()
            filtered = [
                doc
                for doc in all_docs
                if any(
                    c.lower() == category_lower
                    for c in (doc.keywords or [])
                )
            ]
            return filtered[skip : skip + limit]

        return query.offset(skip).limit(limit).all()

from datetime import datetime
from typing import Any

from src.repositories.post_repository import PostRepository


class PostService:
    def __init__(self, repository: PostRepository) -> None:
        self._repo = repository

    def get_by_id(self, post_id: str) -> dict[str, Any] | None:
        post = self._repo.get_by_id(post_id)
        if post is None:
            return None
        return {
            "post_id": post.post_id,
            "source_id": post.source_id,
            "item_guid": post.item_guid,
            "url": post.url,
            "title": post.title,
            "description": post.description,
            "category": post.category,
            "content": post.content,
            "author": post.author,
            "published_at": post.published_at,
            "crawled_at": post.crawled_at,
            "parsed_at": post.parsed_at,
            "image_url": post.image_url,
            "language": post.language,
            "keywords": post.keywords,
        }

    def get_count(self) -> int:
        return self._repo.count()

    def list_posts(
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
    ) -> list[dict[str, Any]]:
        posts = self._repo.list(
            limit=limit,
            skip=skip,
            source_id=source_id,
            language=language,
            category=category,
            published_from=published_from,
            published_to=published_to,
            parsed_from=parsed_from,
            parsed_to=parsed_to,
        )
        return [
            {
                "post_id": p.post_id,
                "source_id": p.source_id,
                "item_guid": p.item_guid,
                "url": p.url,
                "title": p.title,
                "description": p.description,
                "category": p.category,
                "content": p.content,
                "author": p.author,
                "published_at": p.published_at,
                "crawled_at": p.crawled_at,
                "parsed_at": p.parsed_at,
                "image_url": p.image_url,
                "language": p.language,
                "keywords": p.keywords,
            }
            for p in posts
        ]

from datetime import datetime

from src.models.article import Article
from src.repositories.article_repository import ArticleRepository


def _to_dict(doc: Article) -> dict:
    return {
        "id": doc.id,
        "feed_id": doc.feed_id,
        "item_guid": doc.item_guid,
        "url": doc.url,
        "title": doc.title,
        "description": doc.description,
        "category": doc.category,
        "content": doc.content,
        "author": doc.author,
        "published_at": doc.published_at,
        "crawled_at": doc.crawled_at,
        "parsed_at": doc.parsed_at,
        "image_url": doc.image_url,
        "language": doc.language,
        "keywords": doc.keywords or [],
    }


class ArticleService:
    def __init__(self, repo: ArticleRepository) -> None:
        self._repo = repo

    def get_count(self) -> int:
        return self._repo.count()

    def get_by_id(self, article_id: str) -> dict | None:
        doc = self._repo.get_by_id(article_id)
        return _to_dict(doc) if doc is not None else None

    def list_articles(
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
    ) -> list[dict]:
        docs = self._repo.list(
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
        return [_to_dict(d) for d in docs]

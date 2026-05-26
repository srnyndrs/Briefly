import logging
from datetime import datetime, timezone
from typing import Any

import feedparser
from sqlalchemy.orm import Session

from src.repositories.article_repository import ArticleRepository
from src.services import content_extractor, event_publisher

logger = logging.getLogger(__name__)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _entry_published_at(entry: Any) -> datetime | None:
    if entry.get("published_parsed"):
        return datetime(
            *entry.published_parsed[:6], tzinfo=timezone.utc
        )
    return None


def _build_article_data(
    feed_id: str,
    entry: Any,
    crawled_at: datetime | None,
    source_title: str | None = None,
) -> dict[str, Any]:
    item_guid = entry.get("guid") or entry.get("link", "")
    url = entry.get("link", "")
    title = entry.get("title", "Untitled")
    author = entry.get("author", None)
    category = entry.get("category", None)
    published_at = _entry_published_at(entry)

    extracted = (
        content_extractor.extract_article(url) if url else {}
    )

    final_title = extracted.get("title") or title
    description = extracted.get("description") or None
    content = extracted.get("content") or None
    authors = extracted.get("authors") or []
    final_author = authors[0] if authors else author
    final_published_at = published_at or extracted.get(
        "publish_date"
    )
    image_url = extracted.get("image") or None
    keywords = extracted.get("keywords") or []
    language = extracted.get("language") or None

    return {
        "feed_id": feed_id,
        "item_guid": item_guid,
        "url": url,
        "title": final_title,
        "description": description,
        "category": category,
        "content": content,
        "author": final_author,
        "published_at": final_published_at,
        "crawled_at": crawled_at,
        "parsed_at": datetime.now(timezone.utc),
        "image_url": image_url,
        "language": language,
        "keywords": keywords,
        "source_title": source_title,
    }


class FeedProcessorService:
    def __init__(self, db: Session) -> None:
        self._repo = ArticleRepository(db)

    def process(self, channel: Any, event: dict[str, Any]) -> None:
        payload = event.get("payload", {})
        raw_xml = payload.get("raw_xml", "")
        feed_id = payload.get("feed_id", "")
        crawled_at = _parse_dt(event.get("occurred_at"))

        feed = feedparser.parse(raw_xml)
        source_title = payload.get("source_title") or (
            feed.feed.get("title")
            if hasattr(feed, "feed")
            else None
        )
        for entry in feed.entries:
            item_guid = entry.get("id") or entry.get("link", "")
            try:
                article_data = _build_article_data(
                    feed_id, entry, crawled_at, source_title
                )
            except Exception as exc:
                logger.error(
                    "Failed to build article data for %s/%s: %s",
                    feed_id,
                    item_guid,
                    exc,
                )
                event_publisher.publish_parsed_failed(
                    channel,
                    feed_id=feed_id,
                    item_guid=item_guid,
                    error=str(exc),
                )
                continue

            source_title_val = article_data.pop(
                "source_title", None
            )
            article_id = self._repo.save(article_data)
            if article_id:
                article_data["source_title"] = source_title_val
                self._publish_success_events(
                    channel, article_id, article_data
                )

    def _publish_success_events(
        self,
        channel: Any,
        article_id: str,
        data: dict[str, Any],
    ) -> None:
        feed_id = data["feed_id"]
        event_publisher.publish_parsed_success(
            channel,
            article_id=article_id,
            feed_id=feed_id,
            item_guid=data["item_guid"],
            url=data["url"],
            title=data["title"],
            category=data["category"],
            content=data["content"],
            content_length=len(data["content"] or ""),
            description=data.get("description"),
            published_at=data["published_at"].isoformat()
            if data["published_at"]
            else None,
            language=data["language"],
            keywords=data["keywords"],
            source_title=data.get("source_title"),
        )
        event_publisher.publish_article_updated(
            channel,
            article_id=article_id,
            source_id=feed_id,
            changed_fields=[
                "title",
                "description",
                "category",
                "content",
                "author",
                "published_at",
                "parsed_at",
            ],
        )
        event_publisher.publish_article_content_extracted(
            channel,
            article_id=article_id,
            source_id=feed_id,
            content_ref=f"article:{article_id}",
            image_ref=data["image_url"],
        )
        event_publisher.publish_article_enriched(
            channel,
            article_id=article_id,
            source_id=feed_id,
            sentiment="unknown",
            topics=[],
            cluster_id=None,
            model_version="content-service-default-v1",
        )

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import feedparser
from sqlalchemy.orm import Session

from src.adapters import content_extractor, post_publisher
from src.repositories.post_repository import PostRepository

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


def _build_post_data(
    source_id: str,
    entry: Any,
    crawled_at: datetime | None,
    source_title: str | None = None,
) -> dict[str, Any]:
    item_guid = (
        entry.get("guid") or entry.get("id") or entry.get("link", "")
    )
    url = entry.get("link", "")
    title = entry.get("title", "Untitled")
    author = entry.get("author", None)
    category = entry.get("category", None)
    published_at = _entry_published_at(entry)

    extracted = content_extractor.extract_article(url) if url else {}

    final_title = extracted.get("title") or title
    description = extracted.get("description") or None
    content = extracted.get("content") or None
    authors = extracted.get("authors") or []
    final_author = authors[0] if authors else author
    final_published_at = published_at or extracted.get("publish_date")
    image_url = extracted.get("image") or None
    keywords = extracted.get("keywords") or []
    language = extracted.get("language") or None

    return {
        "source_id": source_id,
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


class SourceProcessorService:
    def __init__(self, db: Session) -> None:
        self._repo = PostRepository(db)

    def process(self, channel: Any, event: dict[str, Any]) -> None:
        payload = event.get("payload", {})
        raw_xml = payload.get("raw_xml", "")
        source_id = payload.get("source_id", "")
        crawled_at = _parse_dt(event.get("occurred_at"))
        correlation_id = event.get("correlation_id") or str(
            uuid.uuid4()
        )

        feed = feedparser.parse(raw_xml)
        source_title = payload.get("source_title") or (
            feed.feed.get("title") if hasattr(feed, "feed") else None
        )
        for entry in feed.entries:
            item_guid = (
                entry.get("id")
                or entry.get("guid")
                or entry.get("link", "")
            )
            try:
                post_data = _build_post_data(
                    source_id, entry, crawled_at, source_title
                )
            except Exception as exc:
                logger.error(
                    "Failed to build post data for %s/%s: %s",
                    source_id,
                    item_guid,
                    exc,
                )
                continue

            post_id = self._repo.save(post_data)
            if post_id:
                _publish_success_events(
                    channel, post_id, post_data, correlation_id
                )


def _publish_success_events(
    channel: Any,
    post_id: str,
    data: dict[str, Any],
    correlation_id: str,
) -> None:
    source_id = data["source_id"]
    post_publisher.publish_post_parsed_success(
        channel,
        post_id=post_id,
        source_id=source_id,
        item_guid=data["item_guid"],
        url=data["url"],
        title=data["title"],
        correlation_id=correlation_id,
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
        image_url=data.get("image_url"),
    )

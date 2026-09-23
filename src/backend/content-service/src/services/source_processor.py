import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import feedparser
from sqlalchemy.orm import Session

from src.adapters import content_extractor, post_publisher
from src.repositories.post_repository import PostRepository

logger = logging.getLogger(__name__)

_INVALID_TITLES = frozenset({"null", "undefined", "null: undefined"})


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_description(value: Any) -> str | None:
    description = _clean_text(value)
    if description is None:
        return None
    return _clean_text(
        content_extractor.normalize_html_text(description)
    )


def _require_source_value(value: Any, field_name: str) -> str:
    normalized = _clean_text(value)
    if normalized is None:
        raise ValueError(f"{field_name} must be nonblank")
    return normalized


def _require_source_title(value: Any) -> str:
    title = _require_source_value(value, "source_title")
    if len(title) > 255:
        raise ValueError("source_title must be at most 255 characters")
    return title


def _clean_title(value: Any) -> str | None:
    title = _clean_text(value)
    if title and title.casefold() not in _INVALID_TITLES:
        return title
    return None


def _clean_values(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return []
    return [
        cleaned
        for value in values
        if (cleaned := _clean_text(value)) is not None
    ]


def _entry_tags(entry: Any) -> list[str]:
    tags = entry.get("tags") or []
    return _clean_values(
        [tag.get("term") for tag in tags if hasattr(tag, "get")]
    )


def _entry_image(entry: Any) -> str | None:
    for enclosure in entry.get("enclosures") or []:
        image_url = _clean_text(
            enclosure.get("href") or enclosure.get("url")
        )
        if image_url:
            return image_url

    for media in entry.get("media_content") or []:
        image_url = _clean_text(media.get("url"))
        if image_url:
            return image_url

    return None


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
    source_title: str,
    feed_language: str | None = None,
) -> dict[str, Any]:
    item_guid = (
        entry.get("guid") or entry.get("id") or entry.get("link", "")
    )
    url = entry.get("link", "")
    tags = _entry_tags(entry)
    title = _clean_title(entry.get("title"))
    description = _clean_description(
        entry.get("description")
    ) or _clean_description(entry.get("summary"))
    author = _clean_text(entry.get("author"))
    category = _clean_text(entry.get("category")) or (
        tags[0] if tags else None
    )
    published_at = _entry_published_at(entry)

    extracted = content_extractor.extract_article(url) if url else {}
    extracted_title = _clean_title(extracted.get("title"))
    if _clean_text(extracted.get("title")) and not extracted_title:
        logger.warning(
            "Ignoring invalid extracted title for %s: %r",
            url,
            extracted.get("title"),
        )

    final_title = title or extracted_title or "Untitled"
    description = description or _clean_description(
        extracted.get("description")
    )
    content = _clean_text(extracted.get("content"))
    authors = _clean_values(extracted.get("authors"))
    final_author = author or (authors[0] if authors else None)
    final_published_at = published_at or extracted.get("publish_date")
    image_url = _entry_image(entry) or _clean_text(
        extracted.get("image")
    )
    keywords = _clean_values(extracted.get("keywords")) or tags
    language = (
        _clean_text(entry.get("language"))
        or _clean_text(feed_language)
        or _clean_text(extracted.get("language"))
    )

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
        source_id = _require_source_value(
            payload.get("source_id"), "source_id"
        )
        source_title = _require_source_title(
            payload.get("source_title")
        )
        crawled_at = _parse_dt(event.get("occurred_at"))
        correlation_id = event.get("correlation_id") or str(
            uuid.uuid4()
        )

        feed = feedparser.parse(raw_xml)
        feed_data = feed.feed if hasattr(feed, "feed") else {}
        feed_language = feed_data.get("language")
        for entry in feed.entries:
            item_guid = (
                entry.get("id")
                or entry.get("guid")
                or entry.get("link", "")
            )
            try:
                post_data = _build_post_data(
                    source_id,
                    entry,
                    crawled_at,
                    source_title,
                    feed_language,
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
        author=data["author"],
        source_title=data["source_title"],
        image_url=data.get("image_url"),
    )

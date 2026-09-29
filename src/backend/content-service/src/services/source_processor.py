import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from urllib.parse import urlsplit

import feedparser
import langcodes
from sqlalchemy.orm import Session

from src.adapters import content_extractor, post_publisher
from src.models.post import Post
from src.repositories.post_repository import PostRepository

logger = logging.getLogger(__name__)

_INVALID_TITLES = frozenset({"null", "undefined", "null: undefined"})


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_language(value: Any) -> str | None:
    candidate = _clean_text(value)
    if candidate is None:
        return None

    try:
        language = langcodes.get(candidate.replace("_", "-"))
    except (TypeError, ValueError):
        return None

    if not language.is_valid() or not language.language:
        return None
    primary = language.language.lower()
    return (
        None
        if primary == "und" or primary.startswith("x-")
        else primary
    )


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
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return (
            parsed
            if parsed.tzinfo
            else parsed.replace(tzinfo=timezone.utc)
        )
    except Exception:
        return None


def _entry_published_at(entry: Any) -> datetime | None:
    if entry.get("published_parsed"):
        return datetime(
            *entry.published_parsed[:6], tzinfo=timezone.utc
        )
    return None


def _entry_guid(entry: Any) -> str:
    for field in ("guid", "id", "link"):
        value = _clean_text(entry.get(field))
        if value:
            return value
    raise ValueError("item_guid must be nonblank")


def _stored_post_data(post: Post) -> dict[str, Any]:
    return {
        "url": post.url,
        "title": post.title,
        "description": post.description,
        "category": post.category,
        "content": post.content,
        "author": post.author,
        "published_at": post.published_at,
        "image_url": post.image_url,
        "language": post.language,
        "keywords": post.keywords,
    }


def _build_post_data(
    source_id: str,
    entry: Any,
    crawled_at: datetime | None,
    source_title: str,
    feed_language: str | None = None,
    *,
    item_guid: str,
    url: str,
    extracted: dict[str, Any],
    stored: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stored = stored or {}
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

    extracted_title = _clean_title(extracted.get("title"))
    if _clean_text(extracted.get("title")) and not extracted_title:
        logger.warning(
            "Ignoring invalid extracted title (host=%s, title=%r)",
            urlsplit(url).hostname,
            extracted.get("title"),
        )

    final_title = (
        title
        or extracted_title
        or _clean_title(stored.get("title"))
        or "Untitled"
    )
    description = (
        description
        or _clean_description(extracted.get("description"))
        or _clean_description(stored.get("description"))
    )
    category = category or _clean_text(stored.get("category"))
    content = _clean_text(extracted.get("content")) or _clean_text(
        stored.get("content")
    )
    authors = _clean_values(extracted.get("authors"))
    final_author = (
        author
        or (authors[0] if authors else None)
        or _clean_text(stored.get("author"))
    )
    final_published_at = (
        published_at
        or extracted.get("publish_date")
        or stored.get("published_at")
    )
    image_url = (
        _entry_image(entry)
        or _clean_text(extracted.get("image"))
        or _clean_text(stored.get("image_url"))
    )
    keywords = (
        _clean_values(extracted.get("keywords"))
        or _clean_values(stored.get("keywords"))
        or tags
    )
    language = next(
        (
            normalized
            for candidate in (
                entry.get("language"),
                feed_language,
                extracted.get("language"),
                stored.get("language"),
            )
            if (normalized := _normalize_language(candidate))
            is not None
        ),
        None,
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

    def reextract_post(self, channel: Any, post_id: str) -> bool:
        """Refresh one post body while preserving stored metadata and identity."""
        post = self._repo.get_by_id(post_id)
        if post is None:
            raise ValueError("Post not found")
        extracted = content_extractor.extract_article(post.url)
        content = extracted.get("content")
        if (
            extracted.get("error")
            or not isinstance(content, str)
            or not content.strip()
        ):
            return False
        data = {
            **_stored_post_data(post),
            "source_id": post.source_id,
            "item_guid": post.item_guid,
            "source_title": post.source_title,
            "crawled_at": post.crawled_at,
            "parsed_at": datetime.now(timezone.utc),
            "content": content.strip(),
        }
        saved_id = self._repo.save(data)
        if not saved_id:
            raise RuntimeError("Post save returned no ID")
        _publish_success_events(
            channel, saved_id, data, f"reextract-{uuid.uuid4()}"
        )
        return True

    def process(
        self,
        channel: Any,
        event: dict[str, Any],
        *,
        on_progress: Callable[[], None] | None = None,
    ) -> None:
        started = perf_counter()
        processing_at = datetime.now(timezone.utc)
        if (
            not isinstance(event, dict)
            or event.get("event_type") != "feed.raw_fetched.v1"
        ):
            raise ValueError("Expected a feed.raw_fetched.v1 event")
        payload = event.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        raw_xml = payload.get("raw_xml")
        if not isinstance(raw_xml, str) or not raw_xml.strip():
            raise ValueError("raw_xml must be nonblank XML")
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
        age_seconds = (
            max(0, (processing_at - crawled_at).total_seconds())
            if crawled_at
            else None
        )

        feed = feedparser.parse(raw_xml)
        if not feed.entries and (not feed.version or feed.bozo):
            raise ValueError("raw_xml is not a usable RSS/Atom feed")
        feed_data = feed.feed if hasattr(feed, "feed") else {}
        feed_language = feed_data.get("language")
        entries = [
            (_entry_guid(entry), entry) for entry in feed.entries
        ]
        stored_posts = {
            post.item_guid: _stored_post_data(post)
            for post in self._repo.get_by_guids(
                source_id,
                list(dict.fromkeys(guid for guid, _ in entries)),
            )
        }
        attempted = reused = partial = 0
        completed = False
        try:
            if on_progress:
                on_progress()
            for item_guid, entry in entries:
                stored = stored_posts.get(item_guid)
                url = (
                    content_extractor.normalize_article_url(
                        entry.get("link")
                    )
                    or ""
                )
                extracted = {}
                if stored is not None and stored["url"] == url:
                    reused += 1
                elif url:
                    attempted += 1
                    extracted = content_extractor.extract_article(url)
                post_data = _build_post_data(
                    source_id,
                    entry,
                    crawled_at,
                    source_title,
                    feed_language,
                    item_guid=item_guid,
                    url=url,
                    extracted=extracted,
                    stored=stored,
                )
                partial += bool(
                    not url
                    or extracted.get("error")
                    or not post_data["content"]
                )

                post_id = self._repo.save(post_data)
                if not post_id:
                    raise RuntimeError("Post save returned no ID")
                stored_posts[item_guid] = post_data
                _publish_success_events(
                    channel, post_id, post_data, correlation_id
                )
                if on_progress:
                    on_progress()
            completed = True
        finally:
            logger.info(
                "Feed processing (event_id=%s, source_id=%s, "
                "correlation_id=%s, completed=%s, age_seconds=%s, "
                "entries=%d, attempted=%d, reused=%d, partial=%d, "
                "duration_seconds=%.3f)",
                event.get("event_id"),
                source_id,
                correlation_id,
                completed,
                age_seconds,
                len(entries),
                attempted,
                reused,
                partial,
                perf_counter() - started,
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

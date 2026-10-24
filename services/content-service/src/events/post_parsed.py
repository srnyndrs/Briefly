"""Build the parsed post event published after persistence."""

from datetime import UTC, datetime
from typing import Any

from src.events.envelope import build_envelope


def build_post_parsed_event(
    *,
    post_id: str,
    source_id: str,
    post_revision: int,
    item_guid: str,
    url: str,
    title: str,
    correlation_id: str,
    category: str | None = None,
    content: str | None,
    description: str | None = None,
    published_at: str | None = None,
    language: str | None = None,
    keywords: list[str] | None = None,
    author: str | None = None,
    source_title: str,
    image_url: str | None = None,
) -> dict[str, Any]:
    payload = {
        "post_id": post_id,
        "source_id": source_id,
        "post_revision": post_revision,
        "item_guid": item_guid,
        "url": url,
        "title": title,
        "parsed_at": datetime.now(UTC).isoformat(),
        "content": content,
        "content_length": len(content or ""),
        "source_title": source_title,
        "image_url": image_url,
        "description": description,
        "published_at": published_at,
        "language": language,
        "keywords": keywords if keywords is not None else [],
        "author": author,
        "category": category,
    }
    return build_envelope(
        event_type="post.parsed.v1",
        partition_key=f"source:{source_id}",
        payload=payload,
        correlation_id=correlation_id,
    )

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from src.events.envelope import build_envelope

_POST_EVENT_TYPE = "post.parsed.v1"


def build_post_parsed_event(
    snapshot: Mapping[str, Any], *, correlation_id: str
) -> dict[str, Any]:
    published_at = snapshot["published_at"]
    if published_at is not None:
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)
        published_at = published_at.isoformat()

    content = snapshot["content"]
    source_id = str(snapshot["source_id"])
    payload = {
        "post_id": str(snapshot["post_id"]),
        "source_id": source_id,
        "post_revision": snapshot["post_revision"],
        "item_guid": snapshot["item_guid"],
        "url": snapshot["url"],
        "title": snapshot["title"],
        "parsed_at": datetime.now(UTC).isoformat(),
        "content": content,
        "content_length": len(content or ""),
        "source_title": snapshot["source_title"],
        "image_url": snapshot["image_url"],
        "description": snapshot["description"],
        "published_at": published_at,
        "language": snapshot["language"],
        "keywords": snapshot["keywords"],
        "author": snapshot["author"],
        "category": snapshot["category"],
    }

    return build_envelope(
        event_type=_POST_EVENT_TYPE,
        partition_key=f"source:{source_id}",
        payload=payload,
        correlation_id=correlation_id,
    )

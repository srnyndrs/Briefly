import json
from datetime import datetime, timezone
from typing import Any

import pika

from src.config.settings import settings
from src.events.envelope import build_envelope


def _publish(
    channel: Any, routing_key: str, envelope: dict[str, Any]
) -> None:
    body = json.dumps(envelope, default=str, ensure_ascii=False).encode(
        "utf-8"
    )
    channel.basic_publish(
        exchange=settings.parsed_exchange,
        routing_key=routing_key,
        body=body,
        mandatory=True,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent,
            content_type="application/json",
        ),
    )


def publish_post_parsed_success(
    channel: Any,
    *,
    post_id: str,
    source_id: str,
    item_guid: str,
    url: str,
    title: str,
    correlation_id: str,
    category: str | None = None,
    content: str | None,
    content_length: int,
    description: str | None = None,
    published_at: str | None = None,
    language: str | None = None,
    keywords: list[str] | None = None,
    author: str | None = None,
    source_title: str,
    image_url: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "post_id": post_id,
        "source_id": source_id,
        "item_guid": item_guid,
        "url": url,
        "title": title,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "content": content,
        "content_length": content_length,
        "source_title": source_title,
    }
    payload.update(
        {
            "image_url": image_url,
            "description": description,
            "published_at": published_at,
            "language": language,
            "keywords": keywords if keywords is not None else [],
            "author": author,
            "category": category,
        }
    )

    envelope = build_envelope(
        event_type="post.parsed.v1",
        partition_key=f"source:{source_id}",
        payload=payload,
        correlation_id=correlation_id,
    )
    _publish(
        channel,
        "post.parsed.v1",
        envelope,
    )

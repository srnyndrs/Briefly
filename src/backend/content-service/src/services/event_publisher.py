import json
from datetime import datetime, timezone
from typing import Any

import pika

from src.config.settings import settings
from src.events.envelope import build_envelope


def _publish(
    channel: Any, routing_key: str, envelope: dict[str, Any]
) -> None:
    body = json.dumps(envelope, default=str, ensure_ascii=False).encode("utf-8")
    channel.basic_publish(
        exchange=settings.parsed_exchange,
        routing_key=routing_key,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent,
            content_type="application/json",
        ),
    )


def publish_parsed_success(
    channel: Any,
    *,
    article_id: str,
    feed_id: str,
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
    source_title: str | None = None,
    image_url: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "article_id": article_id,
        "feed_id": feed_id,
        "item_guid": item_guid,
        "url": url,
        "title": title,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "content": content,
        "content_length": content_length,
        "source_title": source_title,
    }
    if image_url is not None:
        payload["image_url"] = image_url
    if description is not None:
        payload["description"] = description
    if published_at:
        payload["published_at"] = published_at
    if language:
        payload["language"] = language
    if keywords is not None:
        payload["keywords"] = keywords
    if category is not None:
        payload["category"] = category
    envelope = build_envelope(
        event_type="article.parsed.v1",
        partition_key=f"source:{feed_id}",
        payload=payload,
        correlation_id=correlation_id,
    )
    _publish(
        channel,
        "article.parsed.v1",
        envelope,
    )

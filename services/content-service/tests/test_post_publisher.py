import json
from datetime import datetime
from unittest.mock import MagicMock
from uuid import UUID

import pika
import pytest

from src.adapters.event_publisher import publish_event
from src.config.settings import settings
from src.events.post_parsed import build_post_parsed_event


@pytest.mark.parametrize("populated", [True, False], ids=["populated", "nullable"])
def test_publisher_emits_complete_snapshot_and_envelope(
    populated: bool,
) -> None:
    channel = MagicMock()
    snapshot = {
        "post_id": "p1",
        "source_id": "s1",
        "post_revision": 3,
        "item_guid": "g1",
        "url": "https://example.com/article",
        "title": "Title",
        "source_title": "Source",
        "content": "Full body" if populated else None,
        "description": "Description" if populated else None,
        "category": "news" if populated else None,
        "author": "Author" if populated else None,
        "image_url": "https://example.com/image.jpg" if populated else None,
        "published_at": datetime(2026, 5, 5) if populated else None,
        "language": "en" if populated else None,
        "keywords": ["keyword"] if populated else [],
    }
    envelope = build_post_parsed_event(snapshot, correlation_id="corr-123")
    publish_event(channel, exchange=settings.parsed_exchange, envelope=envelope)
    channel.basic_publish.assert_called_once()
    published = channel.basic_publish.call_args.kwargs
    assert published["exchange"] == settings.parsed_exchange
    assert published["routing_key"] == "post.parsed.v1"
    assert published["mandatory"] is True
    assert published["properties"].message_id == envelope["event_id"]
    assert published["properties"].type == "post.parsed.v1"
    assert published["properties"].correlation_id == "corr-123"
    assert published["properties"].timestamp == int(
        datetime.fromisoformat(envelope["occurred_at"]).timestamp()
    )
    assert (
        published["properties"].delivery_mode == pika.DeliveryMode.Persistent.value
    )
    assert published["properties"].content_type == "application/json"
    envelope = json.loads(published["body"])
    assert envelope["event_type"] == "post.parsed.v1"
    assert envelope["schema_version"] == 1
    assert envelope["producer"] == "content-service"
    assert envelope["correlation_id"] == "corr-123"
    assert envelope["partition_key"] == "source:s1"
    assert UUID(envelope["event_id"])
    assert datetime.fromisoformat(envelope["occurred_at"]).tzinfo is not None
    assert len(envelope["trace"]["trace_id"]) == 32
    assert len(envelope["trace"]["span_id"]) == 16
    payload = envelope["payload"]
    assert datetime.fromisoformat(payload["parsed_at"]).tzinfo is not None
    assert payload == snapshot | {
        "published_at": "2026-05-05T00:00:00+00:00" if populated else None,
        "content_length": 9 if populated else 0,
        "parsed_at": payload["parsed_at"],
    }

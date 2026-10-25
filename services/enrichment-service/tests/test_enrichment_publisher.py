import json
from datetime import datetime
from unittest.mock import MagicMock
from uuid import UUID

import pika
import pytest

from src.adapters.event_publisher import publish_event
from src.config.settings import settings
from src.events.post_enriched import build_enrichment_event
from src.repositories.stored_enrichment import StoredEnrichment


@pytest.fixture
def saved() -> StoredEnrichment:
    return StoredEnrichment(
        post_id=UUID("e278cc08-f8d2-4787-a117-a2fa09486284"),
        event_id="7dad9c91-c917-4f4b-ad92-c98dcebc10d5",
        processed_at=datetime.fromisoformat("2026-10-23T10:00:00+00:00"),
        post_revision=2,
        enrichment_revision=1,
        status="completed",
        category_ids=("science",),
        reason=None,
    )


def test_publishes_persistent_mandatory_result(saved) -> None:
    channel = MagicMock()
    channel.basic_publish.return_value = None

    publish_event(
        channel,
        exchange=settings.result_exchange,
        envelope=build_enrichment_event(saved),
    )

    channel.basic_publish.assert_called_once()
    kwargs = channel.basic_publish.call_args.kwargs
    assert kwargs["exchange"] == settings.result_exchange
    assert kwargs["routing_key"] == "post.enriched.v1"
    assert kwargs["mandatory"] is True
    published = json.loads(kwargs["body"])
    published.pop("trace")
    assert published == {
        "event_id": saved.event_id,
        "event_type": "post.enriched.v1",
        "schema_version": 1,
        "partition_key": f"post:{saved.post_id}",
        "producer": "enrichment-service",
        "occurred_at": saved.processed_at.isoformat(),
        "correlation_id": saved.correlation_id,
        "payload": {
            "post_id": str(saved.post_id),
            "post_revision": 2,
            "enrichment_revision": 1,
            "status": "completed",
            "category_ids": ["science"],
        },
    }
    assert kwargs["properties"].delivery_mode == 2
    assert kwargs["properties"].content_type == "application/json"


@pytest.mark.parametrize(
    "error_type", [pika.exceptions.NackError, pika.exceptions.UnroutableError]
)
def test_publication_failure_propagates(saved, error_type) -> None:
    channel = MagicMock()
    error = error_type([])
    channel.basic_publish.side_effect = error

    with pytest.raises(error_type) as caught:
        publish_event(
            channel,
            exchange=settings.result_exchange,
            envelope=build_enrichment_event(saved),
        )
    assert caught.value is error

import json
from unittest.mock import MagicMock

import pytest

from src.adapters.result_publisher import publish_result
from src.config.settings import settings


@pytest.fixture
def saved_event() -> dict:
    return {
        "event_id": "7dad9c91-c917-4f4b-ad92-c98dcebc10d5",
        "event_type": "post.enriched.v1",
        "schema_version": 1,
        "partition_key": "post:e278cc08-f8d2-4787-a117-a2fa09486284",
        "producer": "enrichment-service",
        "occurred_at": "2026-10-23T10:00:00+00:00",
        "payload": {
            "post_id": "e278cc08-f8d2-4787-a117-a2fa09486284",
            "post_revision": 2,
            "enrichment_revision": 1,
            "status": "completed",
            "category_ids": ["science"],
        },
    }


def test_publishes_persistent_mandatory_result(saved_event) -> None:
    channel = MagicMock()

    publish_result(channel, saved_event)

    kwargs = channel.basic_publish.call_args.kwargs
    assert kwargs["exchange"] == settings.result_exchange
    assert kwargs["routing_key"] == "post.enriched.v1"
    assert kwargs["mandatory"] is True
    assert json.loads(kwargs["body"]) == saved_event
    assert kwargs["properties"].delivery_mode == 2


def test_unconfirmed_result_raises(saved_event) -> None:
    channel = MagicMock()
    channel.basic_publish.return_value = False

    with pytest.raises(RuntimeError, match="not confirmed"):
        publish_result(channel, saved_event)

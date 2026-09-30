import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pika
import pytest

from src.adapters.feed_publisher import FeedPublisher
from src.config.message_broker import create_feed_publisher_channel
from src.config.settings import settings


@patch("src.adapters.feed_publisher.create_feed_publisher_channel")
def test_publisher_keeps_raw_feed_event_contract(mock_create_channel):
    source_id = uuid.uuid4()
    publisher = FeedPublisher()
    publisher.publish_source_fetched(
        source_id=source_id,
        source_url="https://example.com/feed",
        correlation_id="cycle-1",
        source_title="Example",
        raw_xml="<feed/>",
    )

    published = mock_create_channel.return_value.basic_publish.call_args.kwargs
    envelope = json.loads(published["body"])
    assert published["exchange"] == settings.feed_exchange
    assert published["routing_key"] == "feed.raw_fetched.v1"
    assert published["mandatory"] is True
    assert (
        published["properties"].delivery_mode
        == pika.DeliveryMode.Persistent.value
    )
    assert published["properties"].content_type == "application/json"
    assert set(envelope) == {
        "event_id",
        "event_type",
        "schema_version",
        "occurred_at",
        "producer",
        "correlation_id",
        "partition_key",
        "trace",
        "payload",
    }
    assert uuid.UUID(envelope["event_id"])
    assert datetime.fromisoformat(envelope["occurred_at"]).tzinfo is not None
    assert envelope["event_type"] == "feed.raw_fetched.v1"
    assert envelope["schema_version"] == 1
    assert envelope["producer"] == "crawler-service"
    assert envelope["correlation_id"] == "cycle-1"
    assert envelope["partition_key"] == f"source:{source_id}"
    assert set(envelope["trace"]) == {"trace_id", "span_id"}
    assert len(envelope["trace"]["trace_id"]) == 32
    assert len(envelope["trace"]["span_id"]) == 16
    assert envelope["payload"] == {
        "source_id": str(source_id),
        "source_url": "https://example.com/feed",
        "source_title": "Example",
        "raw_xml": "<feed/>",
    }


@patch("src.config.message_broker.pika.BlockingConnection")
def test_feed_publisher_channel_declares_only_feed_exchange(
    mock_connection_cls: MagicMock,
) -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection_cls.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel

    channel = create_feed_publisher_channel()

    assert channel is mock_channel
    mock_channel.exchange_declare.assert_called_once_with(
        exchange=settings.feed_exchange,
        exchange_type="topic",
        durable=True,
    )
    mock_channel.confirm_delivery.assert_called_once_with()
    mock_channel.queue_declare.assert_not_called()
    mock_channel.queue_bind.assert_not_called()


@patch("src.adapters.feed_publisher.create_feed_publisher_channel")
def test_publisher_requires_routing_and_propagates_rejection(
    mock_create_channel: MagicMock,
) -> None:
    channel = MagicMock()
    channel.basic_publish.side_effect = pika.exceptions.UnroutableError([])
    mock_create_channel.return_value = channel

    publisher = FeedPublisher()
    with pytest.raises(pika.exceptions.UnroutableError):
        publisher.publish_source_fetched(
            source_id=uuid.uuid4(),
            source_url="https://example.com/feed",
            correlation_id="cycle-1",
            source_title="Example",
            raw_xml="<feed/>",
        )

    assert channel.basic_publish.call_args.kwargs["mandatory"] is True

import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pika
import pytest

from src.adapters.event_publisher import publish_event
from src.config.message_broker import publisher_channel
from src.config.settings import settings
from src.events.feed_fetched import build_feed_fetched_event


def test_publisher_keeps_raw_feed_event_contract() -> None:
    source_id = uuid.uuid4()
    envelope = build_feed_fetched_event(
        source_id=source_id,
        source_url="https://example.com/feed",
        correlation_id="cycle-1",
        source_title="Example",
        raw_xml="<feed/>一",
    )
    channel = MagicMock()

    publish_event(channel, exchange=settings.feed_exchange, envelope=envelope)

    published = channel.basic_publish.call_args.kwargs
    assert published["exchange"] == settings.feed_exchange
    assert published["routing_key"] == "feed.raw_fetched.v1"
    assert published["mandatory"] is True
    assert published["body"].decode("utf-8") == json.dumps(
        envelope, ensure_ascii=False
    )
    properties = published["properties"]
    assert properties.delivery_mode == pika.DeliveryMode.Persistent.value
    assert properties.content_type == "application/json"
    assert properties.message_id == envelope["event_id"]
    assert properties.type == envelope["event_type"]
    assert properties.correlation_id == "cycle-1"
    assert properties.timestamp == int(
        datetime.fromisoformat(envelope["occurred_at"]).timestamp()
    )
    assert envelope["producer"] == "crawler-service"
    assert envelope["partition_key"] == f"source:{source_id}"
    assert envelope["payload"] == {
        "source_id": str(source_id),
        "source_url": "https://example.com/feed",
        "source_title": "Example",
        "raw_xml": "<feed/>一",
    }


@patch("src.config.message_broker.pika.BlockingConnection")
def test_publisher_channel_declares_exchange_confirms_and_closes(
    mock_connection_cls: MagicMock,
) -> None:
    connection = mock_connection_cls.return_value
    channel = connection.channel.return_value

    with publisher_channel(exchange=settings.feed_exchange) as yielded:
        assert yielded is channel

    channel.exchange_declare.assert_called_once_with(
        exchange=settings.feed_exchange,
        exchange_type="topic",
        durable=True,
    )
    channel.confirm_delivery.assert_called_once_with()
    channel.queue_declare.assert_not_called()
    channel.queue_bind.assert_not_called()
    connection.close.assert_called_once_with()


def test_transport_propagates_broker_rejection() -> None:
    channel = MagicMock()
    error = pika.exceptions.UnroutableError([])
    channel.basic_publish.side_effect = error
    envelope = build_feed_fetched_event(
        source_id=uuid.uuid4(),
        source_url="https://example.com/feed",
        correlation_id="cycle-1",
        source_title="Example",
        raw_xml="<feed/>",
    )

    with pytest.raises(pika.exceptions.UnroutableError) as caught:
        publish_event(channel, exchange=settings.feed_exchange, envelope=envelope)
    assert caught.value is error


@patch("src.config.message_broker.pika.BlockingConnection")
def test_publisher_cleanup_preserves_primary_exception(
    mock_connection_cls: MagicMock,
) -> None:
    connection = mock_connection_cls.return_value
    primary_error = RuntimeError("publish failed")
    connection.close.side_effect = RuntimeError("cleanup failed")

    with pytest.raises(RuntimeError) as caught:
        with publisher_channel(exchange=settings.feed_exchange):
            raise primary_error

    assert caught.value is primary_error
    connection.close.assert_called_once_with()

import uuid
from unittest.mock import MagicMock, patch

import pika
import pytest

from src.adapters.feed_publisher import FeedPublisher
from src.config.message_broker import create_feed_publisher_channel
from src.config.settings import settings


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
    channel.basic_publish.side_effect = pika.exceptions.UnroutableError(
        []
    )
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

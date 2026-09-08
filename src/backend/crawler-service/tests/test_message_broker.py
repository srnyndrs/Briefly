from unittest.mock import MagicMock, patch

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
    mock_channel.queue_declare.assert_not_called()
    mock_channel.queue_bind.assert_not_called()

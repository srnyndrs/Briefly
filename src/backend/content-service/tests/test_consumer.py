from unittest.mock import MagicMock, call, patch

from src.config.settings import settings
from src.adapters.feed_consumer import FeedConsumer


def test_feed_consumer_stop_sets_event_and_calls_threadsafe() -> None:
    consumer = FeedConsumer()
    mock_conn = MagicMock()
    mock_conn.is_open = True
    consumer._connection = mock_conn

    assert not consumer._stop_event.is_set()
    consumer.stop()
    assert consumer._stop_event.is_set()
    mock_conn.add_callback_threadsafe.assert_called_once_with(
        consumer._safe_stop_consuming
    )


def test_feed_consumer_safe_stop_consuming_closes_channels() -> None:
    consumer = FeedConsumer()
    mock_channel = MagicMock()
    mock_channel.is_open = True
    mock_conn = MagicMock()
    mock_conn.is_open = True
    consumer._channel = mock_channel
    consumer._connection = mock_conn

    consumer._safe_stop_consuming()
    mock_channel.stop_consuming.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("src.adapters.feed_consumer.pika.BlockingConnection")
def test_consumer_startup_declares_both_exchanges_before_consuming(
    mock_connection_cls: MagicMock,
) -> None:
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_connection_cls.return_value = mock_conn
    mock_conn.channel.return_value = mock_channel

    consumer = FeedConsumer()
    mock_channel.start_consuming.side_effect = None

    consumer._connect_and_consume()

    declarations = [
        recorded_call
        for recorded_call in mock_channel.method_calls
        if recorded_call[0] == "exchange_declare"
    ]
    expected_declarations = [
        call.exchange_declare(
            exchange=settings.feed_exchange,
            exchange_type="topic",
            durable=True,
        ),
        call.exchange_declare(
            exchange=settings.parsed_exchange,
            exchange_type="topic",
            durable=True,
        ),
    ]
    assert declarations == expected_declarations
    assert mock_channel.method_calls.index(
        declarations[-1]
    ) < mock_channel.method_calls.index(call.start_consuming())

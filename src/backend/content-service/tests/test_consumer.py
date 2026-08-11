from unittest.mock import MagicMock

from src.services.consumer import FeedConsumer


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

import json
from unittest.mock import MagicMock, call, patch

import pika
import pytest

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


@patch("src.adapters.feed_consumer.BlockingConnection")
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
        call.exchange_declare(
            exchange=settings.failed_exchange,
            exchange_type="direct",
            durable=True,
        ),
    ]
    assert declarations == expected_declarations
    assert mock_channel.method_calls.index(
        declarations[-1]
    ) < mock_channel.method_calls.index(call.start_consuming())
    mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)
    mock_channel.confirm_delivery.assert_called_once()
    mock_channel.queue_declare.assert_any_call(
        queue=settings.feed_dlq, durable=True
    )
    mock_channel.queue_bind.assert_any_call(
        queue=settings.feed_dlq,
        exchange=settings.failed_exchange,
        routing_key="feed.failed",
    )
    assert (
        mock_connection_cls.call_args.args[0].blocked_connection_timeout
        == settings.blocked_timeout_seconds
    )
    mock_conn.close.assert_called_once()


def test_consumer_services_io_without_waiting() -> None:
    consumer = FeedConsumer()
    consumer._connection = MagicMock(is_open=True)
    consumer._service_connection()
    consumer._connection.process_data_events.assert_called_once_with(
        time_limit=0
    )


def test_consumer_does_not_use_closed_connection() -> None:
    consumer = FeedConsumer()
    consumer._connection = MagicMock(is_open=False)
    with pytest.raises(pika.exceptions.ConnectionWrongStateError):
        consumer._service_connection()


def test_consumer_acknowledges_only_after_processing_and_session_cleanup() -> (
    None
):
    consumer = FeedConsumer()
    channel = MagicMock(is_open=True)
    method = MagicMock(delivery_tag=7)
    order: list[str] = []
    with (
        patch("src.adapters.feed_consumer.SessionLocal") as session,
        patch("src.adapters.feed_consumer.SourceProcessorService") as service,
    ):
        service.return_value.process.side_effect = lambda *args, **kwargs: (
            order.append("process")
        )
        session.return_value.close.side_effect = lambda: order.append("close")
        channel.basic_ack.side_effect = lambda **kwargs: order.append("ack")
        consumer._on_message(
            channel,
            method,
            None,
            b'{"event_type":"feed.raw_fetched.v1"}',
        )
        service.return_value.process.assert_called_once_with(
            channel,
            {"event_type": "feed.raw_fetched.v1"},
            on_progress=consumer._service_connection,
        )
    assert order == ["process", "close", "ack"]
    channel.basic_nack.assert_not_called()


def test_invalid_message_is_rejected_without_requeue() -> None:
    channel = MagicMock(is_open=True)
    with patch("src.adapters.feed_consumer.SessionLocal"):
        FeedConsumer()._on_message(
            channel, MagicMock(delivery_tag=7), None, b"not JSON"
        )
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=7, requeue=False)


def test_processing_failure_is_rejected_without_ack() -> None:
    channel = MagicMock(is_open=True)
    with (
        patch("src.adapters.feed_consumer.SessionLocal") as session,
        patch("src.adapters.feed_consumer.SourceProcessorService") as service,
    ):
        service.return_value.process.side_effect = RuntimeError(
            "Database unavailable"
        )
        FeedConsumer()._on_message(
            channel,
            MagicMock(delivery_tag=7),
            None,
            json.dumps({}).encode(),
        )
        session.return_value.close.assert_called_once()
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=7, requeue=False)


def test_closed_channel_failure_propagates_for_broker_redelivery() -> None:
    channel = MagicMock(is_open=False)
    with (
        patch("src.adapters.feed_consumer.SessionLocal"),
        patch("src.adapters.feed_consumer.SourceProcessorService") as service,
    ):
        service.return_value.process.side_effect = RuntimeError(
            "Channel closed"
        )
        with pytest.raises(RuntimeError, match="Channel closed"):
            FeedConsumer()._on_message(
                channel, MagicMock(delivery_tag=7), None, b"{}"
            )
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_not_called()

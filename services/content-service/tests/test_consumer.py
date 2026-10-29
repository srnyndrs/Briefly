import json
from unittest.mock import MagicMock, call, patch

import pytest
from pika.exceptions import ConnectionWrongStateError
from sqlalchemy.exc import InterfaceError, OperationalError, TimeoutError

from src.adapters.feed_consumer import FeedConsumer
from src.config.message_broker import publisher_channel
from src.config.settings import settings


@patch("src.adapters.feed_consumer.BlockingConnection")
def test_consumer_startup_configures_exchanges_queues_and_confirms(
    mock_connection_cls: MagicMock,
) -> None:
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_connection_cls.return_value = mock_conn
    mock_conn.channel.return_value = mock_channel

    consumer = FeedConsumer(MagicMock())
    assert not consumer.is_consuming

    def consume():
        assert consumer.is_consuming
        consumer.stop()
        assert not consumer.is_consuming

    mock_channel.start_consuming.side_effect = consume

    consumer._connect_and_consume()
    assert not consumer.is_consuming

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
    assert all(declaration in declarations for declaration in expected_declarations)
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
    mock_channel.queue_bind.assert_any_call(
        queue=settings.feed_queue,
        exchange=settings.feed_exchange,
        routing_key="feed.raw_fetched.v1",
    )


def test_consumer_acknowledges_only_after_processing_and_session_cleanup() -> None:
    processor_factory = MagicMock()
    processor = processor_factory.return_value
    session_context = MagicMock()
    db = MagicMock()
    session_context.__enter__.return_value = db
    channel = MagicMock(is_open=True)
    method = MagicMock(delivery_tag=7)
    order: list[str] = []
    consumer = FeedConsumer(processor_factory)
    session_context.__exit__.side_effect = lambda *args: order.append("close")
    with patch(
        "src.adapters.feed_consumer.SessionLocal",
        return_value=session_context,
    ):
        processor.process.side_effect = lambda *args, **kwargs: order.append(
            "process"
        )
        channel.basic_ack.side_effect = lambda **kwargs: order.append("ack")
        consumer._on_message(
            channel,
            method,
            None,
            b'{"event_type":"feed.raw_fetched.v1"}',
        )
        processor_factory.assert_called_once_with(db)
        processor.process.assert_called_once_with(
            channel,
            {"event_type": "feed.raw_fetched.v1"},
            on_progress=consumer._service_connection,
        )
    session_context.__exit__.assert_called_once()
    assert order == ["process", "close", "ack"]
    channel.basic_nack.assert_not_called()


def test_invalid_message_is_rejected_without_requeue() -> None:
    channel = MagicMock(is_open=True)
    with patch("src.adapters.feed_consumer.SessionLocal"):
        FeedConsumer(MagicMock())._on_message(
            channel, MagicMock(delivery_tag=7), None, b"not JSON"
        )
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=7, requeue=False)


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("processing failed"),
        OperationalError("query", {}, RuntimeError("unavailable")),
        InterfaceError("query", {}, RuntimeError("connection closed")),
        TimeoutError("pool unavailable"),
    ],
)
def test_processing_failure_preserves_transient_deliveries(error) -> None:
    channel = MagicMock(is_open=True)
    processor_factory = MagicMock()
    session_context = MagicMock()
    session_context.__enter__.return_value = MagicMock()
    processor_factory.return_value.process.side_effect = error
    with (
        patch(
            "src.adapters.feed_consumer.SessionLocal",
            return_value=session_context,
        ),
    ):
        consumer = FeedConsumer(processor_factory)
        if isinstance(error, RuntimeError):
            consumer._on_message(
                channel, MagicMock(delivery_tag=7), None, json.dumps({}).encode()
            )
        else:
            with pytest.raises(type(error)):
                consumer._on_message(
                    channel,
                    MagicMock(delivery_tag=7),
                    None,
                    json.dumps({}).encode(),
                )
        session_context.__exit__.assert_called_once()
    channel.basic_ack.assert_not_called()
    if isinstance(error, RuntimeError):
        channel.basic_nack.assert_called_once_with(delivery_tag=7, requeue=False)
    else:
        channel.basic_nack.assert_not_called()


@pytest.mark.parametrize(
    "stop_timing",
    ["before_progress", "during_progress", "during_connect", "during_subscribe"],
)
def test_stop_prevents_new_deliveries_and_interrupts_feed_progress(
    stop_timing,
) -> None:
    factory = MagicMock()
    consumer = FeedConsumer(factory)
    connection = MagicMock(is_open=True)
    if stop_timing in ("during_connect", "during_subscribe"):

        def connect(params):
            if stop_timing == "during_connect":
                consumer.stop()
            return connection

        connection.channel.return_value.basic_consume.side_effect = lambda **_: (
            consumer.stop()
        )
        with patch(
            "src.adapters.feed_consumer.BlockingConnection", side_effect=connect
        ):
            consumer._connect_and_consume()
        connection.close.assert_called_once_with()
        connection.channel.return_value.start_consuming.assert_not_called()
    elif stop_timing == "before_progress":
        consumer._connection = connection
        consumer.stop()
    else:
        consumer._connection = connection
        connection.process_data_events.side_effect = lambda **_: consumer.stop()
    with pytest.raises(ConnectionWrongStateError, match="stopping"):
        consumer._service_connection()
    channel = MagicMock(is_open=True)
    consumer._on_message(channel, MagicMock(delivery_tag=7), None, b"{}")
    factory.assert_not_called()
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_not_called()


def test_closed_channel_failure_propagates_for_broker_redelivery() -> None:
    channel = MagicMock(is_open=False)
    processor_factory = MagicMock()
    processor_factory.return_value.process.side_effect = RuntimeError(
        "Channel closed"
    )
    with (
        patch("src.adapters.feed_consumer.SessionLocal"),
    ):
        with pytest.raises(RuntimeError, match="Channel closed"):
            FeedConsumer(processor_factory)._on_message(
                channel, MagicMock(delivery_tag=7), None, b"{}"
            )
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_not_called()


@patch("src.config.message_broker.pika.BlockingConnection")
def test_replay_publisher_declares_parsed_exchange_and_enables_confirms(
    mock_connection_cls: MagicMock,
) -> None:
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection_cls.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel

    with publisher_channel(exchange=settings.parsed_exchange) as channel:
        assert channel is mock_channel

    mock_channel.exchange_declare.assert_called_once_with(
        exchange=settings.parsed_exchange,
        exchange_type="topic",
        durable=True,
    )
    mock_channel.confirm_delivery.assert_called_once()
    mock_connection.close.assert_called_once_with()

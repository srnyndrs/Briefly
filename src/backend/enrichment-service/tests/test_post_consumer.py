import json
from unittest.mock import MagicMock, call, patch

import pytest

from src.adapters.post_consumer import PostConsumer
from src.config.settings import settings


def test_declares_durable_isolated_queue_and_dead_letter_route() -> None:
    channel = MagicMock()

    PostConsumer._declare_topology(channel)

    channel.exchange_declare.assert_has_calls(
        [
            call(
                exchange=settings.parsed_exchange,
                exchange_type="topic",
                durable=True,
            ),
            call(
                exchange=settings.failed_exchange,
                exchange_type="direct",
                durable=True,
            ),
            call(
                exchange=settings.result_exchange,
                exchange_type="topic",
                durable=True,
            ),
        ]
    )
    channel.queue_declare.assert_any_call(
        queue=settings.post_queue,
        durable=True,
        arguments={
            "x-dead-letter-exchange": settings.failed_exchange,
            "x-dead-letter-routing-key": settings.post_failed_routing_key,
        },
    )
    channel.queue_bind.assert_any_call(
        queue=settings.post_queue,
        exchange=settings.parsed_exchange,
        routing_key="post.parsed.v1",
    )
    channel.queue_bind.assert_any_call(
        queue=settings.post_dlq,
        exchange=settings.failed_exchange,
        routing_key=settings.post_failed_routing_key,
    )
    channel.queue_bind.assert_any_call(
        queue=settings.result_queue,
        exchange=settings.result_exchange,
        routing_key="post.enriched.v2",
    )


@patch("src.adapters.post_consumer.pika.BlockingConnection")
def test_connection_uses_prefetch_one_and_durable_queue(
    connection_class: MagicMock,
) -> None:
    connection = MagicMock(is_open=True)
    channel = MagicMock(is_open=True)
    connection_class.return_value = connection
    connection.channel.return_value = channel
    consumer = PostConsumer(lambda _event, _channel: None)

    consumer._connect_and_consume()

    channel.basic_qos.assert_called_once_with(prefetch_count=1)
    channel.confirm_delivery.assert_called_once()
    channel.basic_consume.assert_called_once_with(
        queue=settings.post_queue,
        on_message_callback=consumer._on_message,
    )
    channel.start_consuming.assert_called_once()
    connection.close.assert_called_once()
    assert (
        connection_class.call_args.args[0].blocked_connection_timeout
        == settings.blocked_timeout_seconds
    )


def test_message_is_acknowledged_only_after_processing() -> None:
    order: list[str] = []
    processor = MagicMock(
        side_effect=lambda _event, _channel: order.append("processed")
    )
    channel = MagicMock(is_open=True)
    channel.basic_ack.side_effect = lambda **_: order.append("ack")
    consumer = PostConsumer(processor)
    event = {"event_type": "post.parsed.v1"}

    consumer._on_message(
        channel,
        MagicMock(delivery_tag=9),
        None,
        json.dumps(event).encode(),
    )

    assert order == ["processed", "ack"]
    processor.assert_called_once_with(event, channel)
    channel.basic_ack.assert_called_once_with(delivery_tag=9)
    channel.basic_nack.assert_not_called()


@pytest.mark.parametrize(
    ("body", "expected_processor_calls"),
    [(b"not-json", 0), (b"{}", 1)],
)
def test_invalid_message_is_dead_lettered_without_requeue(
    body: bytes,
    expected_processor_calls: int,
) -> None:
    channel = MagicMock(is_open=True)

    def validate(event: object, _channel: object) -> None:
        if (
            not isinstance(event, dict)
            or event.get("event_type") != "post.parsed.v1"
        ):
            raise ValueError("invalid parsed post event")

    processor = MagicMock(side_effect=validate)

    PostConsumer(processor)._on_message(
        channel,
        MagicMock(delivery_tag=10),
        None,
        body,
    )

    assert processor.call_count == expected_processor_calls
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(
        delivery_tag=10,
        requeue=False,
    )


def test_processing_failure_is_dead_lettered_without_requeue() -> None:
    channel = MagicMock(is_open=True)
    processor = MagicMock(side_effect=RuntimeError("database unavailable"))

    PostConsumer(processor)._on_message(
        channel,
        MagicMock(delivery_tag=11),
        None,
        b'{"event_type":"post.parsed.v1"}',
    )

    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(
        delivery_tag=11,
        requeue=False,
    )


def test_stopping_consumer_requests_thread_safe_shutdown() -> None:
    consumer = PostConsumer(lambda _event, _channel: None)
    connection = MagicMock(is_open=True)
    consumer._connection = connection

    consumer.stop()

    assert consumer._stop_event.is_set()
    connection.add_callback_threadsafe.assert_called_once_with(
        consumer._safe_stop_consuming
    )


def test_consumer_reconnects_with_backoff_after_connection_failure() -> None:
    consumer = PostConsumer(lambda _event, _channel: None)
    attempts = 0

    def connect_once_then_stop() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("RabbitMQ unavailable")
        consumer._stop_event.set()

    with (
        patch.object(consumer, "_connect_and_consume", connect_once_then_stop),
        patch.object(consumer._stop_event, "wait", return_value=False) as wait,
    ):
        consumer.run()

    assert attempts == 2
    wait.assert_called_once_with(1)

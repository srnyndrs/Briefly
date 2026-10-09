import threading
from collections import deque
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pika.exceptions import ConnectionWrongStateError

from src.adapters.post_consumer import PostConsumer
from src.config.settings import settings
from src.repositories.enrichment_repository import StoredEnrichment


def result(*, pending=False, status="completed"):
    return StoredEnrichment(
        post_id=uuid4(),
        input_hash="a" * 64,
        enrichment_version="test",
        category_ids=("science",) if status == "completed" else (),
        status=status,
        reason=None,
        processed_at=datetime.now(UTC),
        publication_pending=pending,
        event_id="saved-event",
        result_event={"event_id": "saved-event"},
    )


def test_declares_only_input_and_dead_letter_queues():
    channel = MagicMock()
    PostConsumer._declare_topology(channel)
    assert {
        c.kwargs["queue"] for c in channel.queue_declare.call_args_list
    } == {
        settings.post_queue,
        settings.post_dlq,
    }
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
    assert all(
        c.kwargs["routing_key"] != "post.enriched.v2"
        for c in channel.queue_bind.call_args_list
    )


@patch("src.adapters.post_consumer.pika.BlockingConnection")
def test_connection_uses_prefetch_one_and_confirms(connection_class):
    connection = MagicMock(is_open=True)
    channel = MagicMock(is_open=True)
    connection_class.return_value = connection
    connection.channel.return_value = channel
    consumer = PostConsumer(MagicMock())
    consumer._connect_and_consume()
    channel.basic_qos.assert_called_once_with(prefetch_count=1)
    channel.confirm_delivery.assert_called_once()
    channel.start_consuming.assert_called_once()
    connection.close.assert_called_once()
    assert consumer._connection is None
    assert (
        connection_class.call_args.args[0].blocked_connection_timeout
        == settings.blocked_timeout_seconds
    )


def test_process_and_mark_run_off_broker_thread(deliver):
    broker_thread = threading.get_ident()
    order = []
    saved = result(pending=True)
    processor = MagicMock()

    def process(event):
        assert threading.get_ident() != broker_thread
        order.append("saved")
        return saved

    def publish(value, channel):
        assert threading.get_ident() == broker_thread
        order.append("confirmed")

    def mark(value):
        assert threading.get_ident() != broker_thread
        order.append("marked")
        return replace(value, publication_pending=False)

    processor.side_effect = process
    processor.publish.side_effect = publish
    processor.mark_published.side_effect = mark
    channel = MagicMock(is_open=True)
    channel.basic_ack.side_effect = lambda **_: order.append("ack")
    deliver(processor, channel, b"{}", 9)
    assert order == ["saved", "confirmed", "marked", "ack"]
    processor.assert_called_once_with({})


@pytest.mark.parametrize(
    "body,error",
    [
        (b"not-json", None),
        (b"{}", ValueError("invalid")),
        (b"{}", RuntimeError("database unavailable")),
    ],
)
def test_invalid_delivery_is_dead_lettered(deliver, body, error):
    processor = MagicMock(side_effect=error)
    channel = MagicMock(is_open=True)
    deliver(processor, channel, body, 10)
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=10, requeue=False)


def test_failed_saved_event_is_published_before_reject(deliver):
    saved = result(pending=True, status="failed")
    processor = MagicMock(return_value=saved)
    processor.mark_published.return_value = replace(
        saved, publication_pending=False
    )
    channel = MagicMock(is_open=True)
    deliver(processor, channel, b"{}", 11)
    processor.publish.assert_called_once_with(saved, channel)
    processor.mark_published.assert_called_once_with(saved)
    channel.basic_nack.assert_called_once_with(delivery_tag=11, requeue=False)
    channel.basic_ack.assert_not_called()


@pytest.mark.parametrize("phase", ["publish", "mark_published"])
def test_publication_failure_does_not_ack(deliver, phase):
    saved = result(pending=True)
    processor = MagicMock(return_value=saved)
    getattr(processor, phase).side_effect = RuntimeError("failed")
    channel = MagicMock(is_open=True)
    deliver(processor, channel, b"{}")
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


@pytest.mark.parametrize("disconnect", ["closed", "replaced", "shutdown"])
def test_slow_worker_completion_cannot_touch_closed_or_replaced_channel(
    disconnect,
):
    entered = threading.Event()
    release = threading.Event()
    callbacks = deque()

    def slow(event):
        entered.set()
        assert release.wait(2)
        return result(pending=True)

    processor = MagicMock(side_effect=slow)
    consumer = PostConsumer(processor)
    connection = MagicMock(is_open=True)
    connection.add_callback_threadsafe.side_effect = callbacks.append
    channel = MagicMock(is_open=True)
    consumer._connection = connection
    consumer._channel = channel
    consumer._on_message(channel, MagicMock(delivery_tag=2), None, b"{}")
    assert entered.wait(1)
    assert not callbacks
    if disconnect == "closed":
        connection.is_open = False
    elif disconnect == "replaced":
        consumer._connection = MagicMock(is_open=True)
    else:
        consumer.stop()
        callbacks.popleft()()
    release.set()
    consumer._worker.join(2)
    while callbacks:
        callbacks.popleft()()
    processor.publish.assert_not_called()
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_not_called()
    assert consumer._worker.daemon


def test_completion_scheduling_handles_closed_connection():
    consumer = PostConsumer(MagicMock(return_value=result()))
    connection = MagicMock()
    connection.add_callback_threadsafe.side_effect = ConnectionWrongStateError()
    consumer._process_delivery(connection, 1, b"{}")


def test_stop_requests_thread_safe_shutdown():
    consumer = PostConsumer(MagicMock())
    connection = MagicMock(is_open=True)
    consumer._connection = connection
    consumer.stop()
    connection.add_callback_threadsafe.assert_called_once_with(
        consumer._safe_stop_consuming
    )
    assert consumer._stop_event.is_set()


def test_reconnect_waits_for_disconnected_worker():
    consumer = PostConsumer(MagicMock())
    worker = MagicMock()
    worker.is_alive.side_effect = [True, False]
    consumer._worker = worker
    with patch.object(
        consumer,
        "_connect_and_consume",
        side_effect=lambda: consumer._stop_event.set(),
    ):
        consumer.run()
    worker.join.assert_called_once_with(timeout=0.1)


def test_consumer_reconnects_with_backoff_after_connection_failure():
    consumer = PostConsumer(MagicMock())
    attempts = 0

    def connect():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("unavailable")
        consumer._stop_event.set()

    with (
        patch.object(consumer, "_connect_and_consume", connect),
        patch.object(consumer._stop_event, "wait", return_value=False) as wait,
    ):
        consumer.run()
    assert attempts == 2
    wait.assert_called_once_with(1)

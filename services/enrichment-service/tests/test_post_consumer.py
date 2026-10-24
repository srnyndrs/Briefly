import threading
from collections import deque
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pika
import pytest

from src.adapters.post_consumer import PostConsumer
from src.config.settings import settings
from src.repositories.stored_enrichment import StoredEnrichment


def result(*, pending=False, status="completed"):
    return StoredEnrichment(
        post_id=uuid4(),
        category_ids=("science",) if status == "completed" else (),
        status=status,
        reason=None,
        processed_at=datetime.now(UTC),
        publication_pending=pending,
        event_id="saved-event",
    )


def test_declares_only_input_and_dead_letter_queues():
    connection = MagicMock(is_open=True)
    channel = connection.channel.return_value
    with patch(
        "src.adapters.post_consumer.BlockingConnection",
        return_value=connection,
    ):
        PostConsumer(MagicMock())._connect_and_consume()
    channel.basic_qos.assert_called_once_with(prefetch_count=1)
    channel.confirm_delivery.assert_called_once()
    channel.queue_declare.assert_any_call(
        queue=settings.post_queue,
        durable=True,
        arguments={
            "x-dead-letter-exchange": settings.failed_exchange,
            "x-dead-letter-routing-key": settings.post_failed_routing_key,
        },
    )
    assert {c.kwargs["queue"] for c in channel.queue_declare.call_args_list} == {
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
        c.kwargs["routing_key"] != "post.enriched.v1"
        for c in channel.queue_bind.call_args_list
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

    processor.process.side_effect = process
    channel = MagicMock(is_open=True)
    channel.basic_publish.side_effect = lambda **_: publish(None, channel)
    processor.mark_published.side_effect = mark
    channel.basic_ack.side_effect = lambda **_: order.append("ack")
    deliver(processor, channel, b"{}", 9)
    assert order == ["saved", "confirmed", "marked", "ack"]
    processor.process.assert_called_once_with({})


@pytest.mark.parametrize(
    "error_type", [pika.exceptions.NackError, pika.exceptions.UnroutableError]
)
def test_publication_failure_leaves_result_pending(deliver, error_type):
    saved = result(pending=True)
    processor = MagicMock()
    processor.process.return_value = saved
    channel = MagicMock(is_open=True)
    channel.basic_publish.side_effect = error_type([])

    deliver(processor, channel, b"{}", 9)

    assert saved.publication_pending is True
    processor.mark_published.assert_not_called()
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=9, requeue=False)


def test_invalid_delivery_is_dead_lettered(deliver):
    processor = MagicMock()
    body = b"not-json"
    channel = MagicMock(is_open=True)
    deliver(processor, channel, body, 10)
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=10, requeue=False)


@pytest.mark.parametrize("disconnect", ["replaced", "shutdown"])
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

    processor = MagicMock()
    processor.process.side_effect = slow
    consumer = PostConsumer(processor)
    connection = MagicMock(is_open=True)
    connection.add_callback_threadsafe.side_effect = callbacks.append
    channel = MagicMock(is_open=True)
    consumer._connection = connection
    consumer._channel = channel
    consumer._on_message(channel, MagicMock(delivery_tag=2), None, b"{}")
    try:
        assert entered.wait(1)
        assert not callbacks
        if disconnect == "replaced":
            consumer._connection = MagicMock(is_open=True)
        else:
            consumer.stop()
            callbacks.popleft()()
    finally:
        release.set()
        consumer._worker.join(2)
    assert not consumer._worker.is_alive()
    while callbacks:
        callbacks.popleft()()
    channel.basic_publish.assert_not_called()
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_not_called()


def test_reconnect_waits_for_disconnected_worker():
    consumer = PostConsumer(MagicMock())
    joined = []
    worker = MagicMock()
    worker.is_alive.side_effect = [True, False]
    worker.join.side_effect = lambda **_: joined.append(True)
    consumer._worker = worker

    def reconnect():
        assert joined
        consumer._stop_event.set()

    with patch.object(
        consumer, "_connect_and_consume", side_effect=reconnect
    ) as connect:
        consumer.run()
    connect.assert_called_once()

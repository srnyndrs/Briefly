"""Opt-in isolated RabbitMQ checks; never replay platform backlog."""

import json
import os
import threading
import time
from uuid import UUID, uuid4

import pika
import pytest

from src.adapters.post_consumer import PostConsumer
from src.config.settings import settings
from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.enrichment import EnrichmentService
from src.services.post_processor import PostEventProcessor
from src.scripts.republish_result import republish_result


def wait_for(check, timeout=12):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("Broker check exceeded its time bound")


@pytest.fixture
def broker(monkeypatch):
    url = os.environ.get("ENRICHMENT_TEST_RABBITMQ_URL")
    if not url:
        pytest.skip("Set ENRICHMENT_TEST_RABBITMQ_URL for broker checks")
    prefix = f"enrichment-test-{uuid4().hex}"
    monkeypatch.setattr(settings, "rabbitmq_url", url + "?heartbeat=2")
    for field in (
        "parsed_exchange",
        "result_exchange",
        "failed_exchange",
        "post_queue",
        "post_dlq",
    ):
        monkeypatch.setattr(settings, field, f"{prefix}.{field}")
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.rabbitmq_url)
    )
    channel = connection.channel()
    PostConsumer._declare_topology(channel)
    channel.confirm_delivery()
    result_queue = f"{prefix}.query"

    def bind():
        channel.queue_declare(queue=result_queue, durable=True)
        channel.queue_bind(
            queue=result_queue,
            exchange=settings.result_exchange,
            routing_key="post.enriched.v2",
        )

    try:
        yield channel, result_queue, bind
    finally:
        for queue in (settings.post_queue, settings.post_dlq, result_queue):
            channel.queue_delete(queue=queue)
        for exchange in (
            settings.parsed_exchange,
            settings.result_exchange,
            settings.failed_exchange,
        ):
            channel.exchange_delete(exchange=exchange)
        connection.close()


def event():
    return {
        "event_id": str(uuid4()),
        "event_type": "post.parsed.v1",
        "correlation_id": "broker-test",
        "payload": {
            "post_id": str(uuid4()),
            "source_id": str(uuid4()),
            "post_revision": 1,
            "item_guid": "one",
            "url": "https://example.com/test",
            "title": "Research report",
        },
    }


def publish(channel, value):
    channel.basic_publish(
        exchange=settings.parsed_exchange,
        routing_key="post.parsed.v1",
        body=json.dumps(value).encode(),
        mandatory=True,
    )


def start(processor, channel):
    consumer = PostConsumer(processor)
    thread = threading.Thread(target=consumer.run, daemon=True)
    thread.start()
    wait_for(
        lambda: (
            channel.queue_declare(
                queue=settings.post_queue, passive=True
            ).method.consumer_count
            == 1
        )
    )
    return consumer, thread


def stop(consumer, thread):
    consumer.stop()
    thread.join(timeout=5)
    assert not thread.is_alive()


def test_live_slow_inference_survives_heartbeat_and_duplicate(
    broker, session_factory
):
    channel, result_queue, bind = broker
    bind()
    calls = []

    def classify(article):
        calls.append(article)
        time.sleep(5)
        return ("science",)

    repository = EnrichmentRepository(session_factory)
    processor = PostEventProcessor(EnrichmentService(repository, classify))
    consumer, thread = start(processor, channel)
    value = event()
    try:
        publish(channel, value)
        delivered = wait_for(
            lambda: channel.basic_get(queue=result_queue, auto_ack=True)[2]
        )
        saved = repository.get_by_post_id(UUID(value["payload"]["post_id"]))
        wait_for(
            lambda: (
                not repository.get_by_post_id(saved.post_id).publication_pending
            )
        )
        assert json.loads(delivered)["event_id"] == saved.event_id
        original_connection = consumer._connection
        # Wait for duplicate settlement on the broker thread.
        settled = threading.Event()
        original_settle = consumer._settle

        def settle(*args):
            original_settle(*args)
            settled.set()

        consumer._settle = settle
        publish(channel, value)
        wait_for(settled.is_set)
        assert len(calls) == 1
        assert consumer._connection is original_connection
        assert original_connection.is_open
    finally:
        stop(consumer, thread)


def test_live_shutdown_redelivers_saved_work(broker, session_factory):
    channel, result_queue, bind = broker
    bind()
    entered, release = threading.Event(), threading.Event()
    calls = []

    def classify(article):
        calls.append(article)
        entered.set()
        assert release.wait(8)
        return ("science",)

    repository = EnrichmentRepository(session_factory)
    processor = PostEventProcessor(EnrichmentService(repository, classify))
    consumer, thread = start(processor, channel)
    try:
        publish(channel, event())
        assert entered.wait(2)
        stop(consumer, thread)
    finally:
        release.set()
        consumer.stop()
        thread.join(5)
        if consumer._worker:
            consumer._worker.join(2)
    restarted, restarted_thread = start(processor, channel)
    try:
        assert wait_for(
            lambda: channel.basic_get(queue=result_queue, auto_ack=True)[2]
        )
        assert len(calls) == 1
    finally:
        stop(restarted, restarted_thread)


def test_live_disconnect_waits_for_worker_and_reuses_saved_result(
    broker, session_factory
):
    channel, result_queue, bind = broker
    bind()
    entered, release = threading.Event(), threading.Event()
    calls = []

    def classify(article):
        calls.append(article)
        entered.set()
        assert release.wait(8)
        return ("science",)

    processor = PostEventProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classify)
    )
    consumer, thread = start(processor, channel)
    try:
        publish(channel, event())
        assert entered.wait(2)
        original_connection = consumer._connection
        original_connection.add_callback_threadsafe(original_connection.close)
        wait_for(lambda: consumer._connection is None)
        release.set()
        delivered = wait_for(
            lambda: channel.basic_get(queue=result_queue, auto_ack=True)[2]
        )
        assert json.loads(delivered)["payload"]["category_ids"] == ["science"]
        assert consumer._connection is not original_connection
        assert len(calls) == 1
    finally:
        release.set()
        stop(consumer, thread)


def test_live_missing_binding_retains_saved_event(
    broker, session_factory, monkeypatch
):
    channel, result_queue, bind = broker
    repository = EnrichmentRepository(session_factory)
    processor = PostEventProcessor(
        EnrichmentService(repository, lambda _: ("science",))
    )
    consumer, thread = start(processor, channel)
    value = event()
    try:
        publish(channel, value)
        assert wait_for(
            lambda: channel.basic_get(queue=settings.post_dlq, auto_ack=True)[2]
        )
        saved = repository.get_by_post_id(UUID(value["payload"]["post_id"]))
        assert saved.publication_pending
        bind()
        monkeypatch.setattr(
            "src.scripts.republish_result.SessionLocal", session_factory
        )
        republish_result(saved.post_id)
        delivered = wait_for(
            lambda: channel.basic_get(queue=result_queue, auto_ack=True)[2]
        )
        assert json.loads(delivered) == saved.result_event
        assert not repository.get_by_post_id(saved.post_id).publication_pending
    finally:
        stop(consumer, thread)

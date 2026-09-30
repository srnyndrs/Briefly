"""Opt-in checks against scripts/rabbitmq/compose.test.yml, never the app broker."""

import json
import os
from pathlib import Path
from time import monotonic, sleep
from unittest.mock import patch

import pika
import pytest
import requests
from sqlalchemy.orm import Session

from src.adapters.feed_consumer import FeedConsumer
from src.config.settings import settings
from src.scripts.replay_failed_feed import replay_failed_feed

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_RABBITMQ_INTEGRATION") != "1",
    reason="Requires the disposable RabbitMQ Compose project",
)


@pytest.fixture
def broker():
    params = pika.ConnectionParameters(
        host="127.0.0.1",
        port=5673,
        heartbeat=2,
        blocked_connection_timeout=settings.blocked_timeout_seconds,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    try:
        channel.exchange_declare(
            exchange=settings.feed_exchange,
            exchange_type="topic",
            durable=True,
        )
        channel.queue_declare(queue=settings.feed_queue, durable=True)
        channel.queue_bind(
            queue=settings.feed_queue,
            exchange=settings.feed_exchange,
            routing_key="feed.raw_fetched.v1",
        )
        channel.queue_purge(queue=settings.feed_queue)
        channel.confirm_delivery()
        channel.basic_publish(
            exchange=settings.feed_exchange,
            routing_key="feed.raw_fetched.v1",
            body=b"before-policy",
            mandatory=True,
        )
        definitions = json.loads(
            (
                Path(__file__).resolve().parents[4]
                / "scripts/rabbitmq/content-dlq.json"
            ).read_text()
        )
        response = requests.post(
            "http://127.0.0.1:15673/api/definitions",
            json=definitions,
            auth=(
                params.credentials.username,
                params.credentials.password,
            ),
            timeout=5,
        )
        response.raise_for_status()
        method, _, body = channel.basic_get(queue=settings.feed_queue)
        assert body == b"before-policy"
        channel.basic_ack(method.delivery_tag)
        channel.queue_purge(queue=settings.feed_dlq)
        channel.exchange_declare(
            exchange=settings.parsed_exchange,
            exchange_type="topic",
            durable=True,
        )
        channel.queue_declare(queue="public-api.query.v1", durable=True)
        channel.queue_bind(
            queue="public-api.query.v1",
            exchange=settings.parsed_exchange,
            routing_key="post.parsed.v1",
        )
        channel.queue_purge(queue="public-api.query.v1")
        yield connection, channel
    finally:
        if connection.is_open:
            connection.close()


def _event(xml: str) -> dict:
    return {
        "event_id": "integration-feed",
        "event_type": "feed.raw_fetched.v1",
        "correlation_id": "integration-correlation",
        "payload": {
            "source_id": "00000000-0000-0000-0000-000000000001",
            "source_title": "Example Source",
            "raw_xml": xml,
        },
    }


def _process(connection, channel, db_session: Session, body: bytes) -> None:
    channel.basic_publish(
        exchange=settings.feed_exchange,
        routing_key="feed.raw_fetched.v1",
        body=body,
        mandatory=True,
    )
    method, properties, delivered = channel.basic_get(queue=settings.feed_queue)
    assert method is not None
    consumer = FeedConsumer()
    consumer._connection = connection
    with patch(
        "src.adapters.feed_consumer.SessionLocal",
        return_value=db_session,
    ):
        consumer._on_message(channel, method, properties, delivered)


def _get(channel, queue: str):
    deadline = monotonic() + 3
    while monotonic() < deadline:
        method, properties, body = channel.basic_get(queue=queue, auto_ack=True)
        if method:
            return properties, body
        channel.connection.sleep(0.05)
    pytest.fail(f"No delivery on {queue}")


def test_rejected_feeds_reach_dlq_with_original_body(
    broker, db_session: Session
) -> None:
    connection, channel = broker
    body = json.dumps(_event("<html>Not a feed</html>")).encode()
    _process(connection, channel, db_session, body)
    properties, rejected = _get(channel, settings.feed_dlq)
    assert rejected == body
    assert properties.headers["x-death"][0]["reason"] == "rejected"
    assert (
        channel.queue_declare(
            queue=settings.feed_queue, passive=True
        ).method.message_count
        == 0
    )


def test_guarded_dlq_replay_preserves_original_body_and_correlation(
    broker, db_session: Session
) -> None:
    connection, channel = broker
    body = json.dumps(_event("<html>Not a feed</html>")).encode()
    _process(connection, channel, db_session, body)
    deadline = monotonic() + 3
    while (
        channel.queue_declare(
            queue=settings.feed_dlq, passive=True
        ).method.message_count
        == 0
    ):
        assert monotonic() < deadline
        connection.sleep(0.05)
    with pytest.raises(ValueError, match="does not match"):
        replay_failed_feed(channel, "wrong-event")
    assert replay_failed_feed(channel, "integration-feed")
    _, replayed = _get(channel, settings.feed_queue)
    assert replayed == body
    assert json.loads(replayed)["correlation_id"] == "integration-correlation"
    assert (
        channel.queue_declare(
            queue=settings.feed_dlq, passive=True
        ).method.message_count
        == 0
    )


def test_blocked_articles_complete_across_heartbeat_intervals(
    broker, db_session: Session
) -> None:
    connection, channel = broker
    items = "".join(
        f"<item><guid>item-{index}</guid><link>https://example.com/{index}</link><title>RSS title</title></item>"
        for index in range(7)
    )

    def blocked_article(url: str) -> dict:
        sleep(0.75)
        return {"error": "ArticleException"}

    with patch(
        "src.adapters.content_extractor.extract_article",
        side_effect=blocked_article,
    ):
        _process(
            connection,
            channel,
            db_session,
            json.dumps(
                _event(f"<rss><channel>{items}</channel></rss>")
            ).encode(),
        )

    assert connection.is_open
    assert (
        channel.queue_declare(
            queue=settings.feed_dlq, passive=True
        ).method.message_count
        == 0
    )
    assert (
        channel.queue_declare(
            queue="public-api.query.v1", passive=True
        ).method.message_count
        == 7
    )
    _, published = _get(channel, "public-api.query.v1")
    assert json.loads(published)["payload"]["title"] == "RSS title"


def test_unroutable_publication_dead_letters_feed_and_replay_reuses_post(
    broker, db_session: Session
) -> None:
    connection, channel = broker
    channel.queue_unbind(
        queue="public-api.query.v1",
        exchange=settings.parsed_exchange,
        routing_key="post.parsed.v1",
    )
    event = _event(
        "<rss><channel><item><guid>replay</guid><link>https://example.com/replay</link><title>RSS title</title></item></channel></rss>"
    )
    with patch(
        "src.adapters.content_extractor.extract_article",
        return_value={"content": "Body"},
    ) as extract:
        _process(connection, channel, db_session, json.dumps(event).encode())
        _, rejected = _get(channel, settings.feed_dlq)
        assert (
            json.loads(rejected)["correlation_id"] == "integration-correlation"
        )
        extract.reset_mock()
        channel.queue_bind(
            queue="public-api.query.v1",
            exchange=settings.parsed_exchange,
            routing_key="post.parsed.v1",
        )
        _process(connection, channel, db_session, rejected)
        extract.assert_not_called()
    _, published = _get(channel, "public-api.query.v1")
    assert json.loads(published)["payload"]["content"] == "Body"
    assert (
        channel.queue_declare(
            queue=settings.feed_queue, passive=True
        ).method.message_count
        == 0
    )
    assert (
        channel.queue_declare(
            queue=settings.feed_dlq, passive=True
        ).method.message_count
        == 0
    )

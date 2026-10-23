import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.query_projector import QueryProjector
from src.config.settings import settings
from src.models.read_models import (
    PostEnrichmentProjection,
    PostProjection,
    ProcessedEvent,
    UserPreferencesProjection,
)


class RecordingChannel:
    def __init__(self, on_ack=lambda: None):
        self.acknowledged = []
        self.rejected = []
        self.on_ack = on_ack

    def basic_ack(self, *, delivery_tag):
        self.on_ack()
        self.acknowledged.append(delivery_tag)

    def basic_nack(self, *, delivery_tag, requeue):
        self.rejected.append((delivery_tag, requeue))


def _post_event():
    return {
        "event_id": "parsed-1",
        "event_type": "post.parsed.v1",
        "payload": {
            "post_id": "post-1",
            "post_revision": 2,
            "source_id": "source-1",
            "source_title": "Publisher",
            "title": "Article",
            "content": "Body",
            "keywords": [],
            "published_at": None,
            "url": "https://example.com/post-1",
            "description": None,
            "category": "Publisher label",
            "author": None,
            "language": "en",
            "image_url": None,
        },
    }


def test_duplicate_delivery_and_dispatch_commit_before_ack(session_factory):
    def check_committed():
        with session_factory() as db:
            assert db.get(ProcessedEvent, "parsed-1") is not None
            assert db.get(PostProjection, "post-1").content == "Body"

    channel = RecordingChannel(check_committed)
    projector = QueryProjector(session_factory)
    event = _post_event()
    for tag in (1, 2):
        projector._on_message(
            channel,
            SimpleNamespace(delivery_tag=tag),
            None,
            json.dumps(event).encode(),
        )
    with session_factory() as db:
        assert db.query(ProcessedEvent).count() == 1
        assert db.query(PostProjection).count() == 1
        # A duplicate must not apply the handler again.
        db.get(PostProjection, "post-1").title = "Already projected"
        db.commit()
    projector._on_message(
        channel,
        SimpleNamespace(delivery_tag=3),
        None,
        json.dumps(event).encode(),
    )
    with session_factory() as db:
        assert db.get(PostProjection, "post-1").title == "Already projected"

    enrichment = {
        "event_id": "enriched-1",
        "event_type": "post.enriched.v1",
        "schema_version": 1,
        "payload": {
            "post_id": "post-1",
            "post_revision": 2,
            "enrichment_revision": 1,
            "status": "completed",
            "category_ids": ["science"],
        },
    }
    preferences = {
        "event_id": "preferences-1",
        "event_type": "preferences.updated.v1",
        "payload": {"user_id": "user-1", "languages": ["en"]},
    }
    # Replaying the same content revision keeps matching enrichment.
    event = {**event, "event_id": "parsed-repeat"}
    for tag, envelope in enumerate((enrichment, preferences, event), start=4):
        projector._on_message(
            channel,
            SimpleNamespace(delivery_tag=tag),
            None,
            json.dumps(envelope).encode(),
        )
    with session_factory() as db:
        assert db.get(PostProjection, "post-1").categories == ["science"]
        assert db.get(PostEnrichmentProjection, "post-1").category_ids == [
            "science"
        ]
        assert db.get(UserPreferencesProjection, "user-1").languages == ["en"]
        assert db.query(ProcessedEvent).count() == 4
    assert channel.acknowledged == [1, 2, 3, 4, 5, 6]
    assert channel.rejected == []


def test_commit_failure_rolls_back_projection_and_receipt(session_factory):
    session = session_factory()
    staged = []

    def fail_commit():
        # Both writes have reached the real transaction before it fails.
        session.flush()
        staged.extend(
            [
                session.get(PostProjection, "post-1").post_id,
                session.get(ProcessedEvent, "parsed-1").event_id,
            ]
        )
        raise RuntimeError("commit failed")

    channel = RecordingChannel()
    with patch.object(session, "commit", side_effect=fail_commit) as commit:
        QueryProjector(lambda: session)._on_message(
            channel,
            SimpleNamespace(delivery_tag=1),
            None,
            json.dumps(_post_event()).encode(),
        )
    commit.assert_called_once_with()
    assert staged == ["post-1", "parsed-1"]
    with session_factory() as db:
        assert db.query(PostProjection).count() == 0
        assert db.query(ProcessedEvent).count() == 0
    assert channel.acknowledged == []
    assert channel.rejected == [(1, False)]


def test_query_queue_is_durable_and_binds_all_events():
    connection = MagicMock()
    channel = connection.channel.return_value
    with patch(
        "src.adapters.query_projector.pika.BlockingConnection",
        return_value=connection,
    ):
        QueryProjector(lambda: None)._connect_and_consume()
    channel.queue_declare.assert_called_once_with(
        queue=settings.query_queue, durable=True
    )
    for exchange, key in (
        (settings.account_exchange, "preferences.updated.v1"),
        (settings.content_exchange, "post.parsed.v1"),
        (settings.enrichment_exchange, "post.enriched.v1"),
    ):
        channel.queue_bind.assert_any_call(
            queue=settings.query_queue, exchange=exchange, routing_key=key
        )


def test_projector_closes_connection_when_consumption_fails():
    connection = MagicMock(is_open=True)
    connection.channel.return_value.start_consuming.side_effect = RuntimeError(
        "consume failed"
    )
    with (
        patch(
            "src.adapters.query_projector.pika.BlockingConnection",
            return_value=connection,
        ),
        pytest.raises(RuntimeError, match="consume failed"),
    ):
        QueryProjector(lambda: None)._connect_and_consume()
    connection.close.assert_called_once_with()


def test_invalid_envelope_records_no_receipt_or_projection(session_factory):
    channel = RecordingChannel()
    event = {
        "event_id": "invalid",
        "event_type": "post.enriched.v1",
        "schema_version": True,
        "payload": {
            "post_id": "post-1",
            "post_revision": 1,
            "enrichment_revision": 1,
            "status": "completed",
            "category_ids": ["science"],
        },
    }
    QueryProjector(session_factory)._on_message(
        channel,
        SimpleNamespace(delivery_tag=1),
        None,
        json.dumps(event).encode(),
    )
    assert channel.rejected == [(1, False)]
    assert channel.acknowledged == []
    with session_factory() as db:
        assert db.query(ProcessedEvent).count() == 0
        assert db.query(PostEnrichmentProjection).count() == 0
        assert db.query(PostProjection).count() == 0

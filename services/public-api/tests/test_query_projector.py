import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from pika.exceptions import ConnectionWrongStateError
from sqlalchemy.exc import OperationalError

from src.adapters.query_projector import QueryProjector
from src.config.settings import settings
from src.models.read_models import (
    PostEnrichmentProjection,
    PostProjection,
    ProcessedEvent,
    UserPreferencesProjection,
)

POST_ID = "00000000-0000-0000-0000-000000000001"
SOURCE_ID = "00000000-0000-0000-0000-000000000002"
USER_ID = "00000000-0000-0000-0000-000000000003"


class RecordingChannel:
    is_open = True

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
            "post_id": POST_ID,
            "post_revision": 2,
            "source_id": SOURCE_ID,
            "source_title": "Publisher",
            "title": "Article",
            "content": "Body",
            "keywords": [],
            "published_at": None,
            "url": f"https://example.com/{POST_ID}",
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
            assert db.get(PostProjection, UUID(POST_ID)).content == "Body"

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
        db.get(PostProjection, UUID(POST_ID)).title = "Already projected"
        db.commit()
    projector._on_message(
        channel,
        SimpleNamespace(delivery_tag=3),
        None,
        json.dumps(event).encode(),
    )
    with session_factory() as db:
        assert db.get(PostProjection, UUID(POST_ID)).title == "Already projected"

    enrichment = {
        "event_id": "enriched-1",
        "event_type": "post.enriched.v1",
        "schema_version": 1,
        "payload": {
            "post_id": POST_ID,
            "post_revision": 2,
            "enrichment_revision": 1,
            "status": "completed",
            "category_ids": ["science"],
        },
    }
    preferences = {
        "event_id": "preferences-1",
        "event_type": "preferences.updated.v1",
        "payload": {"user_id": USER_ID, "languages": ["en"]},
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
        assert db.get(PostProjection, UUID(POST_ID)).categories == ["science"]
        assert db.get(PostEnrichmentProjection, UUID(POST_ID)).category_ids == [
            "science"
        ]
        assert db.get(UserPreferencesProjection, UUID(USER_ID)).languages == ["en"]
        assert db.query(ProcessedEvent).count() == 4
    assert channel.acknowledged == [1, 2, 3, 4, 5, 6]
    assert channel.rejected == []


@pytest.mark.parametrize("transient", [False, True])
def test_commit_failure_rolls_back_projection_and_receipt(
    session_factory, transient
):
    session = session_factory()
    staged = []

    def fail_commit():
        # Both writes have reached the real transaction before it fails.
        session.flush()
        staged.extend(
            [
                session.get(PostProjection, UUID(POST_ID)).post_id,
                session.get(ProcessedEvent, "parsed-1").event_id,
            ]
        )
        if transient:
            raise OperationalError("commit", {}, RuntimeError("unavailable"))
        raise RuntimeError("commit failed")

    channel = RecordingChannel()
    with patch.object(session, "commit", side_effect=fail_commit) as commit:
        projector = QueryProjector(lambda: session)
        if transient:
            with pytest.raises(OperationalError):
                projector._on_message(
                    channel,
                    SimpleNamespace(delivery_tag=1),
                    None,
                    json.dumps(_post_event()).encode(),
                )
        else:
            projector._on_message(
                channel,
                SimpleNamespace(delivery_tag=1),
                None,
                json.dumps(_post_event()).encode(),
            )
    commit.assert_called_once_with()
    assert staged == [UUID(POST_ID), "parsed-1"]
    with session_factory() as db:
        assert db.query(PostProjection).count() == 0
        assert db.query(ProcessedEvent).count() == 0
    assert channel.acknowledged == []
    assert channel.rejected == ([] if transient else [(1, False)])
    if transient:
        QueryProjector(session_factory)._on_message(
            channel,
            SimpleNamespace(delivery_tag=2),
            None,
            json.dumps(_post_event()).encode(),
        )
        assert channel.acknowledged == [2]
        with session_factory() as db:
            assert db.query(PostProjection).count() == 1
            assert db.get(ProcessedEvent, "parsed-1") is not None


def test_query_queue_is_durable_and_binds_all_events():
    connection = MagicMock()
    channel = connection.channel.return_value
    projector = QueryProjector(lambda: None)
    assert not projector.is_consuming

    def consume():
        assert projector.is_consuming
        projector.stop()
        assert not projector.is_consuming

    channel.start_consuming.side_effect = consume
    with patch(
        "src.adapters.query_projector.BlockingConnection",
        return_value=connection,
    ) as connect:
        projector._connect_and_consume()
    assert not projector.is_consuming
    parameters = connect.call_args.args[0]
    assert parameters.blocked_connection_timeout == settings.blocked_timeout_seconds
    channel.queue_declare.assert_called_once_with(
        queue=settings.query_queue, durable=True
    )
    for exchange, key in (
        (settings.account_exchange, "preferences.updated.v1"),
        (settings.content_exchange, "post.parsed.v1"),
        (settings.content_exchange, "post.deleted.v1"),
        (settings.enrichment_exchange, "post.enriched.v1"),
    ):
        channel.queue_bind.assert_any_call(
            queue=settings.query_queue, exchange=exchange, routing_key=key
        )


def test_projector_closes_connection_when_consumption_fails():
    connection = MagicMock(is_open=True)
    projector = QueryProjector(lambda: None)

    def consume():
        assert projector.is_consuming
        raise RuntimeError("consume failed")

    connection.channel.return_value.start_consuming.side_effect = consume
    with (
        patch(
            "src.adapters.query_projector.BlockingConnection",
            return_value=connection,
        ),
        pytest.raises(RuntimeError, match="consume failed"),
    ):
        projector._connect_and_consume()
    connection.close.assert_called_once_with()
    assert projector._connection is None
    assert projector._channel is None
    assert not projector.is_consuming


def test_invalid_envelope_records_no_receipt_or_projection(session_factory):
    channel = RecordingChannel()
    event = {
        "event_id": "invalid",
        "event_type": "post.enriched.v1",
        "schema_version": True,
        "payload": {
            "post_id": "not-a-uuid",
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


def test_ack_failure_leaves_committed_event_safe_to_redeliver(session_factory):
    def fail_ack():
        raise ConnectionWrongStateError("closed")

    channel = RecordingChannel(fail_ack)
    projector = QueryProjector(session_factory)
    body = json.dumps(_post_event()).encode()
    with pytest.raises(ConnectionWrongStateError):
        projector._on_message(channel, SimpleNamespace(delivery_tag=1), None, body)
    assert channel.rejected == []
    channel.on_ack = lambda: None
    projector._on_message(channel, SimpleNamespace(delivery_tag=2), None, body)
    with session_factory() as db:
        assert db.query(ProcessedEvent).count() == 1
        assert db.query(PostProjection).count() == 1
    assert channel.acknowledged == [2]
    projector.stop()
    projector._on_message(channel, SimpleNamespace(delivery_tag=3), None, body)
    assert channel.acknowledged == [2]

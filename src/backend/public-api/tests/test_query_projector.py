import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.adapters.query_projector import QueryProjector
from src.config.database import Base
from src.config.settings import settings
from src.models.read_models import PostProjection, ProcessedEvent


class FakeSession:
    def __init__(self) -> None:
        self.receipts: dict[str, ProcessedEvent] = {}
        self.added: list[ProcessedEvent] = []
        self.commits = 0

    def get(self, model, event_id: str):
        assert model is ProcessedEvent
        return self.receipts.get(event_id)

    def add(self, receipt: ProcessedEvent) -> None:
        self.added.append(receipt)
        self.receipts[receipt.event_id] = receipt

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        raise AssertionError("duplicate delivery should not roll back")

    def close(self) -> None:
        pass


class FakeChannel:
    def __init__(self) -> None:
        self.acknowledged: list[int] = []

    def basic_ack(self, *, delivery_tag: int) -> None:
        self.acknowledged.append(delivery_tag)


def test_duplicate_delivery_projects_once_and_acknowledges_both() -> None:
    session = FakeSession()
    projector = QueryProjector(lambda: session)
    applied: list[tuple[str, dict]] = []
    projector._apply_event = lambda db, event_type, payload: applied.append(
        (event_type, payload)
    )
    channel = FakeChannel()
    method = SimpleNamespace(delivery_tag=1)
    body = b'{"event_id":"event-1","event_type":"post.parsed.v1","payload":{"post_id":"post-1"}}'

    projector._on_message(channel, method, None, body)
    method.delivery_tag = 2
    projector._on_message(channel, method, None, body)

    assert applied == [("post.parsed.v1", {"post_id": "post-1"})]
    assert len(session.added) == 1
    assert session.commits == 1
    assert channel.acknowledged == [1, 2]


def test_query_queue_binds_enrichment_results() -> None:
    connection = MagicMock()
    channel = connection.channel.return_value
    projector = QueryProjector(lambda: None)

    with patch(
        "src.adapters.query_projector.pika.BlockingConnection",
        return_value=connection,
    ):
        projector._connect_and_consume()

    channel.queue_bind.assert_any_call(
        queue=settings.query_queue,
        exchange=settings.enrichment_exchange,
        routing_key="post.enriched.v1",
    )


def test_result_event_before_post_is_projected_after_matching_snapshot() -> (
    None
):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, class_=Session, autoflush=False)
    projector = QueryProjector(factory)
    channel = FakeChannel()
    result_event = {
        "event_id": "result-1",
        "event_type": "post.enriched.v1",
        "payload": {
            "post_id": "post-1",
            "post_revision": 2,
            "taxonomy_version": "categories-v1",
            "status": "completed",
            "category_id": "science",
        },
    }
    post_event = {
        "event_id": "post-1-event",
        "event_type": "post.parsed.v1",
        "payload": {
            "post_id": "post-1",
            "post_revision": 2,
            "source_id": "source-1",
            "source_title": "Publisher",
            "url": "https://example.com/post-1",
            "title": "Article",
            "description": None,
            "category": "Publisher label",
            "content": "Body",
            "author": None,
            "language": "en",
            "keywords": [],
            "image_url": None,
            "published_at": None,
        },
    }

    projector._on_message(
        channel,
        SimpleNamespace(delivery_tag=1),
        None,
        json.dumps(result_event).encode(),
    )
    with factory() as db:
        assert db.get(PostProjection, "post-1") is None
    projector._on_message(
        channel,
        SimpleNamespace(delivery_tag=2),
        None,
        json.dumps(post_event).encode(),
    )
    projector._on_message(
        channel,
        SimpleNamespace(delivery_tag=3),
        None,
        json.dumps(result_event).encode(),
    )

    with factory() as db:
        post = db.get(PostProjection, "post-1")
        assert post is not None
        assert post.category == "science"
        assert post.source_category == "Publisher label"
    assert channel.acknowledged == [1, 2, 3]
    engine.dispose()

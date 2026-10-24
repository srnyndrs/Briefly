import json
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.event_publisher import publish_event
from src.config.settings import settings
from src.events.post_enriched import build_enrichment_event
from src.repositories.enrichment_repository import EnrichmentRepository
from src.scripts.republish_result import republish_result
from src.services.classification import ArticleInput
from src.services.enrichment_service import EnrichmentService
from src.services.post_processor import PostProcessor


def process(processor, event, channel):
    saved = processor.process(event)
    if saved.publication_pending:
        publish_event(
            channel,
            exchange=settings.result_exchange,
            envelope=build_enrichment_event(saved),
        )
        saved = processor.mark_published(saved)
    return saved


def test_failed_result_is_published_before_dlq(deliver, session_factory):
    error = ValueError("invalid output")
    repository = EnrichmentRepository(session_factory)
    post_id = str(uuid4())
    first = process(
        PostProcessor(EnrichmentService(repository, lambda _: ("science",))),
        _event(post_id=post_id),
        MagicMock(),
    )

    def fail(_):
        raise error

    processor = PostProcessor(EnrichmentService(repository, fail))
    channel = MagicMock(is_open=True)

    def reject_after_publication(**_):
        channel.basic_publish.assert_called_once()
        stored = repository.get_by_post_id(UUID(post_id))
        assert stored.status == "failed" and not stored.publication_pending

    channel.basic_nack.side_effect = reject_after_publication
    deliver(
        processor,
        channel,
        json.dumps(
            _event(post_id=post_id, revision=2, content="Updated finding")
        ).encode(),
    )
    saved = repository.get_by_post_id(UUID(post_id))
    assert saved.status == "failed" and saved.category_ids == ()
    assert saved.enrichment_revision == first.enrichment_revision + 1
    assert build_enrichment_event(saved)["payload"]["status"] == "failed"
    assert build_enrichment_event(saved)["payload"]["category_ids"] == []
    assert not saved.publication_pending
    published = json.loads(channel.basic_publish.call_args.kwargs["body"])
    assert published["payload"] == {
        "post_id": post_id,
        "post_revision": 2,
        "enrichment_revision": 2,
        "status": "failed",
        "category_ids": [],
    }
    channel.basic_ack.assert_not_called()
    channel.basic_publish.assert_called_once()
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_pending_failed_event_recovers_without_repeating_inference(
    deliver, session_factory
):
    repository = EnrichmentRepository(session_factory)
    classifier = MagicMock(side_effect=ValueError("invalid output"))
    processor = PostProcessor(EnrichmentService(repository, classifier))
    event = _event(post_id=str(uuid4()))
    channel = MagicMock(is_open=True)
    channel.basic_publish.side_effect = RuntimeError("missing binding")
    deliver(processor, channel, json.dumps(event).encode())
    pending = repository.get_by_post_id(UUID(event["payload"]["post_id"]))
    assert pending.status == "failed" and pending.publication_pending
    recovered = process(processor, event, MagicMock(is_open=True))
    assert recovered.event_id == pending.event_id
    assert recovered.enrichment_revision == pending.enrichment_revision
    assert not recovered.publication_pending and classifier.call_count == 1
    classifier.side_effect = None
    classifier.return_value = ("science",)
    assert process(processor, event, MagicMock()).status == "completed"
    assert classifier.call_count == 2


class RecordingClassifier:
    def __init__(self) -> None:
        self.inputs: list[ArticleInput] = []

    def __call__(self, article: ArticleInput) -> tuple[str, ...]:
        self.inputs.append(article)
        return ("science",)


def _event(
    *,
    post_id: str,
    revision: int = 1,
    title: str = "Research report",
    content: str = "New finding",
) -> dict[str, object]:
    return {
        "event_id": "event-1",
        "event_type": "post.parsed.v1",
        "correlation_id": "correlation-1",
        "payload": {
            "post_id": post_id,
            "source_id": "3a202899-d470-423e-a91b-7692f177755e",
            "post_revision": revision,
            "item_guid": "item-1",
            "url": "https://example.com/article",
            "title": title,
            "description": None,
            "content": content,
            "language": "en",
        },
    }


def test_revisions_control_classification_and_saved_identity(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = str(uuid4())
    classifier = RecordingClassifier()
    processor = PostProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )

    channel = MagicMock(is_open=True)
    first = process(processor, _event(post_id=post_id, revision=4), channel)
    duplicate_event = _event(post_id=post_id, revision=4)
    duplicate_event["event_id"] = "different-event-id"
    duplicate_event["force_reclassify"] = True
    duplicate_event["payload"].update(
        content="Conflicting body", force_reclassify=True
    )
    duplicate = process(processor, duplicate_event, channel)
    newer_unchanged = process(
        processor, _event(post_id=post_id, revision=5), channel
    )
    changed_event = _event(
        post_id=post_id, revision=6, content="New medical finding"
    )
    changed_event["payload"].update(
        category="Health", keywords=["medical research"]
    )
    newer_changed = process(processor, changed_event, channel)
    stale_changed = process(
        processor,
        _event(post_id=post_id, revision=3, title="Old report"),
        channel,
    )

    assert first.post_revision == 4
    assert duplicate == first
    assert newer_unchanged.post_revision == 5
    assert newer_unchanged.event_id != first.event_id
    assert newer_unchanged.enrichment_revision == first.enrichment_revision + 1
    assert newer_changed.event_id != newer_unchanged.event_id
    assert (
        newer_changed.enrichment_revision == newer_unchanged.enrichment_revision + 1
    )
    assert stale_changed == newer_changed
    assert len(classifier.inputs) == 3
    assert classifier.inputs[-1].body == "New medical finding"
    assert classifier.inputs[-1].source_category == "Health"
    assert classifier.inputs[-1].keywords == ("medical research",)


def test_consumer_acknowledges_a_saved_parsed_post(
    deliver,
    session_factory: sessionmaker[Session],
) -> None:
    post_id = str(uuid4())
    classifier = RecordingClassifier()
    repository = EnrichmentRepository(session_factory)
    processor = PostProcessor(EnrichmentService(repository, classifier))
    channel = MagicMock(is_open=True)

    def confirm_publication(**kwargs: object) -> bool:
        saved_before_publish = repository.get_by_post_id(UUID(post_id))
        assert saved_before_publish is not None
        assert saved_before_publish.publication_pending
        assert saved_before_publish.event_id is not None
        channel.basic_ack.assert_not_called()
        return True

    channel.basic_publish.side_effect = confirm_publication

    event = _event(post_id=post_id, revision=3)
    event["payload"].update(category="Science", keywords=["study"])
    deliver(
        processor,
        channel,
        json.dumps(event).encode(),
        7,
    )

    saved = repository.get_by_post_id(UUID(post_id))
    assert saved is not None
    assert saved.post_revision == 3
    assert saved.category_ids == ("science",)
    assert not saved.publication_pending
    assert saved.event_id is not None
    result_event = build_enrichment_event(saved)
    assert result_event["event_type"] == "post.enriched.v1"
    assert result_event["schema_version"] == 1
    assert "correlation_id" not in result_event
    assert "trace" not in result_event
    assert result_event["payload"]["post_revision"] == 3
    assert result_event["payload"]["enrichment_revision"] == 1
    assert result_event["payload"]["category_ids"] == ["science"]
    assert set(result_event["payload"]) == {
        "post_id",
        "post_revision",
        "enrichment_revision",
        "status",
        "category_ids",
    }
    assert result_event["occurred_at"] == saved.processed_at.isoformat()
    published_event = json.loads(channel.basic_publish.call_args.kwargs["body"])
    assert published_event == result_event
    assert len(classifier.inputs) == 1
    assert classifier.inputs[0].source_category == "Science"
    assert classifier.inputs[0].keywords == ("study",)
    channel.basic_ack.assert_called_once_with(delivery_tag=7)
    channel.basic_nack.assert_not_called()


def test_failed_publish_reuses_saved_event_after_restart(
    deliver,
    session_factory: sessionmaker[Session],
) -> None:
    post_id = str(uuid4())
    classifier = RecordingClassifier()
    repository = EnrichmentRepository(session_factory)
    processor = PostProcessor(EnrichmentService(repository, classifier))
    event = _event(post_id=post_id, revision=2)
    channel = MagicMock(is_open=True)
    channel.basic_publish.side_effect = RuntimeError("broker did not confirm")

    deliver(processor, channel, json.dumps(event).encode(), 8)

    pending = repository.get_by_post_id(UUID(post_id))
    assert pending is not None and pending.publication_pending
    assert pending.event_id is not None
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=8, requeue=False)

    def no_classifier_call(_: ArticleInput) -> tuple[str, ...]:
        raise AssertionError("saved result should be reused")

    restarted = PostProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), no_classifier_call)
    )
    retry_channel = MagicMock(is_open=True)
    retried = process(restarted, event, retry_channel)

    assert retried.event_id == pending.event_id
    assert retried.enrichment_revision == pending.enrichment_revision
    assert not retried.publication_pending
    retried_event = json.loads(retry_channel.basic_publish.call_args.kwargs["body"])
    assert retried_event == json.loads(
        channel.basic_publish.call_args.kwargs["body"]
    )
    assert retried_event["payload"]["status"] == "completed"
    assert retried_event["payload"]["post_revision"] == 2
    assert retried_event["payload"]["category_ids"] == ["science"]
    assert retried_event["occurred_at"] == pending.processed_at.isoformat()
    assert retried_event["event_id"] == pending.event_id
    assert len(classifier.inputs) == 1

    process(restarted, event, retry_channel)
    assert retry_channel.basic_publish.call_count == 1


def test_save_failure_prevents_publication(
    deliver,
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    processor = PostProcessor(EnrichmentService(repository, RecordingClassifier()))
    channel = MagicMock(is_open=True)

    with patch.object(repository, "save", side_effect=RuntimeError("save failed")):
        deliver(
            processor,
            channel,
            json.dumps(_event(post_id=str(uuid4()))).encode(),
        )

    channel.basic_publish.assert_not_called()
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_explicit_republish_uses_saved_event_without_classifier(
    session_factory: sessionmaker[Session],
    monkeypatch,
) -> None:
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    processor = PostProcessor(EnrichmentService(repository, RecordingClassifier()))
    channel = MagicMock(is_open=True)
    process(processor, _event(post_id=str(post_id)), channel)
    saved = repository.get_by_post_id(post_id)
    assert saved is not None and saved.event_id is not None
    connection = MagicMock(is_open=True)
    connection.channel.return_value = MagicMock(is_open=True)
    with (
        patch("src.scripts.republish_result.SessionLocal", session_factory),
        patch(
            "src.config.message_broker.pika.BlockingConnection",
            return_value=connection,
        ),
    ):
        republish_result(post_id)

    republished = json.loads(
        connection.channel.return_value.basic_publish.call_args.kwargs["body"]
    )
    assert republished == build_enrichment_event(saved)
    connection.channel.return_value.confirm_delivery.assert_called_once()
    connection.close.assert_called_once()
    assert repository.get_by_post_id(post_id) == saved


def test_confirmed_publish_with_failed_completion_can_be_delivered_again(
    deliver, session_factory
):
    repository = EnrichmentRepository(session_factory)
    classifier = MagicMock(return_value=())
    processor = PostProcessor(EnrichmentService(repository, classifier))
    event = _event(post_id=str(uuid4()))
    first_channel = MagicMock(is_open=True)
    with patch.object(repository, "mark_published", side_effect=RuntimeError("db")):
        deliver(processor, first_channel, json.dumps(event).encode())
    pending = repository.get_by_post_id(UUID(event["payload"]["post_id"]))
    assert pending.publication_pending
    first_channel.basic_publish.assert_called_once()
    first_channel.basic_ack.assert_not_called()
    second_channel = MagicMock(is_open=True)
    recovered = process(processor, event, second_channel)
    assert recovered.event_id == pending.event_id
    assert recovered.enrichment_revision == pending.enrichment_revision
    assert not recovered.publication_pending
    assert classifier.call_count == 1
    first_message = json.loads(first_channel.basic_publish.call_args.kwargs["body"])
    second_message = json.loads(
        second_channel.basic_publish.call_args.kwargs["body"]
    )
    assert first_message == second_message
    assert second_message["payload"]["status"] == "abstained"
    assert second_message["payload"]["category_ids"] == []


@pytest.mark.parametrize(
    "event",
    [
        {
            "event_type": "post.parsed.v1",
            "payload": {
                "post_id": "not-a-uuid",
                "source_id": "3a202899-d470-423e-a91b-7692f177755e",
                "post_revision": 1,
                "item_guid": "item-1",
                "url": "https://example.com/article",
                "title": "Title",
            },
        },
        {
            "event_type": "post.parsed.v1",
            "payload": {
                "post_id": "3a202899-d470-423e-a91b-7692f177755e",
                "source_id": "3a202899-d470-423e-a91b-7692f177755e",
                "post_revision": True,
                "item_guid": "item-1",
                "url": "https://example.com/article",
                "title": "Title",
            },
        },
    ],
)
def test_invalid_parsed_post_events_are_rejected(
    event: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    classifier = MagicMock(return_value=("science",))
    processor = PostProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )
    channel = MagicMock(is_open=True)
    with pytest.raises(ValidationError):
        process(processor, event, channel)
    classifier.assert_not_called()
    channel.basic_publish.assert_not_called()

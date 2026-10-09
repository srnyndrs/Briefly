import json
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker


from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.classification import ArticleInput
from src.services.enrichment import EnrichmentService
from src.services.post_processor import PostEventProcessor
from src.scripts.republish_result import republish_result


def process(processor, event, channel):
    saved = processor(event)
    processor.publish(saved, channel)
    return (
        processor.mark_published(saved) if saved.publication_pending else saved
    )


@pytest.mark.parametrize(
    "error", [ValueError("invalid output"), TimeoutError("timed out")]
)
def test_failed_result_is_published_before_dlq(deliver, session_factory, error):
    repository = EnrichmentRepository(session_factory)
    post_id = str(uuid4())
    first = process(
        PostEventProcessor(
            EnrichmentService(repository, lambda _: ("science",))
        ),
        _event(post_id=post_id),
        MagicMock(),
    )

    def fail(_):
        raise error

    processor = PostEventProcessor(EnrichmentService(repository, fail))
    channel = MagicMock(is_open=True)
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
    assert saved.result_event["payload"]["status"] == "failed"
    assert saved.result_event["payload"]["category_ids"] == []
    assert not saved.publication_pending
    channel.basic_publish.assert_called_once()
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_pending_failed_event_recovers_without_repeating_inference(
    deliver, session_factory
):
    repository = EnrichmentRepository(session_factory)
    classifier = MagicMock(side_effect=ValueError("invalid output"))
    processor = PostEventProcessor(EnrichmentService(repository, classifier))
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


def test_duplicate_and_stale_events_do_not_repeat_classification(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = str(uuid4())
    classifier = RecordingClassifier()
    processor = PostEventProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )

    channel = MagicMock(is_open=True)
    first = process(processor, _event(post_id=post_id, revision=4), channel)
    duplicate_event = _event(post_id=post_id, revision=4)
    duplicate_event["event_id"] = "different-event-id"
    duplicate = process(processor, duplicate_event, channel)
    newer_unchanged = process(
        processor, _event(post_id=post_id, revision=5), channel
    )
    stale_changed = process(
        processor,
        _event(post_id=post_id, revision=3, title="Old report"),
        channel,
    )

    assert first.post_revision == 4
    assert duplicate == first
    assert newer_unchanged.post_revision == 5
    assert stale_changed == newer_unchanged
    assert len(classifier.inputs) == 1


def test_consumer_acknowledges_a_saved_parsed_post(
    deliver,
    session_factory: sessionmaker[Session],
) -> None:
    post_id = str(uuid4())
    classifier = RecordingClassifier()
    repository = EnrichmentRepository(session_factory)
    processor = PostEventProcessor(EnrichmentService(repository, classifier))
    channel = MagicMock(is_open=True)

    def confirm_publication(**kwargs: object) -> bool:
        saved_before_publish = repository.get_by_post_id(UUID(post_id))
        assert saved_before_publish is not None
        assert saved_before_publish.publication_pending
        assert saved_before_publish.event_id is not None
        channel.basic_ack.assert_not_called()
        return True

    channel.basic_publish.side_effect = confirm_publication

    deliver(
        processor,
        channel,
        json.dumps(_event(post_id=post_id, revision=3)).encode(),
        7,
    )

    saved = repository.get_by_post_id(UUID(post_id))
    assert saved is not None
    assert saved.post_revision == 3
    assert saved.category_ids == ("science",)
    assert not saved.publication_pending
    assert saved.result_event is not None
    result_event = saved.result_event
    assert result_event["event_type"] == "post.enriched.v2"
    assert result_event["correlation_id"] == "correlation-1"
    assert result_event["payload"]["post_revision"] == 3
    assert result_event["payload"]["enrichment_revision"] == 1
    assert result_event["payload"]["category_ids"] == ["science"]
    assert result_event["payload"]["taxonomy_version"] == "categories-v2"
    published_event = json.loads(channel.basic_publish.call_args.kwargs["body"])
    assert published_event == result_event
    assert len(classifier.inputs) == 1
    channel.basic_ack.assert_called_once_with(delivery_tag=7)
    channel.basic_nack.assert_not_called()


def test_failed_publish_reuses_saved_event_after_restart(
    deliver,
    session_factory: sessionmaker[Session],
) -> None:
    post_id = str(uuid4())
    classifier = RecordingClassifier()
    repository = EnrichmentRepository(session_factory)
    processor = PostEventProcessor(EnrichmentService(repository, classifier))
    event = _event(post_id=post_id, revision=2)
    channel = MagicMock(is_open=True)
    channel.basic_publish.side_effect = RuntimeError("broker did not confirm")

    deliver(processor, channel, json.dumps(event).encode(), 8)

    pending = repository.get_by_post_id(UUID(post_id))
    assert pending is not None and pending.publication_pending
    assert pending.result_event is not None
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=8, requeue=False)

    def no_classifier_call(_: ArticleInput) -> tuple[str, ...]:
        raise AssertionError("saved result should be reused")

    restarted = PostEventProcessor(
        EnrichmentService(
            EnrichmentRepository(session_factory), no_classifier_call
        )
    )
    retry_channel = MagicMock(is_open=True)
    retried = process(restarted, event, retry_channel)

    assert retried.event_id == pending.event_id
    assert retried.enrichment_revision == pending.enrichment_revision
    assert not retried.publication_pending
    assert json.loads(retry_channel.basic_publish.call_args.kwargs["body"]) == (
        pending.result_event
    )
    assert len(classifier.inputs) == 1

    process(restarted, event, retry_channel)
    assert retry_channel.basic_publish.call_count == 1


def test_save_failure_prevents_publication(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    processor = PostEventProcessor(
        EnrichmentService(repository, RecordingClassifier())
    )
    channel = MagicMock(is_open=True)

    with patch.object(
        repository, "save", side_effect=RuntimeError("save failed")
    ):
        with pytest.raises(RuntimeError, match="save failed"):
            process(processor, _event(post_id=str(uuid4())), channel)

    channel.basic_publish.assert_not_called()


def test_explicit_republish_uses_saved_event_without_classifier(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    processor = PostEventProcessor(
        EnrichmentService(repository, RecordingClassifier())
    )
    channel = MagicMock(is_open=True)
    process(processor, _event(post_id=str(post_id)), channel)
    saved = repository.get_by_post_id(post_id)
    assert saved is not None and saved.result_event is not None

    connection = MagicMock(is_open=True)
    connection.channel.return_value = MagicMock(is_open=True)
    with (
        patch("src.scripts.republish_result.SessionLocal", session_factory),
        patch(
            "src.scripts.republish_result.pika.BlockingConnection",
            return_value=connection,
        ),
    ):
        republish_result(post_id)

    republished = json.loads(
        connection.channel.return_value.basic_publish.call_args.kwargs["body"]
    )
    assert republished == saved.result_event
    connection.channel.return_value.confirm_delivery.assert_called_once()
    connection.close.assert_called_once()


def test_existing_result_gets_an_event_without_reclassification(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    EnrichmentService(repository, RecordingClassifier()).enrich_article(
        post_id,
        ArticleInput(
            title="Research report", body="New finding", language="en"
        ),
        post_revision=2,
    )

    def no_classifier_call(_: ArticleInput) -> tuple[str, ...]:
        raise AssertionError("saved classification should be reused")

    processor = PostEventProcessor(
        EnrichmentService(repository, no_classifier_call)
    )
    channel = MagicMock(is_open=True)
    processed = process(
        processor, _event(post_id=str(post_id), revision=2), channel
    )

    assert processed.event_id is not None
    assert not processed.publication_pending
    channel.basic_publish.assert_called_once()


def test_changed_input_at_new_revision_is_classified_again(
    session_factory: sessionmaker[Session],
) -> None:
    classifier = RecordingClassifier()
    processor = PostEventProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )
    post_id = str(uuid4())

    channel = MagicMock(is_open=True)
    first = process(processor, _event(post_id=post_id, revision=1), channel)
    changed = process(
        processor,
        _event(post_id=post_id, revision=2, content="A new finding"),
        channel,
    )

    assert changed.post_revision == 2
    assert changed.input_hash != first.input_hash
    assert len(classifier.inputs) == 2


def test_event_category_and_keywords_reach_classifier_as_hints(
    session_factory: sessionmaker[Session],
) -> None:
    classifier = RecordingClassifier()
    processor = PostEventProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )
    event = _event(post_id=str(uuid4()))
    payload = event["payload"]
    assert isinstance(payload, dict)
    payload["category"] = "Technology"
    payload["keywords"] = ["AI", "Devices"]

    process(processor, event, MagicMock(is_open=True))

    assert classifier.inputs[0].source_category == "Technology"
    assert classifier.inputs[0].keywords == ("AI", "Devices")


def test_changed_source_hints_at_new_revision_are_classified_again(
    session_factory: sessionmaker[Session],
) -> None:
    classifier = RecordingClassifier()
    processor = PostEventProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )
    post_id = str(uuid4())
    first_event = _event(post_id=post_id, revision=1)
    second_event = _event(post_id=post_id, revision=2)
    second_payload = second_event["payload"]
    assert isinstance(second_payload, dict)
    second_payload["keywords"] = ["medical research"]

    first = process(processor, first_event, MagicMock(is_open=True))
    second = process(processor, second_event, MagicMock(is_open=True))

    assert second.input_hash != first.input_hash
    assert len(classifier.inputs) == 2


def test_changed_input_at_same_revision_replaces_saved_snapshot(
    session_factory: sessionmaker[Session],
) -> None:
    classifier = RecordingClassifier()
    processor = PostEventProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )
    post_id = str(uuid4())

    channel = MagicMock(is_open=True)
    first = process(processor, _event(post_id=post_id, revision=2), channel)
    duplicate = process(
        processor,
        _event(post_id=post_id, revision=2, content="Conflicting body"),
        channel,
    )

    assert duplicate.input_hash != first.input_hash
    assert duplicate.enrichment_revision == first.enrichment_revision + 1
    assert first.result_event is not None
    assert duplicate.result_event is not None
    assert duplicate.result_event["event_id"] != first.result_event["event_id"]
    assert duplicate.result_event["payload"]["enrichment_revision"] == 2
    assert len(classifier.inputs) == 2


@pytest.mark.parametrize(
    "event",
    [
        {},
        {"event_type": "post.changed.v1", "payload": {}},
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
    processor = PostEventProcessor(
        EnrichmentService(
            EnrichmentRepository(session_factory), lambda _: ("science",)
        )
    )

    with pytest.raises(ValidationError):
        process(processor, event, MagicMock(is_open=True))

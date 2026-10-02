import json
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.post_consumer import PostConsumer
from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.classification import ArticleInput
from src.services.enrichment import EnrichmentService
from src.services.post_processor import PostEventProcessor


class RecordingClassifier:
    def __init__(self) -> None:
        self.inputs: list[ArticleInput] = []

    def __call__(self, article: ArticleInput) -> str | None:
        self.inputs.append(article)
        return "science"


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

    first = processor(_event(post_id=post_id, revision=4))
    duplicate_event = _event(post_id=post_id, revision=4)
    duplicate_event["event_id"] = "different-event-id"
    duplicate = processor(duplicate_event)
    newer_unchanged = processor(_event(post_id=post_id, revision=5))
    stale_changed = processor(
        _event(post_id=post_id, revision=3, title="Old report")
    )

    assert first.post_revision == 4
    assert duplicate == first
    assert newer_unchanged.post_revision == 5
    assert stale_changed == newer_unchanged
    assert len(classifier.inputs) == 1


def test_consumer_acknowledges_a_saved_parsed_post(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = str(uuid4())
    classifier = RecordingClassifier()
    repository = EnrichmentRepository(session_factory)
    processor = PostEventProcessor(EnrichmentService(repository, classifier))
    channel = MagicMock(is_open=True)

    PostConsumer(processor)._on_message(
        channel,
        MagicMock(delivery_tag=7),
        None,
        json.dumps(_event(post_id=post_id, revision=3)).encode(),
    )

    saved = repository.get_by_post_id(UUID(post_id))
    assert saved is not None
    assert saved.post_revision == 3
    assert saved.category_id == "science"
    assert len(classifier.inputs) == 1
    channel.basic_ack.assert_called_once_with(delivery_tag=7)
    channel.basic_nack.assert_not_called()


def test_changed_input_at_new_revision_is_classified_again(
    session_factory: sessionmaker[Session],
) -> None:
    classifier = RecordingClassifier()
    processor = PostEventProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )
    post_id = str(uuid4())

    first = processor(_event(post_id=post_id, revision=1))
    changed = processor(
        _event(post_id=post_id, revision=2, content="A new finding")
    )

    assert changed.post_revision == 2
    assert changed.input_hash != first.input_hash
    assert len(classifier.inputs) == 2


def test_conflicting_duplicate_revision_keeps_first_saved_snapshot(
    session_factory: sessionmaker[Session],
) -> None:
    classifier = RecordingClassifier()
    processor = PostEventProcessor(
        EnrichmentService(EnrichmentRepository(session_factory), classifier)
    )
    post_id = str(uuid4())

    first = processor(_event(post_id=post_id, revision=2))
    duplicate = processor(
        _event(post_id=post_id, revision=2, content="Conflicting body")
    )

    assert duplicate == first
    assert len(classifier.inputs) == 1


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
            EnrichmentRepository(session_factory), lambda _: "science"
        )
    )

    with pytest.raises(ValidationError):
        processor(event)

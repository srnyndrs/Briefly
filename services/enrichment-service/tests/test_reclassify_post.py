import json
from io import BytesIO
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.repositories.enrichment_repository import EnrichmentRepository
from src.scripts import reclassify_post as command
from src.scripts import republish_result as publication
from src.services.classification import ArticleInput
from src.services.enrichment_service import (
    EnrichmentService,
    ReclassificationConflict,
)


@pytest.fixture
def operation(monkeypatch, session_factory):
    post_id = uuid4()
    payload = {
        "post_id": str(post_id),
        "source_id": str(uuid4()),
        "post_revision": 7,
        "item_guid": "one",
        "url": "https://example.com/one",
        "title": "Research",
        "description": "New study",
        "content": "Finding",
        "language": "en",
        "category": "Science",
        "keywords": ["study"],
    }
    opener = MagicMock(
        side_effect=lambda *a, **k: BytesIO(json.dumps(payload).encode())
    )
    monkeypatch.setattr(command, "urlopen", opener)
    monkeypatch.setattr(command, "SessionLocal", session_factory)
    repository = EnrichmentRepository(session_factory)
    classifier = MagicMock(return_value=("science",))
    service = EnrichmentService(repository, classifier)
    monkeypatch.setattr(command, "create_enrichment_service", lambda: service)
    connection = MagicMock(is_open=True)
    monkeypatch.setattr(
        publication.pika, "BlockingConnection", lambda _: connection
    )
    return post_id, payload, opener, repository, classifier, connection


def test_command_fetches_canonical_snapshot_and_reclassifies_without_deleting(
    operation,
):
    post_id, payload, opener, repository, classifier, connection = operation
    first = command.reclassify_post(post_id, "http://content:8002/")
    second = command.reclassify_post(post_id, "http://content:8002/")
    opener.assert_called_with(
        f"http://content:8002/posts/{post_id}", timeout=30
    )
    assert classifier.call_args.args == (
        ArticleInput(
            title="Research",
            description="New study",
            body="Finding",
            language="en",
            source_category="Science",
            keywords=("study",),
        ),
    )
    assert classifier.call_count == 2
    assert second.post_revision == first.post_revision == 7
    assert second.enrichment_revision == first.enrichment_revision + 1
    assert second.event_id != first.event_id
    saved = repository.get_by_post_id(post_id)
    assert not saved.publication_pending
    published = json.loads(
        connection.channel.return_value.basic_publish.call_args.kwargs["body"]
    )
    assert published["event_id"] == second.event_id
    assert published["payload"]["enrichment_revision"] == 2
    assert "trace" not in published and "correlation_id" not in published
    assert connection.close.call_count == 2


@pytest.mark.parametrize("failure", ["publish", "mark"])
def test_command_failure_preserves_pending_result_and_blocks_reclassification(
    operation, monkeypatch, failure
):
    post_id, _, _, repository, classifier, connection = operation
    if failure == "publish":
        connection.channel.return_value.basic_publish.side_effect = (
            RuntimeError("publish")
        )
    else:
        monkeypatch.setattr(
            publication.EnrichmentRepository,
            "mark_published",
            MagicMock(side_effect=RuntimeError("mark")),
        )
    with pytest.raises(RuntimeError, match=failure):
        command.reclassify_post(post_id, "http://content:8002")
    saved = repository.get_by_post_id(post_id)
    assert saved.publication_pending
    with pytest.raises(ReclassificationConflict, match="republish_result"):
        command.reclassify_post(post_id, "http://content:8002")
    assert repository.get_by_post_id(post_id) == saved
    assert classifier.call_count == 1


@pytest.mark.parametrize("invalid", ["identity", "revision"])
def test_command_rejects_invalid_canonical_snapshot_before_classification(
    operation, invalid
):
    post_id, payload, _, repository, classifier, connection = operation
    if invalid == "identity":
        payload["post_id"] = str(uuid4())
    else:
        del payload["post_revision"]
    with pytest.raises((ValueError, ValidationError)):
        command.reclassify_post(post_id, "http://content:8002")
    classifier.assert_not_called()
    connection.channel.assert_not_called()
    assert repository.get_by_post_id(post_id) is None


def test_command_publishes_saved_classification_failure(operation):
    post_id, _, _, repository, classifier, connection = operation
    classifier.side_effect = TimeoutError("model")
    failed = command.reclassify_post(post_id, "http://content:8002")
    assert failed.status == "failed"
    assert not repository.get_by_post_id(post_id).publication_pending
    published = json.loads(
        connection.channel.return_value.basic_publish.call_args.kwargs["body"]
    )
    assert published["payload"]["status"] == "failed"

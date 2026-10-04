from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.repositories.enrichment_repository import (
    EnrichmentRepository,
    StoredEnrichment,
)


def test_saves_and_reads_enrichment(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    enrichment = StoredEnrichment(
        post_id=uuid4(),
        input_hash="a" * 64,
        enrichment_version="classification-v1",
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
    )

    assert repository.save(enrichment)

    assert repository.get_by_post_id(enrichment.post_id) == enrichment


def test_save_replaces_the_previous_result(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    post_id = uuid4()
    first = StoredEnrichment(
        post_id=post_id,
        input_hash="a" * 64,
        enrichment_version="classification-v1",
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
    )
    updated = StoredEnrichment(
        post_id=post_id,
        input_hash="b" * 64,
        enrichment_version="classification-v2",
        category_ids=(),
        status="abstained",
        reason="classifier_abstained",
        processed_at=datetime.now(UTC),
        post_revision=2,
    )

    assert repository.save(first)
    assert repository.save(updated)

    assert repository.get_by_post_id(post_id) == replace(
        updated, enrichment_revision=2
    )


def test_save_rejects_an_older_post_revision(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    post_id = uuid4()
    latest = StoredEnrichment(
        post_id=post_id,
        input_hash="b" * 64,
        enrichment_version="classification-v1",
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        post_revision=2,
    )
    stale = StoredEnrichment(
        post_id=post_id,
        input_hash="a" * 64,
        enrichment_version="classification-v1",
        category_ids=("business",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        post_revision=1,
    )

    assert repository.save(latest)
    assert not repository.save(stale)
    assert repository.get_by_post_id(post_id) == latest


def test_old_publish_confirmation_cannot_clear_newer_pending_result(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    first = StoredEnrichment(
        post_id=uuid4(),
        input_hash="a" * 64,
        enrichment_version="classification-v1",
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        event_id="event-1",
        result_event={"event_id": "event-1"},
        publication_pending=True,
    )
    newer = replace(
        first,
        post_revision=2,
        event_id="event-2",
        result_event={"event_id": "event-2"},
    )
    assert repository.save(first)
    assert repository.save(newer)

    with pytest.raises(RuntimeError, match="changed"):
        repository.mark_published(first.post_id, "event-1")

    assert repository.get_by_post_id(first.post_id) == replace(
        newer, enrichment_revision=2
    )


def test_second_result_for_same_revision_cannot_replace_first_event(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    first = StoredEnrichment(
        post_id=uuid4(),
        input_hash="a" * 64,
        enrichment_version="classification-v1",
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        event_id="event-1",
        result_event={"event_id": "event-1"},
        publication_pending=True,
    )
    competing = replace(
        first, event_id="event-2", result_event={"event_id": "event-2"}
    )

    assert repository.save(first)
    assert not repository.save(competing)
    assert repository.get_by_post_id(first.post_id) == first


def test_same_revision_new_policy_replaces_categories_and_increments_revision(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    first = StoredEnrichment(
        post_id=uuid4(),
        input_hash="a" * 64,
        enrichment_version="policy-1",
        category_ids=("finance",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
    )
    saved_first = repository.save(first)
    assert saved_first is not None
    second = replace(
        first,
        enrichment_version="policy-2",
        category_ids=("economy", "finance"),
    )
    saved_second = repository.save(second)
    assert saved_second is not None
    assert saved_second.enrichment_revision == 2
    assert repository.get_by_post_id(first.post_id) == saved_second

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
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
    )
    updated = StoredEnrichment(
        post_id=post_id,
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
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        post_revision=2,
    )
    stale = StoredEnrichment(
        post_id=post_id,
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
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        event_id=str(uuid4()),
        publication_pending=True,
    )
    newer = replace(
        first,
        post_revision=2,
        event_id=str(uuid4()),
    )
    assert repository.save(first)
    assert repository.save(newer)

    with pytest.raises(RuntimeError, match="changed"):
        repository.mark_published(first.post_id, first.event_id)

    assert repository.get_by_post_id(first.post_id) == replace(
        newer, enrichment_revision=2
    )


def test_second_result_for_same_revision_cannot_replace_first_event(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    first = StoredEnrichment(
        post_id=uuid4(),
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        event_id=str(uuid4()),
        publication_pending=True,
    )
    competing = replace(first, event_id=str(uuid4()))

    assert repository.save(first)
    assert not repository.save(competing)
    assert repository.get_by_post_id(first.post_id) == first


def test_same_revision_explicit_reclassification_is_conditional(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    first = StoredEnrichment(
        post_id=uuid4(),
        category_ids=("finance",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
    )
    saved_first = repository.save(first)
    assert saved_first is not None
    repository.mark_published(first.post_id, saved_first.event_id)
    second = replace(
        first,
        category_ids=("economy", "finance"),
    )
    saved_second = repository.save(
        second, expected_enrichment_revision=saved_first.enrichment_revision
    )
    assert saved_second is not None
    assert saved_second.enrichment_revision == 2
    assert repository.get_by_post_id(first.post_id) == saved_second


@pytest.mark.parametrize("status", ["completed", "failed"])
def test_pending_same_revision_cannot_be_replaced_even_explicitly(
    session_factory, status
):
    repository = EnrichmentRepository(session_factory)
    first = StoredEnrichment(
        post_id=uuid4(),
        category_ids=("science",) if status == "completed" else (),
        status=status,
        reason=None,
        processed_at=datetime.now(UTC),
    )
    assert repository.save(first) == first
    replacement = replace(first, event_id=str(uuid4()))
    assert repository.save(replacement) is None
    assert repository.save(replacement, expected_enrichment_revision=1) is None
    assert repository.get_by_post_id(first.post_id) == first


def test_stale_explicit_guard_cannot_replace_same_revision(session_factory):
    repository = EnrichmentRepository(session_factory)
    first = StoredEnrichment(
        post_id=uuid4(),
        category_ids=("science",),
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
    )
    assert repository.save(first)
    repository.mark_published(first.post_id, first.event_id)
    second = repository.save(
        replace(first, event_id=str(uuid4())), expected_enrichment_revision=1
    )
    assert second.enrichment_revision == 2
    repository.mark_published(second.post_id, second.event_id)
    assert (
        repository.save(
            replace(first, event_id=str(uuid4())),
            expected_enrichment_revision=1,
        )
        is None
    )

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.repositories.enrichment_repository import EnrichmentRepository
from src.repositories.stored_enrichment import StoredEnrichment


def test_revision_lifecycle_rejects_competing_and_stale_results(
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
    competing = replace(enrichment, event_id=str(uuid4()))
    assert repository.save(competing) is None
    newer = replace(
        enrichment,
        post_revision=2,
        event_id=str(uuid4()),
        category_ids=(),
        status="abstained",
        reason="classifier_abstained",
    )
    saved = repository.save(newer)
    assert saved == replace(newer, enrichment_revision=2)
    assert repository.save(enrichment) is None
    assert repository.get_by_post_id(enrichment.post_id) == saved


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
        event_id=str(uuid4()),
        category_ids=("economy", "finance"),
    )
    saved_second = repository.save(
        second, expected_enrichment_revision=saved_first.enrichment_revision
    )
    assert saved_second is not None
    assert saved_second.enrichment_revision == 2
    assert repository.get_by_post_id(first.post_id) == saved_second
    repository.mark_published(second.post_id, saved_second.event_id)
    assert (
        repository.save(
            replace(second, event_id=str(uuid4())),
            expected_enrichment_revision=1,
        )
        is None
    )
    assert repository.get_by_post_id(first.post_id) == replace(
        saved_second, publication_pending=False
    )


def test_pending_same_revision_cannot_be_replaced_even_explicitly(
    session_factory,
):
    repository = EnrichmentRepository(session_factory)
    first = StoredEnrichment(
        post_id=uuid4(),
        category_ids=(),
        status="failed",
        reason=None,
        processed_at=datetime.now(UTC),
    )
    assert repository.save(first) == first
    replacement = replace(first, event_id=str(uuid4()))
    assert repository.save(replacement) is None
    assert repository.save(replacement, expected_enrichment_revision=1) is None
    assert repository.get_by_post_id(first.post_id) == first

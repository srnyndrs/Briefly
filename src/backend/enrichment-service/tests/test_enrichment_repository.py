from datetime import UTC, datetime
from uuid import uuid4

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
        category_id="science",
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
        category_id="science",
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
    )
    updated = StoredEnrichment(
        post_id=post_id,
        input_hash="b" * 64,
        enrichment_version="classification-v2",
        category_id=None,
        status="abstained",
        reason="classifier_abstained",
        processed_at=datetime.now(UTC),
        post_revision=2,
    )

    assert repository.save(first)
    assert repository.save(updated)

    assert repository.get_by_post_id(post_id) == updated


def test_save_rejects_an_older_post_revision(
    session_factory: sessionmaker[Session],
) -> None:
    repository = EnrichmentRepository(session_factory)
    post_id = uuid4()
    latest = StoredEnrichment(
        post_id=post_id,
        input_hash="b" * 64,
        enrichment_version="classification-v1",
        category_id="science",
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        post_revision=2,
    )
    stale = StoredEnrichment(
        post_id=post_id,
        input_hash="a" * 64,
        enrichment_version="classification-v1",
        category_id="business",
        status="completed",
        reason=None,
        processed_at=datetime.now(UTC),
        post_revision=1,
    )

    assert repository.save(latest)
    assert not repository.save(stale)
    assert repository.get_by_post_id(post_id) == latest

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.config.settings import settings
from src.repositories.source_repository import SourceRepository


@pytest.mark.parametrize("verified", [True, False], ids=["verified", "unverified"])
def test_retry_scheduling_and_recovery(db_session, source_factory, verified):
    source = source_factory(verified=verified)
    repository = SourceRepository(db_session)
    base = (
        settings.verified_crawl_interval_seconds
        if verified
        else settings.unverified_crawl_interval_seconds
    )
    for failures in (1, 2):
        assert repository.save_crawl_failure(source_id=source.source_id) == failures
        repository.commit()
        db_session.refresh(source)
        assert source.last_crawl_succeeded is False
        assert source.next_crawl_scheduled_at - source.last_crawled_at == timedelta(
            seconds=base * 2**failures
        )
    source.consecutive_failures = 10
    db_session.commit()
    repository.save_crawl_failure(source_id=source.source_id)
    repository.commit()
    db_session.refresh(source)
    assert source.next_crawl_scheduled_at - source.last_crawled_at == timedelta(
        days=1
    )

    repository.save_crawl_success(
        source_id=source.source_id,
        etag="fresh",
        last_modified="new-date",
    )
    repository.commit()
    db_session.refresh(source)
    assert source.consecutive_failures == 0
    assert source.last_crawl_succeeded is True
    assert source.etag == "fresh"
    assert source.last_modified == "new-date"
    assert source.next_crawl_scheduled_at - source.last_crawled_at == timedelta(
        seconds=base
    )


def test_due_sources_use_tier_time_and_id_order(db_session, source_factory):
    repository = SourceRepository(db_session)
    now = datetime.now(timezone.utc)
    due = now - timedelta(minutes=1)
    first = source_factory(
        verified=True,
        next_crawl_scheduled_at=due,
        source_id=uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"),
    )
    second = source_factory(
        verified=True,
        next_crawl_scheduled_at=due,
        source_id=uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2"),
    )
    third = source_factory(verified=True, next_crawl_scheduled_at=now)
    unverified = source_factory(next_crawl_scheduled_at=due)
    source_factory(next_crawl_scheduled_at=now + timedelta(days=1))
    source_factory(consecutive_failures=settings.max_retries)
    expected = [first, second, third, unverified]
    assert repository.get_active_sources(now, settings.max_retries) == expected
    assert (
        repository.get_active_sources(now, settings.max_retries, verified_only=True)
        == expected[:3]
    )


def test_deleted_sources_are_hidden_and_never_scheduled(db_session, source_factory):
    now = datetime.now(timezone.utc)
    deleted = source_factory(
        verified=True,
        next_crawl_scheduled_at=now - timedelta(minutes=1),
    )
    active = source_factory(
        verified=True,
        next_crawl_scheduled_at=now - timedelta(minutes=1),
    )
    repository = SourceRepository(db_session)

    assert repository.delete_source(deleted.source_id)
    repository.commit()

    assert repository.list_sources() == [active]
    assert repository.get_active_sources(now, settings.max_retries) == [active]
    assert repository.get_by_url(deleted.url) == deleted

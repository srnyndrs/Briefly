from datetime import datetime, timedelta, timezone

from src.config.settings import settings
from src.repositories.source_repository import SourceRepository


def test_calculate_next_crawl_success_and_failures(db_session):
    repo = SourceRepository(db_session)
    source = repo.create_source(
        url="https://example.com/feed-retry.xml",
        title="Retry Test Feed",
    )

    base = settings.base_crawl_interval_seconds
    now = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Success (failures == 0)
    source.consecutive_failures = 0
    next_run = repo._calculate_next_crawl(source, now)
    assert next_run == now + timedelta(seconds=base)

    # 1st failure (failures == 1) -> 2^1 * base = 2 * base
    source.consecutive_failures = 1
    next_run = repo._calculate_next_crawl(source, now)
    assert next_run == now + timedelta(seconds=2 * base)

    # 2nd failure (failures == 2) -> 2^2 * base = 4 * base
    source.consecutive_failures = 2
    next_run = repo._calculate_next_crawl(source, now)
    assert next_run == now + timedelta(seconds=4 * base)

    # Capped failure delay (e.g. 10 failures) -> min(2^10 * 300, 24 * 3600) = 86400s (24h)
    source.consecutive_failures = 10
    next_run = repo._calculate_next_crawl(source, now)
    assert next_run == now + timedelta(hours=24)


def test_get_active_sources_respects_max_retries(db_session):
    repo = SourceRepository(db_session)
    now = datetime.now(timezone.utc)
    past = now - timedelta(minutes=10)

    # Source below max_retries (4 < 5)
    source_eligible = repo.create_source(
        url="https://example.com/eligible.xml",
        title="Eligible",
    )
    source_eligible.consecutive_failures = 4
    source_eligible.next_crawl_scheduled_at = past

    # Source at max_retries (5 == 5)
    source_suspended = repo.create_source(
        url="https://example.com/suspended.xml",
        title="Suspended",
    )
    source_suspended.consecutive_failures = 5
    source_suspended.next_crawl_scheduled_at = past

    # Source not due yet (0 failures, but scheduled in future)
    source_future = repo.create_source(
        url="https://example.com/future.xml",
        title="Future",
    )
    source_future.consecutive_failures = 0
    source_future.next_crawl_scheduled_at = now + timedelta(minutes=10)

    db_session.commit()

    active = repo.get_active_sources(now, max_retries=5)
    active_ids = {s.source_id for s in active}

    assert source_eligible.source_id in active_ids
    assert source_suspended.source_id not in active_ids
    assert source_future.source_id not in active_ids


def test_source_defaults_unverified_and_domain_lookup_is_non_unique(
    db_session,
):
    repo = SourceRepository(db_session)
    first = repo.create_source(
        url="https://www.example.com/first.xml",
        title="Example",
        registrable_domain="example.com",
    )
    second = repo.create_source(
        url="https://news.example.com/second.xml",
        title="Example News",
        registrable_domain="example.com",
        verified=True,
    )

    assert first.verified is False
    assert first.submitted_by_user_id is None
    assert [
        source.source_id
        for source in repo.get_sources_by_registrable_domain(
            "example.com"
        )
    ] == sorted([first.source_id, second.source_id], key=str)


def test_get_sources_orders_verified_then_title_and_id(db_session):
    repo = SourceRepository(db_session)
    unverified = repo.create_source(
        url="https://example.com/z.xml", title="Alpha"
    )
    verified_z = repo.create_source(
        url="https://example.com/a.xml", title="zeta", verified=True
    )
    verified_a = repo.create_source(
        url="https://example.com/b.xml", title="Alpha", verified=True
    )

    ordered = repo.get_sources()
    source_ids = [source.source_id for source in ordered]
    assert (
        source_ids.index(verified_a.source_id)
        < source_ids.index(verified_z.source_id)
        < source_ids.index(unverified.source_id)
    )
    assert repo.get_sources(verified_only=True) == [
        verified_a,
        verified_z,
    ]


def test_save_crawl_failure_increments_failures_and_delays_retry(
    db_session,
):
    repo = SourceRepository(db_session)
    source = repo.create_source(
        url="https://example.com/failure-test.xml",
        title="Failure Test Feed",
    )
    assert source.consecutive_failures == 0

    repo.save_crawl_failure(source_id=source.source_id)

    updated = repo.get_source_by_id(source.source_id)
    assert updated is not None
    assert updated.consecutive_failures == 1
    assert updated.last_crawl_succeeded is False
    assert updated.last_crawled_at is not None

    next_scheduled = updated.next_crawl_scheduled_at
    if next_scheduled.tzinfo is None:
        next_scheduled = next_scheduled.replace(tzinfo=timezone.utc)

    # Next run should be scheduled roughly 2 * 300s = 600s in future
    expected_min = datetime.now(timezone.utc) + timedelta(seconds=580)
    assert next_scheduled >= expected_min

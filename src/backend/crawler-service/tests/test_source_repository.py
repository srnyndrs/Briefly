import uuid
from datetime import datetime, timedelta, timezone

from src.config.settings import settings
from src.repositories.source_repository import SourceRepository


def test_source_update_and_delete_preserve_metadata(db_session):
    repo = SourceRepository(db_session)
    source = repo.create_source(
        url="https://example.com/feed",
        title="Example",
        description="Original description",
        favicon="https://example.com/icon.png",
        website_url="https://example.com/",
        registrable_domain="example.com",
        verified=True,
    )
    source_id = source.source_id

    updated = repo.update_source(
        source_id=source_id,
        url="https://example.com/news.xml",
        description=None,
        favicon=None,
    )
    db_session.expire_all()
    stored = repo.get_source_by_url("https://example.com/news.xml")

    assert updated is stored
    assert stored.source_id == source_id
    assert stored.title == "Example"
    assert stored.website_url == "https://example.com/"
    assert stored.registrable_domain == "example.com"
    assert stored.verified is True
    assert stored.description is None
    assert stored.favicon is None
    assert repo.get_source_by_url("https://example.com/feed") is None
    assert repo.delete_source(source_id) is True
    assert repo.get_source_by_id(source_id) is None
    assert repo.delete_source(source_id) is False


def test_missing_source_updates_are_noops(db_session):
    repo = SourceRepository(db_session)
    source_id = uuid.uuid4()

    assert repo.get_source_by_id(source_id) is None
    assert (
        repo.update_source(
            source_id=source_id,
            url="https://example.com/feed",
            description=None,
            favicon=None,
        )
        is None
    )
    assert (
        repo.save_crawl_success(
            source_id=source_id, etag=None, last_modified=None
        )
        is None
    )
    assert repo.save_crawl_failure(source_id=source_id) is None
    assert repo.get_sources() == []


def test_verified_source_uses_verified_interval_after_success(
    db_session,
):
    repo = SourceRepository(db_session)
    source = repo.create_source(
        url="https://example.com/feed-retry.xml",
        title="Retry Test Feed",
        registrable_domain="example.com",
        verified=True,
    )
    now = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

    source.consecutive_failures = 0
    assert repo._calculate_next_crawl(source, now) == now + timedelta(
        seconds=settings.verified_crawl_interval_seconds
    )


def test_unverified_source_uses_unverified_interval_after_success(
    db_session,
):
    repo = SourceRepository(db_session)
    source = repo.create_source(
        url="https://example.com/unverified-retry.xml",
        title="Unverified Retry Test Feed",
        registrable_domain="example.com",
    )
    now = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

    source.consecutive_failures = 0
    assert repo._calculate_next_crawl(source, now) == now + timedelta(
        seconds=settings.unverified_crawl_interval_seconds
    )


def test_retry_backoff_uses_each_sources_base_interval(db_session):
    repo = SourceRepository(db_session)
    now = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    sources = [
        repo.create_source(
            url="https://example.com/verified-retry.xml",
            title="Verified Retry",
            registrable_domain="example.com",
            verified=True,
        ),
        repo.create_source(
            url="https://example.com/unverified-retry-2.xml",
            title="Unverified Retry",
            registrable_domain="example.com",
        ),
    ]
    intervals = [
        settings.verified_crawl_interval_seconds,
        settings.unverified_crawl_interval_seconds,
    ]

    for source, base_interval in zip(sources, intervals, strict=True):
        source.consecutive_failures = 1
        assert repo._calculate_next_crawl(
            source, now
        ) == now + timedelta(seconds=2 * base_interval)
        source.consecutive_failures = 2
        assert repo._calculate_next_crawl(
            source, now
        ) == now + timedelta(seconds=4 * base_interval)
        source.consecutive_failures = 10
        assert repo._calculate_next_crawl(
            source, now
        ) == now + timedelta(hours=24)


def test_get_active_sources_respects_max_retries(db_session):
    repo = SourceRepository(db_session)
    now = datetime.now(timezone.utc)
    past = now - timedelta(minutes=10)

    # Source below max_retries (4 < 5)
    source_eligible = repo.create_source(
        url="https://example.com/eligible.xml",
        title="Eligible",
        registrable_domain="example.com",
    )
    source_eligible.consecutive_failures = 4
    source_eligible.next_crawl_scheduled_at = past

    # Source at max_retries (5 == 5)
    source_suspended = repo.create_source(
        url="https://example.com/suspended.xml",
        title="Suspended",
        registrable_domain="example.com",
    )
    source_suspended.consecutive_failures = 5
    source_suspended.next_crawl_scheduled_at = past

    # Source not due yet (0 failures, but scheduled in future)
    source_future = repo.create_source(
        url="https://example.com/future.xml",
        title="Future",
        registrable_domain="example.com",
    )
    source_future.consecutive_failures = 0
    source_future.next_crawl_scheduled_at = now + timedelta(minutes=10)

    db_session.commit()

    active = repo.get_active_sources(now, max_retries=5)
    active_ids = {s.source_id for s in active}

    assert source_eligible.source_id in active_ids
    assert source_suspended.source_id not in active_ids
    assert source_future.source_id not in active_ids


def test_due_sources_are_verified_first_with_stable_order(db_session):
    repo = SourceRepository(db_session)
    now = datetime.now(timezone.utc)
    past = now - timedelta(minutes=1)
    sources = [
        repo.create_source(
            url="https://example.com/verified-z.xml",
            title="Verified Z",
            registrable_domain="example.com",
            verified=True,
        ),
        repo.create_source(
            url="https://example.com/verified-a.xml",
            title="Verified A",
            registrable_domain="example.com",
            verified=True,
        ),
        repo.create_source(
            url="https://example.com/unverified-b.xml",
            title="Unverified B",
            registrable_domain="example.com",
        ),
        repo.create_source(
            url="https://example.com/unverified-a.xml",
            title="Unverified A",
            registrable_domain="example.com",
        ),
    ]
    for source in sources:
        source.next_crawl_scheduled_at = past
    db_session.commit()

    verified_ids = {source.source_id for source in sources[:2]}
    unverified_ids = {source.source_id for source in sources[2:]}
    target_ids = verified_ids | unverified_ids
    ordered_sources = [
        source
        for source in repo.get_active_sources(now, max_retries=5)
        if source.source_id in target_ids
    ]
    ordered_verified_ids = [
        source.source_id
        for source in ordered_sources
        if source.verified
    ]
    ordered_unverified_ids = [
        source.source_id
        for source in ordered_sources
        if not source.verified
    ]
    assert ordered_verified_ids == sorted(verified_ids, key=str)
    assert ordered_unverified_ids == sorted(unverified_ids, key=str)


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
    domain_sources = [
        source.source_id
        for source in repo.get_sources_by_registrable_domain(
            "example.com"
        )
    ]
    assert first.source_id in domain_sources
    assert second.source_id in domain_sources
    assert domain_sources == sorted(domain_sources, key=str)


def test_get_sources_orders_verified_then_title_and_id(db_session):
    repo = SourceRepository(db_session)
    unverified = repo.create_source(
        url="https://example.com/z.xml",
        title="Alpha",
        registrable_domain="example.com",
    )
    verified_z = repo.create_source(
        url="https://example.com/a.xml",
        title="zeta",
        registrable_domain="example.com",
        verified=True,
    )
    verified_a = repo.create_source(
        url="https://example.com/b.xml",
        title="Alpha",
        registrable_domain="example.com",
        verified=True,
    )

    ordered = repo.get_sources()
    source_ids = [source.source_id for source in ordered]
    assert (
        source_ids.index(verified_a.source_id)
        < source_ids.index(verified_z.source_id)
        < source_ids.index(unverified.source_id)
    )
    verified_ids = [
        source.source_id
        for source in repo.get_sources(verified_only=True)
    ]
    assert verified_a.source_id in verified_ids
    assert verified_z.source_id in verified_ids
    assert verified_ids.index(
        verified_a.source_id
    ) < verified_ids.index(verified_z.source_id)


def test_save_crawl_failure_increments_failures_and_delays_retry(
    db_session,
):
    repo = SourceRepository(db_session)
    source = repo.create_source(
        url="https://example.com/failure-test.xml",
        title="Failure Test Feed",
        registrable_domain="example.com",
    )
    assert source.consecutive_failures == 0

    failure_count = repo.save_crawl_failure(source_id=source.source_id)

    updated = repo.get_source_by_id(source.source_id)
    assert updated is not None
    assert updated.consecutive_failures == 1
    assert failure_count == 1
    assert updated.last_crawl_succeeded is False
    assert updated.last_crawled_at is not None

    next_scheduled = updated.next_crawl_scheduled_at
    if next_scheduled.tzinfo is None:
        next_scheduled = next_scheduled.replace(tzinfo=timezone.utc)

    # Next run should use the unverified base interval with 2x backoff.
    expected_min = datetime.now(timezone.utc) + timedelta(
        seconds=2 * settings.unverified_crawl_interval_seconds - 20
    )
    assert next_scheduled >= expected_min

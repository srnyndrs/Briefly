import os
import threading
from collections import Counter
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import sessionmaker

from src.config.database import Base
from src.config.settings import settings
from src.repositories.source_repository import SourceRepository
from src.services.crawl_orchestrator import CrawlCycleOrchestrator


@pytest.fixture
def db_engine() -> Iterator[Engine]:
    """Use only the configured test database and a uniquely owned schema."""
    database_url = os.environ.get("CRAWLER_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set CRAWLER_TEST_DATABASE_URL to run PostgreSQL checks")
    if make_url(database_url).get_backend_name() != "postgresql":
        pytest.fail("CRAWLER_TEST_DATABASE_URL must point to isolated PostgreSQL")

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 5,
            "options": "-c statement_timeout=5000 -c lock_timeout=2000",
        },
    )
    schema = f"crawler_test_{uuid4().hex}"
    created = False
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        created = True
        mapped = engine.execution_options(schema_translate_map={"crawler": schema})
        Base.metadata.create_all(bind=mapped)
        yield mapped
    finally:
        try:
            if created:
                with engine.begin() as connection:
                    connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        finally:
            engine.dispose()


def test_source_locking_and_transaction_lifecycle(db_engine, source_factory):
    now = datetime.now(timezone.utc)
    first = source_factory(source_id=UUID(int=1), next_crawl_scheduled_at=now)
    second = source_factory(source_id=UUID(int=2), next_crawl_scheduled_at=now)
    sessions = sessionmaker(bind=db_engine, autoflush=False)

    with sessions() as session_a, sessions() as session_b:
        assert session_a.scalar(
            text("SELECT pg_backend_pid()")
        ) != session_b.scalar(text("SELECT pg_backend_pid()"))
        repository_a = SourceRepository(session_a)
        repository_b = SourceRepository(session_b)
        locked = repository_a.get_next_active_source(
            now=now, max_retries=settings.max_retries
        )
        assert locked.source_id == first.source_id

        available = repository_b.get_next_active_source(
            now=now, max_retries=settings.max_retries
        )
        assert available.source_id == second.source_id
        repository_b.save_crawl_success(
            source_id=available.source_id, etag="fresh", last_modified=None
        )
        repository_b.commit()

        # Only A's locked source is still due.
        assert (
            repository_b.get_next_active_source(
                now=now, max_retries=settings.max_retries
            )
            is None
        )
        repository_a.save_crawl_success(
            source_id=locked.source_id, etag="uncommitted", last_modified=None
        )
        repository_a.rollback()

        available = repository_b.get_next_active_source(
            now=now, max_retries=settings.max_retries
        )
        assert available.source_id == first.source_id
        assert available.next_crawl_scheduled_at == now
        assert available.last_crawled_at is None
        assert available.etag is None
        session_b.close()

        # Closing B without committing must also release its source.
        available = repository_a.get_next_active_source(
            now=now, max_retries=settings.max_retries
        )
        assert available.source_id == first.source_id
        repository_a.save_crawl_success(
            source_id=available.source_id, etag="fresh", last_modified=None
        )
        repository_a.commit()

    with sessions() as session:
        assert (
            SourceRepository(session).get_next_active_source(
                now=now, max_retries=settings.max_retries
            )
            is None
        )


def test_two_orchestrators_distribute_sources_once(
    db_engine, source_factory, crawl_cycle, db_session
):
    due = datetime.now(timezone.utc) - timedelta(minutes=1)
    sources = [source_factory(next_crawl_scheduled_at=due) for _ in range(6)]
    first, http_get, publisher, publisher_factory = crawl_cycle
    second = CrawlCycleOrchestrator(sessionmaker(bind=db_engine, autoflush=False))
    overlap = threading.Barrier(2)
    worker = threading.local()
    lock = threading.Lock()
    fetched = []
    published = []
    response = http_get.return_value

    def fetch(url, **kwargs):
        with lock:
            fetched.append(url)
        if not getattr(worker, "started", False):
            worker.started = True
            overlap.wait(timeout=5)
        return response

    def publish(channel, **kwargs):
        with lock:
            published.append(kwargs["envelope"]["payload"]["source_id"])

    http_get.side_effect = fetch
    publisher.side_effect = publish

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(item.run_crawl_cycle) for item in (first, second)
        ]
        for future in futures:
            future.result(timeout=15)

    assert Counter(fetched) == Counter(source.url for source in sources)
    assert Counter(published) == Counter(
        str(source.source_id) for source in sources
    )
    assert publisher_factory.call_count == 2
    for source in sources:
        db_session.refresh(source)
        assert source.last_crawl_succeeded is True
        assert source.consecutive_failures == 0
        assert source.next_crawl_scheduled_at > source.last_crawled_at


def test_publisher_failure_releases_source_for_another_orchestrator(
    db_engine, source_factory, crawl_cycle, db_session
):
    source = source_factory(etag="old", last_modified="old-date")
    previous_schedule = source.next_crawl_scheduled_at
    first, http_get, publisher, _ = crawl_cycle
    publisher.side_effect = RuntimeError("publication failed")

    with pytest.raises(RuntimeError, match="publication failed"):
        first.run_crawl_cycle()

    db_session.refresh(source)
    assert source.next_crawl_scheduled_at == previous_schedule
    assert source.last_crawled_at is None
    assert source.consecutive_failures == 0
    assert source.etag == "old"
    assert source.last_modified == "old-date"

    publisher.side_effect = None
    second = CrawlCycleOrchestrator(sessionmaker(bind=db_engine, autoflush=False))
    second.run_crawl_cycle()

    db_session.refresh(source)
    assert source.last_crawl_succeeded is True
    assert source.next_crawl_scheduled_at > previous_schedule
    assert source.etag == "fresh"
    assert http_get.call_count == 2
    assert publisher.call_count == 2

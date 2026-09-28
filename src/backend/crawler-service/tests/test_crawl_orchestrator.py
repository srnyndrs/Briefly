import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.services.crawl_orchestrator import CrawlCycleOrchestrator


def _session_factory_with(session):
    session_factory = MagicMock()
    session_factory.return_value.__enter__.return_value = session
    return session_factory


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_orchestrator_runs_crawl_and_updates_state(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    source = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/feed.xml",
        title="Test Source",
        etag="old-etag",
        last_modified="Mon, 01 Jan 2026 00:00:00 GMT",
        consecutive_failures=1,
    )

    source_repository = MagicMock()
    source_repository.get_active_sources.return_value = [source]
    mock_source_repo_cls.return_value = source_repository

    http_client = MagicMock()
    http_client.fetch.return_value = SimpleNamespace(
        status_code=200,
        body="<xml>",
        etag="fresh-etag",
        last_modified="Tue, 02 Jan 2026 00:00:00 GMT",
    )
    mock_http_client_cls.return_value = http_client

    event_publisher = MagicMock()
    mock_event_pub_cls.return_value = event_publisher

    orchestrator = CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    )
    orchestrator.run_crawl_cycle()

    http_client.fetch.assert_called_once()
    fetch_headers = http_client.fetch.call_args[0][1]
    assert fetch_headers.etag == "old-etag"
    assert (
        fetch_headers.last_modified == "Mon, 01 Jan 2026 00:00:00 GMT"
    )

    event_publisher.publish_source_fetched.assert_called_once()
    source_repository.save_crawl_success.assert_called_once_with(
        source_id=source.source_id,
        etag="fresh-etag",
        last_modified="Tue, 02 Jan 2026 00:00:00 GMT",
    )
    event_publisher.close.assert_called_once()


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_orchestrator_idle_cycle_does_not_initialize_rabbitmq(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    source_repository = MagicMock()
    source_repository.get_active_sources.return_value = []
    mock_source_repo_cls.return_value = source_repository

    http_client = MagicMock()
    mock_http_client_cls.return_value = http_client

    orchestrator = CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    )
    orchestrator.run_crawl_cycle()

    mock_event_pub_cls.assert_not_called()
    http_client.fetch.assert_not_called()


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_orchestrator_shares_correlation_id_across_cycle(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    source1 = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/s1.xml",
        title="Source 1",
        etag=None,
        last_modified=None,
        consecutive_failures=0,
    )
    source2 = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/s2.xml",
        title="Source 2",
        etag=None,
        last_modified=None,
        consecutive_failures=0,
    )

    source_repository = MagicMock()
    source_repository.get_active_sources.return_value = [
        source1,
        source2,
    ]
    mock_source_repo_cls.return_value = source_repository

    http_client = MagicMock()
    http_client.fetch.return_value = SimpleNamespace(
        status_code=200,
        body="<xml>",
        etag=None,
        last_modified=None,
    )
    mock_http_client_cls.return_value = http_client

    event_publisher = MagicMock()
    mock_event_pub_cls.return_value = event_publisher

    orchestrator = CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    )
    orchestrator.run_crawl_cycle()

    assert event_publisher.publish_source_fetched.call_count == 2
    call1_kwargs = (
        event_publisher.publish_source_fetched.call_args_list[0].kwargs
    )
    call2_kwargs = (
        event_publisher.publish_source_fetched.call_args_list[1].kwargs
    )

    assert (
        call1_kwargs["correlation_id"] == call2_kwargs["correlation_id"]
    )
    assert len(call1_kwargs["correlation_id"]) > 0


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_orchestrator_handles_304_not_modified(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    source = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/feed.xml",
        title="Test Source",
        etag="existing-etag",
        last_modified="Mon, 01 Jan 2026 00:00:00 GMT",
        consecutive_failures=0,
    )

    source_repository = MagicMock()
    source_repository.get_active_sources.return_value = [source]
    mock_source_repo_cls.return_value = source_repository

    http_client = MagicMock()
    http_client.fetch.return_value = SimpleNamespace(
        status_code=304,
        body="",
        etag="existing-etag",
        last_modified="Mon, 01 Jan 2026 00:00:00 GMT",
    )
    mock_http_client_cls.return_value = http_client

    event_publisher = MagicMock()
    mock_event_pub_cls.return_value = event_publisher

    orchestrator = CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    )
    orchestrator.run_crawl_cycle()

    http_client.fetch.assert_called_once()
    fetch_headers = http_client.fetch.call_args[0][1]
    assert fetch_headers.etag == "existing-etag"
    assert (
        fetch_headers.last_modified == "Mon, 01 Jan 2026 00:00:00 GMT"
    )

    event_publisher.publish_source_fetched.assert_not_called()
    source_repository.save_crawl_success.assert_called_once_with(
        source_id=source.source_id,
        etag="existing-etag",
        last_modified="Mon, 01 Jan 2026 00:00:00 GMT",
    )
    event_publisher.close.assert_called_once()


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_orchestrator_recovers_after_prior_failures(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    source = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/feed.xml",
        title="Failing Source",
        etag=None,
        last_modified=None,
        consecutive_failures=3,
    )

    source_repository = MagicMock()
    source_repository.get_active_sources.return_value = [source]
    mock_source_repo_cls.return_value = source_repository

    http_client = MagicMock()
    http_client.fetch.return_value = SimpleNamespace(
        status_code=200,
        body="<xml>recovered</xml>",
        etag="recovered-etag",
        last_modified="Tue, 02 Jan 2026 00:00:00 GMT",
    )
    mock_http_client_cls.return_value = http_client

    event_publisher = MagicMock()
    mock_event_pub_cls.return_value = event_publisher

    orchestrator = CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    )
    orchestrator.run_crawl_cycle()

    http_client.fetch.assert_called_once()
    event_publisher.publish_source_fetched.assert_called_once_with(
        source_id=source.source_id,
        source_url="https://example.com/feed.xml",
        correlation_id=event_publisher.publish_source_fetched.call_args.kwargs[
            "correlation_id"
        ],
        source_title="Failing Source",
        raw_xml="<xml>recovered</xml>",
    )
    source_repository.save_crawl_success.assert_called_once_with(
        source_id=source.source_id,
        etag="recovered-etag",
        last_modified="Tue, 02 Jan 2026 00:00:00 GMT",
    )
    event_publisher.close.assert_called_once()


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_request_failure_updates_source_and_continues_cycle(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    sources = [
        SimpleNamespace(
            source_id=uuid.uuid4(),
            url="https://bad.example/feed?key=secret",
            title="Bad",
            etag=None,
            last_modified=None,
        ),
        SimpleNamespace(
            source_id=uuid.uuid4(),
            url="https://good.example/feed",
            title="Good",
            etag=None,
            last_modified=None,
        ),
    ]
    repo = MagicMock()
    repo.get_active_sources.return_value = sources
    repo.save_crawl_failure.return_value = 1
    mock_source_repo_cls.return_value = repo
    http = MagicMock()
    http.fetch.side_effect = [
        requests.Timeout("secret detail"),
        SimpleNamespace(status_code=304),
    ]
    mock_http_client_cls.return_value = http
    publisher = MagicMock()
    mock_event_pub_cls.return_value = publisher

    orchestrator = CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    )
    orchestrator.run_crawl_cycle()

    repo.save_crawl_failure.assert_called_once_with(
        source_id=sources[0].source_id
    )
    repo.save_crawl_success.assert_called_once_with(
        source_id=sources[1].source_id,
        etag=None,
        last_modified=None,
    )
    assert http.fetch.call_count == 2


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_publisher_failure_aborts_cycle_and_closes_publisher(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
    caplog,
):
    source = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/feed",
        title="Feed",
        etag=None,
        last_modified=None,
    )
    repo = MagicMock()
    repo.get_active_sources.return_value = [source]
    mock_source_repo_cls.return_value = repo
    http = MagicMock()
    http.fetch.return_value = SimpleNamespace(
        status_code=200, body="<feed/>", etag=None, last_modified=None
    )
    mock_http_client_cls.return_value = http
    publisher = MagicMock()
    publisher.publish_source_fetched.side_effect = RuntimeError(
        "broker down token=private <feed>private</feed>"
    )
    mock_event_pub_cls.return_value = publisher

    orchestrator = CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    )
    with pytest.raises(RuntimeError, match="broker down"):
        orchestrator.run_crawl_cycle()

    repo.save_crawl_failure.assert_not_called()
    publisher.close.assert_called_once()
    assert "token=private" not in caplog.text
    assert "<feed>private</feed>" not in caplog.text


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_suspension_is_reported_only_at_retry_limit(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
    caplog,
):
    from src.config.settings import settings

    source = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/feed?secret=hidden",
        title="Feed",
        etag=None,
        last_modified=None,
    )
    repo = MagicMock()
    repo.get_active_sources.return_value = [source]
    repo.save_crawl_failure.return_value = settings.max_retries
    mock_source_repo_cls.return_value = repo
    http = MagicMock()
    http.fetch.side_effect = requests.Timeout("private timeout details")
    mock_http_client_cls.return_value = http
    mock_event_pub_cls.return_value = MagicMock()

    CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    ).run_crawl_cycle()

    errors = [
        record
        for record in caplog.records
        if record.levelname == "ERROR"
        and "Source suspended" in record.message
    ]
    assert len(errors) == 1
    assert "example.com" in errors[0].message
    assert "secret=hidden" not in errors[0].message
    assert "private timeout details" not in errors[0].message


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_deleted_source_is_skipped_in_cycle_summary(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
    caplog,
):
    source = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/feed",
        etag=None,
        last_modified=None,
    )
    repo = MagicMock()
    repo.get_active_sources.return_value = [source]
    repo.save_crawl_failure.return_value = None
    mock_source_repo_cls.return_value = repo
    mock_http_client_cls.return_value.fetch.side_effect = (
        requests.Timeout()
    )
    mock_event_pub_cls.return_value = MagicMock()

    with caplog.at_level("INFO"):
        CrawlCycleOrchestrator(
            session_factory=_session_factory_with(MagicMock())
        ).run_crawl_cycle()

    assert "failed=0, skipped=1" in caplog.text


@patch("src.services.crawl_orchestrator.FeedPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.SourceRepository")
def test_cleanup_failure_does_not_add_second_error_log(
    mock_source_repo_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
    caplog,
):
    source = SimpleNamespace(
        source_id=uuid.uuid4(),
        url="https://example.com/feed",
        title="Feed",
        etag=None,
        last_modified=None,
    )
    repo = MagicMock()
    repo.get_active_sources.return_value = [source]
    mock_source_repo_cls.return_value = repo
    mock_http_client_cls.return_value.fetch.return_value = (
        SimpleNamespace(
            status_code=200,
            body="<feed/>",
            etag=None,
            last_modified=None,
        )
    )
    publisher = MagicMock()
    publisher.publish_source_fetched.side_effect = RuntimeError(
        "publish failed"
    )
    publisher.close.side_effect = RuntimeError("close failed")
    mock_event_pub_cls.return_value = publisher

    with pytest.raises(RuntimeError, match="publish failed"):
        CrawlCycleOrchestrator(
            session_factory=_session_factory_with(MagicMock())
        ).run_crawl_cycle()

    assert (
        sum(record.levelname == "ERROR" for record in caplog.records)
        == 1
    )


def test_suspension_alert_follows_committed_retry_transition(
    db_session, caplog
):
    from src.config.settings import settings
    from src.repositories.source_repository import SourceRepository

    repo = SourceRepository(db_session)
    source = repo.create_source(
        url="https://example.com/feed?token=private",
        title="Example",
        registrable_domain="example.com",
    )
    source.consecutive_failures = settings.max_retries - 1
    db_session.commit()

    orchestrator = CrawlCycleOrchestrator(session_factory=MagicMock())
    orchestrator._http_client.fetch = MagicMock(
        side_effect=requests.Timeout("private detail")
    )
    assert (
        orchestrator._crawl_source(repo, MagicMock(), source, "cycle-1")
        == "failed"
    )
    assert repo.get_source_by_id(
        source.source_id
    ).consecutive_failures == (settings.max_retries)
    assert (
        sum(record.levelname == "ERROR" for record in caplog.records)
        == 1
    )

    orchestrator._crawl_source(repo, MagicMock(), source, "cycle-2")
    assert (
        sum(record.levelname == "ERROR" for record in caplog.records)
        == 1
    )


def test_save_crawl_success_reschedules_and_resets_failures(db_session):
    from src.repositories.source_repository import SourceRepository

    repo = SourceRepository(db_session)
    source = repo.create_source(
        url="https://example.com/feed-304.xml",
        title="Test Feed",
        registrable_domain="example.com",
    )

    # Set prior failures and past next_crawl_scheduled_at
    past = datetime(2026, 1, 1, tzinfo=timezone.utc)
    source.consecutive_failures = 2
    source.next_crawl_scheduled_at = past
    db_session.commit()

    # Verify it is due initially
    due = repo.get_active_sources(
        datetime.now(timezone.utc), max_retries=5
    )
    assert any(s.source_id == source.source_id for s in due)

    # Record 304 crawl success with existing validators
    repo.save_crawl_success(
        source_id=source.source_id,
        etag="etag-1",
        last_modified="Mon, 01 Jan 2026 00:00:00 GMT",
    )

    # Reload source and assert state transitions
    updated = repo.get_source_by_id(source.source_id)
    assert updated is not None
    assert updated.consecutive_failures == 0
    assert updated.last_crawl_succeeded is True
    assert updated.etag == "etag-1"
    assert updated.last_modified == "Mon, 01 Jan 2026 00:00:00 GMT"
    assert updated.last_crawled_at is not None

    next_scheduled = updated.next_crawl_scheduled_at
    if next_scheduled.tzinfo is None:
        next_scheduled = next_scheduled.replace(tzinfo=timezone.utc)
    assert next_scheduled > datetime.now(timezone.utc)

    # Subsequent scheduler run does not select the source before that time
    subsequent_due = repo.get_active_sources(
        datetime.now(timezone.utc), max_retries=5
    )
    assert not any(
        s.source_id == source.source_id for s in subsequent_due
    )

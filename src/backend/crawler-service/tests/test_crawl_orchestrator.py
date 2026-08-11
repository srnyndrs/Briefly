import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.services.crawl_orchestrator import CrawlCycleOrchestrator


def _session_factory_with(session):
    session_factory = MagicMock()
    session_factory.return_value.__enter__.return_value = session
    return session_factory


@patch("src.services.crawl_orchestrator.RabbitMQEventPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.RedisCacheRepository")
@patch("src.services.crawl_orchestrator.SqlAlchemyFeedRepository")
def test_orchestrator_runs_crawl_and_updates_cache(
    mock_feed_repo_cls,
    mock_cache_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    feed = SimpleNamespace(
        feed_id=uuid.uuid4(),
        url="https://example.com/feed.xml",
        title="Test Feed",
        etag=None,
        last_modified=None,
        consecutive_failures=1,
    )

    feed_repository = MagicMock()
    feed_repository.get_active_feeds.return_value = [feed]
    mock_feed_repo_cls.return_value = feed_repository

    cache = MagicMock()
    cache.is_seen.return_value = False
    cache.get_etag.return_value = None
    cache.get_last_modified.return_value = None
    mock_cache_cls.return_value = cache

    http_client = MagicMock()
    http_client.fetch.return_value = SimpleNamespace(
        status_code=200,
        body="<xml>",
        etag="fresh-etag",
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
    event_publisher.publish_feed_fetched.assert_called_once()
    feed_repository.save_crawl_success.assert_called_once()

    cache.set_etag.assert_called_once_with(
        str(feed.feed_id), "fresh-etag"
    )
    cache.set_last_modified.assert_called_once_with(
        str(feed.feed_id),
        "Mon, 01 Jan 2026 00:00:00 GMT",
    )
    cache.mark_seen.assert_called_once_with(str(feed.feed_id))
    event_publisher.close.assert_called_once()


@patch("src.services.crawl_orchestrator.RabbitMQEventPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.RedisCacheRepository")
@patch("src.services.crawl_orchestrator.SqlAlchemyFeedRepository")
def test_orchestrator_skips_seen_feed(
    mock_feed_repo_cls,
    mock_cache_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    feed = SimpleNamespace(
        feed_id=uuid.uuid4(),
        url="https://example.com/feed.xml",
        title="Test Feed",
        etag=None,
        last_modified=None,
        consecutive_failures=0,
    )

    feed_repository = MagicMock()
    feed_repository.get_active_feeds.return_value = [feed]
    mock_feed_repo_cls.return_value = feed_repository

    cache = MagicMock()
    cache.is_seen.return_value = True
    mock_cache_cls.return_value = cache

    http_client = MagicMock()
    mock_http_client_cls.return_value = http_client

    event_publisher = MagicMock()
    mock_event_pub_cls.return_value = event_publisher

    orchestrator = CrawlCycleOrchestrator(
        session_factory=_session_factory_with(MagicMock())
    )
    orchestrator.run_crawl_cycle()

    http_client.fetch.assert_not_called()
    event_publisher.close.assert_called_once()


@patch("src.services.crawl_orchestrator.RabbitMQEventPublisher")
@patch("src.services.crawl_orchestrator.RequestsHttpClient")
@patch("src.services.crawl_orchestrator.RedisCacheRepository")
@patch("src.services.crawl_orchestrator.SqlAlchemyFeedRepository")
def test_orchestrator_shares_correlation_id_across_cycle(
    mock_feed_repo_cls,
    mock_cache_cls,
    mock_http_client_cls,
    mock_event_pub_cls,
):
    feed1 = SimpleNamespace(
        feed_id=uuid.uuid4(),
        url="https://example.com/f1.xml",
        title="Feed 1",
        etag=None,
        last_modified=None,
        consecutive_failures=0,
    )
    feed2 = SimpleNamespace(
        feed_id=uuid.uuid4(),
        url="https://example.com/f2.xml",
        title="Feed 2",
        etag=None,
        last_modified=None,
        consecutive_failures=0,
    )

    feed_repository = MagicMock()
    feed_repository.get_active_feeds.return_value = [feed1, feed2]
    mock_feed_repo_cls.return_value = feed_repository

    cache = MagicMock()
    cache.is_seen.return_value = False
    cache.get_etag.return_value = None
    cache.get_last_modified.return_value = None
    mock_cache_cls.return_value = cache

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

    assert event_publisher.publish_feed_fetched.call_count == 2
    call1_kwargs = event_publisher.publish_feed_fetched.call_args_list[0].kwargs
    call2_kwargs = event_publisher.publish_feed_fetched.call_args_list[1].kwargs

    assert call1_kwargs["correlation_id"] == call2_kwargs["correlation_id"]
    assert len(call1_kwargs["correlation_id"]) > 0

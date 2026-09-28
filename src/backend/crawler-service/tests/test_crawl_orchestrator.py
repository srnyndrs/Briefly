from datetime import timedelta

import pytest
import requests

from src.config.settings import settings


@pytest.mark.parametrize("status", [200, 304])
def test_crawl_success_persists_state(
    crawl_cycle, source_factory, db_session, status
):
    source = source_factory(
        etag="old", last_modified="old-date", consecutive_failures=2
    )
    orchestrator, http_get, publisher = crawl_cycle
    http_get.return_value.status_code = status
    orchestrator.run_crawl_cycle()
    db_session.refresh(source)

    assert source.last_crawl_succeeded is True
    assert source.consecutive_failures == 0
    assert source.last_crawled_at is not None
    assert (
        source.next_crawl_scheduled_at - source.last_crawled_at
        == timedelta(seconds=settings.unverified_crawl_interval_seconds)
    )
    headers = http_get.call_args.kwargs["headers"]
    assert headers["If-None-Match"] == "old"
    assert headers["If-Modified-Since"] == "old-date"
    assert (
        http_get.call_args.kwargs["timeout"]
        == settings.fetch_timeout_seconds
    )
    if status == 200:
        assert source.etag == "fresh"
        assert source.last_modified == "new-date"
        event = publisher.publish_source_fetched.call_args.kwargs
        assert event["source_id"] == source.source_id
        assert event["source_url"] == source.url
        assert event["source_title"] == source.title
        assert event["raw_xml"] == "<feed/>"
        assert event["correlation_id"]
    else:
        assert source.etag == "old"
        assert source.last_modified == "old-date"
        publisher.publish_source_fetched.assert_not_called()
    publisher.close.assert_called_once()


def test_feed_failure_retries_and_continues(
    crawl_cycle, source_factory, db_session
):
    first = source_factory(
        url="https://example.com/first", verified=True
    )
    second = source_factory(url="https://example.com/second")
    orchestrator, http_get, publisher = crawl_cycle
    response = http_get.return_value
    http_get.side_effect = [
        requests.Timeout("private detail"),
        response,
    ]
    orchestrator.run_crawl_cycle()
    db_session.refresh(first)
    db_session.refresh(second)

    assert first.last_crawl_succeeded is False
    assert first.consecutive_failures == 1
    assert (
        first.next_crawl_scheduled_at - first.last_crawled_at
        == timedelta(
            seconds=2 * settings.verified_crawl_interval_seconds
        )
    )
    assert second.last_crawl_succeeded is True
    publisher.publish_source_fetched.assert_called_once()
    assert (
        publisher.publish_source_fetched.call_args.kwargs["source_id"]
        == second.source_id
    )


def test_cycle_shares_correlation_id(crawl_cycle, source_factory):
    source_factory()
    source_factory()
    orchestrator, _, publisher = crawl_cycle
    orchestrator.run_crawl_cycle()
    events = publisher.publish_source_fetched.call_args_list
    assert len(events) == 2
    assert (
        events[0].kwargs["correlation_id"]
        == events[1].kwargs["correlation_id"]
    )


def test_idle_cycle_skips_external_services(crawl_cycle):
    orchestrator, http_get, publisher = crawl_cycle
    orchestrator.run_crawl_cycle()
    http_get.assert_not_called()
    publisher.publish_source_fetched.assert_not_called()
    publisher.close.assert_not_called()


@pytest.mark.parametrize("stage", ["publish", "database", "close"])
def test_infrastructure_failure_aborts_without_feed_retry(
    crawl_cycle, source_factory, db_session, monkeypatch, caplog, stage
):
    source = source_factory(
        url="https://example.com/feed?token=private"
    )
    orchestrator, _, publisher = crawl_cycle
    error = RuntimeError("private failure")
    if stage == "publish":
        publisher.publish_source_fetched.side_effect = error
        publisher.close.side_effect = RuntimeError("cleanup failure")
    elif stage == "database":

        def fail_commit(*args, **kwargs):
            raise error

        monkeypatch.setattr(
            "src.repositories.source_repository.SourceRepository.save_crawl_success",
            fail_commit,
        )
    else:
        publisher.close.side_effect = error

    with pytest.raises(RuntimeError, match="private failure"):
        orchestrator.run_crawl_cycle()
    db_session.refresh(source)
    assert source.consecutive_failures == 0
    assert source.last_crawl_succeeded is (stage == "close")
    publisher.close.assert_called_once()
    assert (
        sum(record.levelname == "ERROR" for record in caplog.records)
        == 1
    )
    assert "private" not in caplog.text


def test_deleted_source_is_skipped(
    crawl_cycle, source_factory, db_session, caplog
):
    source = source_factory()
    orchestrator, http_get, _ = crawl_cycle

    def delete_during_fetch(*args, **kwargs):
        db_session.delete(source)
        db_session.commit()
        raise requests.Timeout()

    http_get.side_effect = delete_during_fetch

    with caplog.at_level("INFO"):
        orchestrator.run_crawl_cycle()
    assert "failed=0, skipped=1" in caplog.text

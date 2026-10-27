from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import requests

from src.config.settings import settings
from src.repositories.source_repository import SourceRepository


@pytest.mark.parametrize("status", [200, 304])
def test_crawl_success_persists_state(
    crawl_cycle, source_factory, db_session, monkeypatch, status
):
    source = source_factory(
        etag="old",
        last_modified="old-date",
        consecutive_failures=2,
        title="Feed Title",
        site_name="Publisher Name",
    )
    orchestrator, http_get, publisher, _ = crawl_cycle
    http_get.return_value.status_code = status
    previous_schedule = source.next_crawl_scheduled_at

    def publish_before_state_advance(**event):
        db_session.refresh(source)
        assert source.etag == "old"
        assert source.last_modified == "old-date"
        assert source.consecutive_failures == 2
        assert source.last_crawled_at is None
        assert source.last_crawl_succeeded is False
        assert source.next_crawl_scheduled_at == previous_schedule

    order = []
    commit = SourceRepository.commit

    def record_commit(repository):
        order.append("commit")
        commit(repository)

    monkeypatch.setattr(SourceRepository, "commit", record_commit)

    def record_publish(channel, **kwargs):
        order.append("publish")
        publish_before_state_advance(**kwargs["envelope"]["payload"])

    publisher.side_effect = record_publish
    orchestrator.run_crawl_cycle()
    db_session.refresh(source)

    assert source.last_crawl_succeeded is True
    assert source.consecutive_failures == 0
    assert source.last_crawled_at is not None
    assert source.next_crawl_scheduled_at > source.last_crawled_at
    headers = http_get.call_args.kwargs["headers"]
    assert headers["If-None-Match"] == "old"
    assert headers["If-Modified-Since"] == "old-date"
    assert http_get.call_args.kwargs["timeout"] == settings.fetch_timeout_seconds
    if status == 200:
        assert order == ["publish", "commit"]
        assert source.etag == "fresh"
        assert source.last_modified == "new-date"
        event = publisher.call_args.kwargs["envelope"]["payload"]
        assert event["source_id"] == str(source.source_id)
        assert event["source_url"] == source.url
        assert event["source_title"] == "Publisher Name"
        assert event["raw_xml"] == "<feed/>"
        assert publisher.call_args.kwargs["envelope"]["correlation_id"]
    else:
        assert order == ["commit"]
        assert source.etag == "old"
        assert source.last_modified == "old-date"
        publisher.assert_not_called()
    publisher_factory = crawl_cycle[3]
    publisher_factory.assert_called_once()


def test_feed_failure_retries_and_continues(
    crawl_cycle, source_factory, db_session
):
    first = source_factory(url="https://example.com/first", verified=True)
    second = source_factory(url="https://example.com/second")
    orchestrator, http_get, publisher, _ = crawl_cycle
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
    assert first.next_crawl_scheduled_at > first.last_crawled_at
    assert second.last_crawl_succeeded is True
    publisher.assert_called_once()
    assert publisher.call_args.kwargs["envelope"]["payload"]["source_id"] == str(
        second.source_id
    )


def test_cycle_shares_correlation_id(crawl_cycle, source_factory):
    source_factory()
    source_factory()
    orchestrator, _, publisher, _ = crawl_cycle
    orchestrator.run_crawl_cycle()
    events = publisher.call_args_list
    assert len(events) == 2
    assert (
        events[0].kwargs["envelope"]["correlation_id"]
        == events[1].kwargs["envelope"]["correlation_id"]
    )


def test_idle_cycle_skips_external_services(crawl_cycle):
    orchestrator, http_get, publisher, publisher_factory = crawl_cycle
    orchestrator.run_crawl_cycle()
    publisher_factory.assert_not_called()
    http_get.assert_not_called()
    publisher.assert_not_called()


@pytest.mark.parametrize("stage", ["publish", "database"])
def test_infrastructure_failure_aborts_without_feed_retry(
    crawl_cycle, source_factory, db_session, monkeypatch, stage
):
    due = datetime.now(timezone.utc) - timedelta(minutes=1)
    source = source_factory(
        url="https://example.com/feed?token=private",
        etag="old",
        last_modified="old-date",
        next_crawl_scheduled_at=due,
        source_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"),
    )
    later = source_factory(
        next_crawl_scheduled_at=due,
        source_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2"),
    )
    previous_schedule = source.next_crawl_scheduled_at
    orchestrator, http_get, publisher, _ = crawl_cycle
    error = RuntimeError("publication or database failed")
    if stage == "publish":
        publisher.side_effect = error
    else:

        def fail_save(*args, **kwargs):
            raise error

        monkeypatch.setattr(
            "src.repositories.source_repository.SourceRepository.save_crawl_success",
            fail_save,
        )

    with pytest.raises(RuntimeError) as caught:
        orchestrator.run_crawl_cycle()
    assert caught.value is error
    db_session.refresh(source)
    db_session.refresh(later)
    assert source.consecutive_failures == 0
    assert source.last_crawl_succeeded is False
    assert source.last_crawled_at is None
    assert source.next_crawl_scheduled_at == previous_schedule
    assert source.etag == "old"
    assert source.last_modified == "old-date"
    http_get.assert_called_once()
    assert http_get.call_args.args == (source.url,)
    publisher.assert_called_once()
    assert publisher.call_args.kwargs["envelope"]["payload"]["source_id"] == str(
        source.source_id
    )
    assert later.last_crawled_at is None
    assert later.consecutive_failures == 0


def test_200_republishes_repeated_entries_with_unchanged_validators(
    crawl_cycle, source_factory
):
    source_factory(etag="old", last_modified="old-date")
    orchestrator, http_get, publisher, _ = crawl_cycle
    body = "<feed><entry id='same'/><entry id='same'/></feed>"
    http_get.return_value.text = body
    http_get.return_value.headers = {
        "ETag": "old",
        "Last-Modified": "old-date",
    }

    orchestrator.run_crawl_cycle()

    publisher.assert_called_once()
    assert publisher.call_args.kwargs["envelope"]["payload"]["raw_xml"] == body

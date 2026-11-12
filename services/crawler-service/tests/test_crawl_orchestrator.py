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
    orchestrator, _, publisher, publisher_factory = crawl_cycle
    orchestrator.run_crawl_cycle()
    events = publisher.call_args_list
    assert len(events) == 2
    assert (
        events[0].kwargs["envelope"]["correlation_id"]
        == events[1].kwargs["envelope"]["correlation_id"]
    )
    publisher_factory.assert_called_once()


def test_idle_cycle_skips_external_services(crawl_cycle):
    orchestrator, http_get, publisher, publisher_factory = crawl_cycle
    orchestrator.run_crawl_cycle()
    publisher_factory.assert_not_called()
    http_get.assert_not_called()
    publisher.assert_not_called()


@pytest.mark.parametrize("stage", ["publish", "commit"])
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

    def fail(*args, **kwargs):
        raise error

    if stage == "publish":
        publisher.side_effect = error
    else:
        monkeypatch.setattr(SourceRepository, "commit", fail)

    with pytest.raises(RuntimeError) as caught:
        orchestrator.run_crawl_cycle()
    assert caught.value is error
    assert orchestrator.wait_for_idle(timeout=0)
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


def test_sources_becoming_due_during_cycle_wait_for_next_cycle(
    crawl_cycle, source_factory, db_session, monkeypatch
):
    now = datetime.now(timezone.utc)
    first = source_factory(next_crawl_scheduled_at=now - timedelta(minutes=1))
    later = source_factory(next_crawl_scheduled_at=now + timedelta(seconds=1))
    orchestrator, http_get, _, _ = crawl_cycle
    response = http_get.return_value

    class Clock:
        @staticmethod
        def now(tz):
            return now

    monkeypatch.setattr("src.services.crawl_orchestrator.datetime", Clock)

    def advance_clock(url, **kwargs):
        nonlocal now
        now += timedelta(seconds=2)
        return response

    http_get.side_effect = advance_clock
    orchestrator.run_crawl_cycle()

    http_get.assert_called_once()
    assert http_get.call_args.args == (first.url,)
    db_session.refresh(later)
    assert later.last_crawled_at is None

    orchestrator.run_crawl_cycle()

    assert http_get.call_count == 2
    assert http_get.call_args.args == (later.url,)
    db_session.refresh(later)
    assert later.last_crawl_succeeded is True


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


def test_stop_finishes_current_source_and_leaves_remaining_sources_due(
    crawl_cycle, source_factory, db_session
):
    source_factory()
    source_factory()
    orchestrator, http_get, publisher, _ = crawl_cycle
    response = http_get.return_value
    fetched = []

    def stop_during_fetch(url, **kwargs):
        fetched.append(url)
        assert not orchestrator.wait_for_idle(timeout=0)
        orchestrator.stop()
        return response

    http_get.side_effect = stop_during_fetch
    orchestrator.run_crawl_cycle()
    assert orchestrator.wait_for_idle(timeout=0)
    http_get.assert_called_once()
    publisher.assert_called_once()
    sources = SourceRepository(db_session).get_active_sources(
        datetime.now(timezone.utc), settings.max_retries
    )
    assert len(sources) == 1
    assert sources[0].url not in fetched
    orchestrator.run_crawl_cycle()
    http_get.assert_called_once()

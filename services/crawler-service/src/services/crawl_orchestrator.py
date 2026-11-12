import logging
import threading
import uuid
from contextlib import ExitStack
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import requests
from sqlalchemy.orm import sessionmaker

from src.adapters.event_publisher import publish_event
from src.adapters.http_client import FetchHeaders, RequestsHttpClient
from src.config.message_broker import publisher_channel
from src.config.settings import settings
from src.events.feed_fetched import build_feed_fetched_event
from src.models.source import Source
from src.repositories.source_repository import SourceRepository

logger = logging.getLogger(__name__)


class CrawlCycleOrchestrator:
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._http_client = RequestsHttpClient()
        self._stop_event = threading.Event()
        self._idle = threading.Event()
        self._idle.set()

    def stop(self) -> None:
        self._stop_event.set()

    def wait_for_idle(self, timeout: float) -> bool:
        return self._idle.wait(timeout)

    def run_crawl_cycle(self) -> None:
        if self._stop_event.is_set():
            return
        self._idle.clear()
        try:
            if not self._stop_event.is_set():
                self._run_crawl_cycle(str(uuid.uuid4()))
        finally:
            self._idle.set()

    def _run_crawl_cycle(self, cycle_id: str) -> None:
        now = datetime.now(timezone.utc)
        counts = {
            "succeeded": 0,
            "not_modified": 0,
            "failed": 0,
        }
        logger.info("Crawl cycle started (cycle_id=%s)", cycle_id)

        with ExitStack() as stack:
            channel = None
            while not self._stop_event.is_set():
                with self._session_factory() as db:
                    source_repository = SourceRepository(db)
                    try:
                        source = source_repository.get_next_active_source(
                            now=now, max_retries=settings.max_retries
                        )
                        if source is None:
                            break
                        if self._stop_event.is_set():
                            source_repository.rollback()
                            break
                        if channel is None:
                            channel = stack.enter_context(
                                publisher_channel(exchange=settings.feed_exchange)
                            )
                        outcome = self._crawl_source(
                            source_repository,
                            channel,
                            source,
                            cycle_id,
                        )
                        source_repository.commit()
                    except Exception:
                        source_repository.rollback()
                        raise
                    counts[outcome] += 1

        if self._stop_event.is_set():
            logger.info("Crawl cycle stopped (cycle_id=%s)", cycle_id)
        logger.info(
            "Crawl cycle complete (cycle_id=%s, processed=%d, succeeded=%d, "
            "not_modified=%d, failed=%d)",
            cycle_id,
            sum(counts.values()),
            counts["succeeded"],
            counts["not_modified"],
            counts["failed"],
        )

    def _crawl_source(
        self,
        source_repository: SourceRepository,
        channel: Any,
        source: Source,
        correlation_id: str,
    ) -> str:
        headers = FetchHeaders(
            etag=source.etag,
            last_modified=source.last_modified,
        )
        try:
            result = self._http_client.fetch(source.url, headers)
        except requests.RequestException as exc:
            self._handle_failure(
                source_repository,
                source.source_id,
                source.url,
                correlation_id,
                exc,
            )

            return "failed"

        if result.status_code == 304:
            source_repository.save_crawl_success(
                source_id=source.source_id,
                etag=source.etag,
                last_modified=source.last_modified,
            )

            return "not_modified"

        envelope = build_feed_fetched_event(
            source_id=source.source_id,
            source_url=source.url,
            correlation_id=correlation_id,
            source_title=source.site_name or source.title,
            raw_xml=result.body,
        )
        publish_event(
            channel,
            exchange=settings.feed_exchange,
            envelope=envelope,
        )
        source_repository.save_crawl_success(
            source_id=source.source_id,
            etag=result.etag,
            last_modified=result.last_modified,
        )

        return "succeeded"

    @staticmethod
    def _handle_failure(
        source_repository: SourceRepository,
        source_id: UUID,
        source_url: str,
        cycle_id: str,
        error: requests.RequestException,
    ) -> None:
        host = urlsplit(source_url).hostname or "unknown"
        failures = source_repository.save_crawl_failure(source_id=source_id)
        logger.warning(
            "Feed request failed (source_id=%s, host=%s, cycle_id=%s, "
            "retry_count=%d): %s",
            source_id,
            host,
            cycle_id,
            failures,
            error,
        )
        if failures == settings.max_retries:
            logger.error(
                "Source suspended after retry limit (source_id=%s, host=%s, "
                "retry_count=%d, cycle_id=%s): %s",
                source_id,
                host,
                failures,
                cycle_id,
                error,
            )

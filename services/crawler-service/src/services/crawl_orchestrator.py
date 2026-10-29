import logging
import threading
import uuid
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
        with self._session_factory() as db:
            source_repository = SourceRepository(db)
            now = datetime.now(timezone.utc)
            sources = source_repository.get_active_sources(
                now, settings.max_retries
            )
            counts = {
                "succeeded": 0,
                "not_modified": 0,
                "failed": 0,
                "skipped": 0,
            }
            logger.info(
                "Crawl cycle started (cycle_id=%s, due=%d)",
                cycle_id,
                len(sources),
            )

            if self._stop_event.is_set():
                return
            if not sources:
                logger.info(
                    "Crawl cycle complete (cycle_id=%s, due=0, succeeded=0, "
                    "not_modified=0, failed=0, skipped=0)",
                    cycle_id,
                )
                return

            with publisher_channel(exchange=settings.feed_exchange) as channel:
                for source in sources:
                    if self._stop_event.is_set():
                        logger.info("Crawl cycle stopped (cycle_id=%s)", cycle_id)
                        return
                    outcome = self._crawl_source(
                        source_repository,
                        channel,
                        source,
                        cycle_id,
                    )
                    counts[outcome] += 1

            logger.info(
                "Crawl cycle complete (cycle_id=%s, due=%d, succeeded=%d, "
                "not_modified=%d, failed=%d, skipped=%d)",
                cycle_id,
                len(sources),
                counts["succeeded"],
                counts["not_modified"],
                counts["failed"],
                counts["skipped"],
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
            updated = self._handle_failure(
                source_repository,
                source.source_id,
                source.url,
                correlation_id,
                exc,
            )

            return "failed" if updated else "skipped"

        if result.status_code == 304:
            try:
                source_repository.save_crawl_success(
                    source_id=source.source_id,
                    etag=source.etag,
                    last_modified=source.last_modified,
                )
                source_repository.commit()
            except Exception:
                source_repository.rollback()
                raise

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
        try:
            source_repository.save_crawl_success(
                source_id=source.source_id,
                etag=result.etag,
                last_modified=result.last_modified,
            )
            source_repository.commit()
        except Exception:
            source_repository.rollback()
            raise

        return "succeeded"

    @staticmethod
    def _handle_failure(
        source_repository: SourceRepository,
        source_id: UUID,
        source_url: str,
        cycle_id: str,
        error: requests.RequestException,
    ) -> bool:
        host = urlsplit(source_url).hostname or "unknown"
        try:
            failures = source_repository.save_crawl_failure(source_id=source_id)
            source_repository.commit()
        except Exception:
            source_repository.rollback()
            raise
        if failures is None:
            logger.info(
                "Skipped failure update for deleted source (source_id=%s, "
                "host=%s, cycle_id=%s)",
                source_id,
                host,
                cycle_id,
            )

            return False

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

        return True

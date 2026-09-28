import logging
import traceback
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import UUID

import requests
import sentry_sdk
from sqlalchemy.orm import sessionmaker

from src.adapters.feed_publisher import FeedPublisher
from src.adapters.http_client import FetchHeaders, RequestsHttpClient
from src.config.settings import settings
from src.models.source import Source
from src.repositories.source_repository import SourceRepository

logger = logging.getLogger(__name__)


class CrawlCycleOrchestrator:
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._http_client = RequestsHttpClient()

    def run_crawl_cycle(self) -> None:
        cycle_id = str(uuid.uuid4())
        try:
            self._run_crawl_cycle(cycle_id)
        except Exception as exc:
            logger.error(
                "Crawl cycle failed (cycle_id=%s, error_type=%s)\n%s",
                cycle_id,
                type(exc).__name__,
                "".join(traceback.format_tb(exc.__traceback__)),
            )
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("cycle_id", cycle_id)
                sentry_sdk.capture_exception(exc)
            raise

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

            if not sources:
                logger.info(
                    "Crawl cycle complete (cycle_id=%s, due=0, succeeded=0, "
                    "not_modified=0, failed=0, skipped=0)",
                    cycle_id,
                )
                return

            event_publisher = FeedPublisher()
            try:
                for source in sources:
                    outcome = self._crawl_source(
                        source_repository,
                        event_publisher,
                        source,
                        cycle_id,
                    )
                    counts[outcome] += 1
            except BaseException:
                try:
                    event_publisher.close()
                except Exception:
                    logger.warning(
                        "Publisher cleanup failed after cycle error "
                        "(cycle_id=%s)",
                        cycle_id,
                    )
                raise
            else:
                event_publisher.close()

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
        event_publisher: FeedPublisher,
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
            source_repository.save_crawl_success(
                source_id=source.source_id,
                etag=source.etag,
                last_modified=source.last_modified,
            )
            return "not_modified"

        event_publisher.publish_source_fetched(
            source_id=source.source_id,
            source_url=source.url,
            correlation_id=correlation_id,
            source_title=source.title,
            raw_xml=result.body,
        )
        source_repository.save_crawl_success(
            source_id=source.source_id,
            etag=result.etag,
            last_modified=result.last_modified,
        )
        return "succeeded"

    def _handle_failure(
        self,
        source_repository: SourceRepository,
        source_id: UUID,
        source_url: str,
        cycle_id: str,
        error: requests.RequestException,
    ) -> bool:
        host = urlsplit(source_url).hostname or "unknown"
        failures = source_repository.save_crawl_failure(
            source_id=source_id
        )
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
            "retry_count=%d, error_type=%s)",
            source_id,
            host,
            cycle_id,
            failures,
            type(error).__name__,
        )
        if failures == settings.max_retries:
            logger.error(
                "Source suspended after retry limit (source_id=%s, host=%s, "
                "retry_count=%d, cycle_id=%s)",
                source_id,
                host,
                failures,
                cycle_id,
            )
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("source_id", str(source_id))
                scope.set_tag("source_host", host)
                scope.set_tag("cycle_id", cycle_id)
                sentry_sdk.capture_message(
                    "Source suspended after retry limit", level="error"
                )
        return True

import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import sessionmaker

from src.config.settings import settings
from src.models.source import Source
from src.adapters.http_client import FetchHeaders, RequestsHttpClient
from src.adapters.feed_publisher import FeedPublisher
from src.repositories.source_repository import SourceRepository

logger = logging.getLogger(__name__)


class CrawlCycleOrchestrator:
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._http_client = RequestsHttpClient()

    def run_crawl_cycle(self) -> None:
        cycle_correlation_id = str(uuid.uuid4())
        with self._session_factory() as db:
            source_repository = SourceRepository(db)
            now = datetime.now(timezone.utc)
            sources = source_repository.get_active_sources(
                now, settings.max_retries
            )

            logger.info(
                "Crawl cycle started (correlation_id=%s) - %d source(s) due.",
                cycle_correlation_id,
                len(sources),
            )

            if not sources:
                logger.info("Crawl cycle complete.")
                return

            event_publisher = FeedPublisher()
            try:
                for source in sources:
                    self._crawl_source(
                        source_repository,
                        event_publisher,
                        source,
                        cycle_correlation_id,
                    )
            finally:
                event_publisher.close()

            logger.info("Crawl cycle complete.")

    def _crawl_source(
        self,
        source_repository: SourceRepository,
        event_publisher: FeedPublisher,
        source: Source,
        correlation_id: str,
    ) -> None:
        headers = FetchHeaders(
            etag=source.etag,
            last_modified=source.last_modified,
        )

        try:
            result = self._http_client.fetch(source.url, headers)

            if result.status_code == 304:
                source_repository.save_crawl_success(
                    source_id=source.source_id,
                    etag=source.etag,
                    last_modified=source.last_modified,
                )
                return

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
        except Exception as exc:  # noqa: BLE001
            self._handle_failure(
                source_repository,
                source.source_id,
                source.url,
                str(exc),
            )

    def _handle_failure(
        self,
        source_repository: SourceRepository,
        source_id: UUID,
        source_url: str,
        error_message: str,
    ) -> None:
        logger.warning(
            "Crawl failed for source %s (%s): %s",
            source_id,
            source_url,
            error_message,
        )
        source_repository.save_crawl_failure(
            source_id=source_id,
        )

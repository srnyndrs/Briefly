import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID

import requests
from sqlalchemy.orm import sessionmaker

from src.config.settings import settings
from src.repositories.http_client import (
    FetchHeaders,
    RequestsHttpClient,
)
from src.repositories.message_publisher import (
    RabbitMQEventPublisher,
)
from src.repositories.source_repository import (
    SqlAlchemySourceRepository,
)

logger = logging.getLogger(__name__)


class CrawlCycleOrchestrator:
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._http_client = RequestsHttpClient()

    def run_crawl_cycle(self) -> None:
        cycle_correlation_id = str(uuid.uuid4())
        with self._session_factory() as db:
            source_repository = SqlAlchemySourceRepository(db)
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

            event_publisher = RabbitMQEventPublisher()
            try:
                for source in sources:
                    self._crawl_source(
                        source_repository,
                        event_publisher,
                        source.source_id,
                        source.url,
                        source.title,
                        source.etag,
                        source.last_modified,
                        source.consecutive_failures,
                        cycle_correlation_id,
                    )
            finally:
                event_publisher.close()

            logger.info("Crawl cycle complete.")

    def _crawl_source(
        self,
        source_repository: SqlAlchemySourceRepository,
        event_publisher: RabbitMQEventPublisher,
        source_id: UUID,
        source_url: str,
        source_title: str | None,
        etag: str | None,
        last_modified: str | None,
        retry_count: int,
        correlation_id: str,
    ) -> tuple[bool, str | None, str | None]:
        headers = FetchHeaders(etag=etag, last_modified=last_modified)

        try:
            result = self._http_client.fetch(source_url, headers)

            if result.status_code == 304:
                source_repository.save_crawl_success(
                    source_id=source_id,
                    etag=etag,
                    last_modified=last_modified,
                )
                return True, etag, last_modified

            event_publisher.publish_source_fetched(
                source_id=source_id,
                source_url=source_url,
                correlation_id=correlation_id,
                source_title=source_title,
                raw_xml=result.body,
            )

            source_repository.save_crawl_success(
                source_id=source_id,
                etag=result.etag,
                last_modified=result.last_modified,
            )

            return True, result.etag, result.last_modified

        except requests.exceptions.Timeout:
            self._handle_failure(
                source_repository,
                event_publisher,
                source_id,
                source_url,
                "TIMEOUT",
                "Request timed out",
                retry_count,
            )
            return False, None, None
        except requests.exceptions.ConnectionError as exc:
            self._handle_failure(
                source_repository,
                event_publisher,
                source_id,
                source_url,
                "NETWORK_ERROR",
                str(exc),
                retry_count,
            )
            return False, None, None
        except requests.exceptions.HTTPError as exc:
            self._handle_failure(
                source_repository,
                event_publisher,
                source_id,
                source_url,
                "HTTP_ERROR",
                str(exc),
                retry_count,
            )
            return False, None, None
        except Exception as exc:  # noqa: BLE001
            code = (
                "INVALID_XML"
                if "xml" in str(exc).lower()
                else "UNKNOWN_ERROR"
            )
            self._handle_failure(
                source_repository,
                event_publisher,
                source_id,
                source_url,
                code,
                str(exc),
                retry_count,
            )
            return False, None, None

    def _handle_failure(
        self,
        source_repository: SqlAlchemySourceRepository,
        event_publisher: RabbitMQEventPublisher,
        source_id: UUID,
        source_url: str,
        error_code: str,
        error_message: str,
        retry_count: int,
    ) -> None:
        _ = (event_publisher, source_url, error_code, retry_count)
        source_repository.save_crawl_failure(
            source_id=source_id,
            error=error_message,
        )

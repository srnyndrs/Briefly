import logging
from datetime import datetime, timezone
from uuid import UUID

import requests
from sqlalchemy.orm import sessionmaker

from src.config.settings import settings
from src.repositories.cache_repository import RedisCacheRepository
from src.repositories.feed_repository import (
    SqlAlchemyFeedRepository,
)
from src.repositories.http_client import (
    RequestsHttpClient,
    FetchHeaders,
)
from src.repositories.message_publisher import (
    RabbitMQEventPublisher,
)

logger = logging.getLogger(__name__)


class CrawlCycleOrchestrator:
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._cache = RedisCacheRepository()
        self._http_client = RequestsHttpClient()

    def run_crawl_cycle(self) -> None:
        event_publisher = RabbitMQEventPublisher()
        with self._session_factory() as db:
            feed_repository = SqlAlchemyFeedRepository(db)
            now = datetime.now(timezone.utc)
            feeds = feed_repository.get_active_feeds(
                now, settings.max_retries
            )

            logger.info(
                "Crawl cycle started - %d feed(s) due.", len(feeds)
            )

            try:
                for feed in feeds:
                    feed_id_str = str(feed.feed_id)
                    if self._cache.is_seen(feed_id_str):
                        logger.debug(
                            "Feed %s already published this window, skipping.",
                            feed_id_str,
                        )
                        continue

                    current_etag = (
                        self._cache.get_etag(feed_id_str)
                        or feed.etag
                    )
                    current_last_modified = (
                        self._cache.get_last_modified(feed_id_str)
                        or feed.last_modified
                    )

                    success, etag, last_modified = self._crawl_feed(
                        feed_repository,
                        event_publisher,
                        feed.feed_id,
                        feed.url,
                        feed.title,
                        current_etag,
                        current_last_modified,
                        feed.consecutive_failures,
                    )

                    if success:
                        if etag:
                            self._cache.set_etag(feed_id_str, etag)
                        if last_modified:
                            self._cache.set_last_modified(
                                feed_id_str, last_modified
                            )
                        self._cache.mark_seen(feed_id_str)
            finally:
                event_publisher.close()

            logger.info("Crawl cycle complete.")

    def _crawl_feed(
        self,
        feed_repository: SqlAlchemyFeedRepository,
        event_publisher: RabbitMQEventPublisher,
        feed_id: UUID,
        feed_url: str,
        source_title: str | None,
        etag: str | None,
        last_modified: str | None,
        retry_count: int,
    ) -> tuple[bool, str | None, str | None]:
        headers = FetchHeaders(
            etag=etag, last_modified=last_modified
        )

        try:
            result = self._http_client.fetch(feed_url, headers)

            if result.status_code == 304:
                return True, etag, last_modified

            event_publisher.publish_feed_fetched(
                feed_id=feed_id,
                feed_url=feed_url,
                source_title=source_title,
                raw_xml=result.body,
            )

            feed_repository.save_crawl_success(
                feed_id=feed_id,
                item_count=0,
                etag=result.etag,
                last_modified=result.last_modified,
            )

            return True, result.etag, result.last_modified

        except requests.exceptions.Timeout:
            self._handle_failure(
                feed_repository,
                event_publisher,
                feed_id,
                feed_url,
                "TIMEOUT",
                "Request timed out",
                retry_count,
            )
            return False, None, None
        except requests.exceptions.ConnectionError as exc:
            self._handle_failure(
                feed_repository,
                event_publisher,
                feed_id,
                feed_url,
                "NETWORK_ERROR",
                str(exc),
                retry_count,
            )
            return False, None, None
        except requests.exceptions.HTTPError as exc:
            self._handle_failure(
                feed_repository,
                event_publisher,
                feed_id,
                feed_url,
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
                feed_repository,
                event_publisher,
                feed_id,
                feed_url,
                code,
                str(exc),
                retry_count,
            )
            return False, None, None

    def _handle_failure(
        self,
        feed_repository: SqlAlchemyFeedRepository,
        event_publisher: RabbitMQEventPublisher,
        feed_id: UUID,
        feed_url: str,
        error_code: str,
        error_message: str,
        retry_count: int,
    ) -> None:
        _ = (event_publisher, feed_url, error_code, retry_count)
        feed_repository.save_crawl_failure(
            feed_id=feed_id,
            error=error_message,
        )

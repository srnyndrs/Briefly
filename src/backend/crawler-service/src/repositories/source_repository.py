import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.source import Source

HOURS = 3600


class SqlAlchemySourceRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_sources(self) -> list[Source]:
        return self._db.query(Source).all()

    def get_active_sources(
        self, now: datetime, max_retries: int
    ) -> list[Source]:
        sources = (
            self._db.query(Source)
            .filter(
                Source.next_crawl_scheduled_at <= now,
                Source.consecutive_failures < max_retries,
            )
            .order_by(Source.next_crawl_scheduled_at)
            .all()
        )
        return sources

    def get_source_by_id(self, source_id: UUID) -> Source | None:
        item = (
            self._db.query(Source)
            .filter(Source.source_id == source_id)
            .first()
        )
        if item is None:
            return None
        return item

    def get_source_by_url(self, url: str) -> Source | None:
        item = self._db.query(Source).filter(Source.url == url).first()
        if item is None:
            return None
        return item

    def create_source(
        self,
        *,
        url: str,
        title: str | None = None,
        description: str | None = None,
        favicon: str | None = None,
        website_url: str | None = None,
        enrich_with_ai: bool = False,
    ) -> Source:
        source = Source(
            source_id=uuid.uuid4(),
            url=url,
            title=title,
            description=description,
            favicon=favicon,
            website_url=website_url,
            enrich_with_ai=enrich_with_ai,
        )
        self._db.add(source)
        self._db.commit()
        self._db.refresh(source)
        return source

    def delete_source(self, source_id: UUID) -> bool:
        item = (
            self._db.query(Source)
            .filter(Source.source_id == source_id)
            .first()
        )
        if item is None:
            return False
        self._db.delete(item)
        self._db.commit()
        return True

    def update_source(
        self,
        *,
        source_id: UUID,
        url: str,
        title: str | None,
        description: str | None,
        favicon: str | None,
        website_url: str | None = None,
        enrich_with_ai: bool | None = None,
    ) -> Source | None:
        item = (
            self._db.query(Source)
            .filter(Source.source_id == source_id)
            .first()
        )
        if item is None:
            return None

        item.url = url
        item.title = title
        item.description = description
        item.favicon = favicon
        if website_url is not None:
            item.website_url = website_url
        if enrich_with_ai is not None:
            item.enrich_with_ai = enrich_with_ai
        item.updated_at = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(item)
        return item

    def save_crawl_success(
        self,
        *,
        source_id: UUID,
        etag: str | None,
        last_modified: str | None,
    ) -> None:
        source = (
            self._db.query(Source)
            .filter(Source.source_id == source_id)
            .first()
        )
        if not source:
            return

        now = datetime.now(timezone.utc)
        source.last_crawled_at = now
        source.last_crawl_succeeded = True
        source.consecutive_failures = 0
        source.etag = etag
        source.last_modified = last_modified
        source.next_crawl_scheduled_at = self._calculate_next_crawl(
            source, now
        )
        source.updated_at = now
        self._db.commit()

    def save_crawl_failure(
        self, *, source_id: UUID, error: str
    ) -> None:
        source = (
            self._db.query(Source)
            .filter(Source.source_id == source_id)
            .first()
        )
        if not source:
            return

        now = datetime.now(timezone.utc)
        source.last_crawled_at = now
        source.last_crawl_succeeded = False
        source.consecutive_failures += 1
        source.next_crawl_scheduled_at = self._calculate_next_crawl(
            source, now
        )
        source.updated_at = now
        self._db.commit()

    def _calculate_next_crawl(
        self, source: Source, now: datetime
    ) -> datetime:
        base = settings.base_crawl_interval_seconds
        if source.consecutive_failures > 0:
            backoff = 2**source.consecutive_failures
            interval = min(backoff * base, 24 * HOURS)
        else:
            interval = base
        return now + timedelta(seconds=interval)

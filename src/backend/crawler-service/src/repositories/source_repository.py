import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.source import Source

HOURS = 3600


class SourceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_sources(
        self, *, verified_only: bool = False
    ) -> list[Source]:
        query = self._db.query(Source)
        if verified_only:
            query = query.filter(Source.verified.is_(True))
        return query.order_by(
            Source.verified.desc(),
            func.lower(Source.title),
            Source.source_id,
        ).all()

    def get_sources_by_registrable_domain(
        self, registrable_domain: str
    ) -> list[Source]:
        return (
            self._db.query(Source)
            .filter(Source.registrable_domain == registrable_domain)
            .order_by(Source.source_id)
            .all()
        )

    def get_active_sources(
        self, now: datetime, max_retries: int
    ) -> list[Source]:
        sources = (
            self._db.query(Source)
            .filter(
                Source.next_crawl_scheduled_at <= now,
                Source.consecutive_failures < max_retries,
            )
            .order_by(
                Source.verified.desc(),
                Source.next_crawl_scheduled_at,
                Source.source_id,
            )
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
        title: str,
        description: str | None = None,
        favicon: str | None = None,
        website_url: str | None = None,
        registrable_domain: str,
        verified: bool = False,
        submitted_by_user_id: UUID | None = None,
    ) -> Source:
        source = Source(
            source_id=uuid.uuid4(),
            url=url,
            title=title,
            description=description,
            favicon=favicon,
            website_url=website_url,
            registrable_domain=registrable_domain,
            verified=verified,
            submitted_by_user_id=submitted_by_user_id,
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
        description: str | None,
        favicon: str | None,
        website_url: str | None = None,
    ) -> Source | None:
        item = (
            self._db.query(Source)
            .filter(Source.source_id == source_id)
            .first()
        )
        if item is None:
            return None

        item.url = url
        item.description = description
        item.favicon = favicon
        if website_url is not None:
            item.website_url = website_url
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

    def save_crawl_failure(self, *, source_id: UUID) -> None:
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
        base = (
            settings.verified_crawl_interval_seconds
            if source.verified
            else settings.unverified_crawl_interval_seconds
        )
        if source.consecutive_failures > 0:
            backoff = 2**source.consecutive_failures
            interval = min(backoff * base, 24 * HOURS)
        else:
            interval = base
        return now + timedelta(seconds=interval)

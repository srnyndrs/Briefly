import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.source import Source


class SourceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_sources(self, *, verified_only: bool = False) -> list[Source]:
        query = self._db.query(Source)
        if verified_only:
            query = query.filter(Source.verified.is_(True))

        return query.order_by(
            Source.verified.desc(),
            func.lower(Source.title),
            Source.source_id,
        ).all()

    def get_active_sources(
        self,
        now: datetime,
        max_retries: int,
        *,
        verified_only: bool = False,
    ) -> list[Source]:
        query = self._db.query(Source).filter(
            Source.next_crawl_scheduled_at <= now,
            Source.consecutive_failures < max_retries,
        )

        if verified_only:
            query = query.filter(Source.verified.is_(True))

        query = query.order_by(
            Source.verified.desc(),
            Source.next_crawl_scheduled_at,
            Source.source_id,
        )

        return query.all()

    def get_source_by_id(self, source_id: UUID) -> Source | None:
        return (
            self._db.query(Source).filter(Source.source_id == source_id).first()
        )

    def get_source_by_url(self, url: str) -> Source | None:
        return self._db.query(Source).filter(Source.url == url).first()

    def create_source(
        self,
        *,
        url: str,
        title: str,
        description: str | None = None,
        favicon: str | None = None,
        website_url: str | None = None,
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
            verified=verified,
            submitted_by_user_id=submitted_by_user_id,
        )

        self._db.add(source)
        self._db.commit()
        self._db.refresh(source)

        return source

    def delete_source(self, source_id: UUID) -> bool:
        item = self.get_source_by_id(source_id)
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
        title: str,
        description: str | None,
        favicon: str | None,
        verified: bool,
    ) -> Source | None:
        item = self.get_source_by_id(source_id)
        if item is None:
            return None

        item.url = url
        item.title = title
        item.description = description
        item.favicon = favicon
        item.verified = verified
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
        source = self.get_source_by_id(source_id)
        if not source:
            return

        now = datetime.now(timezone.utc)
        source.last_crawled_at = now
        source.last_crawl_succeeded = True
        source.consecutive_failures = 0
        source.etag = etag
        source.last_modified = last_modified
        source.next_crawl_scheduled_at = self._calculate_next_crawl(source, now)
        source.updated_at = now

        self._db.commit()

    def save_crawl_failure(self, *, source_id: UUID) -> int | None:
        source = self.get_source_by_id(source_id)
        if not source:
            return None

        now = datetime.now(timezone.utc)
        source.last_crawled_at = now
        source.last_crawl_succeeded = False
        source.consecutive_failures += 1
        source.next_crawl_scheduled_at = self._calculate_next_crawl(source, now)
        source.updated_at = now

        self._db.commit()

        return source.consecutive_failures

    @staticmethod
    def _calculate_next_crawl(source: Source, now: datetime) -> datetime:
        base = (
            settings.verified_crawl_interval_seconds
            if source.verified
            else settings.unverified_crawl_interval_seconds
        )
        if source.consecutive_failures > 0:
            backoff = 2**source.consecutive_failures
            interval = min(backoff * base, timedelta(days=1).total_seconds())
        else:
            interval = base

        return now + timedelta(seconds=interval)

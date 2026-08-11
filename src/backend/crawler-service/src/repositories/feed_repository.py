import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.feed import Feed

HOURS = 3600


class SqlAlchemyFeedRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_feeds(self) -> list[Feed]:
        return self._db.query(Feed).all()

    def get_active_feeds(
        self, now: datetime, max_retries: int
    ) -> list[Feed]:
        feeds = (
            self._db.query(Feed)
            .filter(
                Feed.next_crawl_scheduled_at <= now,
                Feed.consecutive_failures < max_retries,
            )
            .order_by(Feed.next_crawl_scheduled_at)
            .all()
        )
        return feeds

    def get_feed_by_id(self, feed_id: UUID) -> Feed | None:
        item = (
            self._db.query(Feed)
            .filter(Feed.feed_id == feed_id)
            .first()
        )
        if item is None:
            return None
        return item

    def get_feed_by_url(self, url: str) -> Feed | None:
        item = self._db.query(Feed).filter(Feed.url == url).first()
        if item is None:
            return None
        return item

    def create_feed(
        self,
        *,
        url: str,
        title: str | None = None,
        description: str | None = None,
        favicon: str | None = None,
        website_url: str | None = None,
    ) -> Feed:
        feed = Feed(
            feed_id=uuid.uuid4(),
            url=url,
            title=title,
            description=description,
            favicon=favicon,
            website_url=website_url,
        )
        self._db.add(feed)
        self._db.commit()
        self._db.refresh(feed)
        return feed

    def delete_feed(self, feed_id: UUID) -> bool:
        item = (
            self._db.query(Feed)
            .filter(Feed.feed_id == feed_id)
            .first()
        )
        if item is None:
            return False
        self._db.delete(item)
        self._db.commit()
        return True

    def update_feed(
        self,
        *,
        feed_id: UUID,
        url: str,
        title: str | None,
        description: str | None,
        favicon: str | None,
        website_url: str | None = None,
    ) -> Feed | None:
        item = (
            self._db.query(Feed)
            .filter(Feed.feed_id == feed_id)
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
        item.updated_at = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(item)
        return item

    def save_crawl_success(
        self,
        *,
        feed_id: UUID,
        item_count: int,
        etag: str | None,
        last_modified: str | None,
    ) -> None:
        feed = (
            self._db.query(Feed)
            .filter(Feed.feed_id == feed_id)
            .first()
        )
        if not feed:
            return

        now = datetime.now(timezone.utc)
        feed.last_crawled_at = now
        feed.last_crawl_succeeded = True
        feed.consecutive_failures = 0
        feed.etag = etag
        feed.last_modified = last_modified
        feed.next_crawl_scheduled_at = self._calculate_next_crawl(
            feed
        )
        feed.updated_at = now
        self._db.commit()

    def save_crawl_failure(
        self, *, feed_id: UUID, error: str
    ) -> None:
        feed = (
            self._db.query(Feed)
            .filter(Feed.feed_id == feed_id)
            .first()
        )
        if not feed:
            return

        now = datetime.now(timezone.utc)
        feed.last_crawled_at = now
        feed.last_crawl_succeeded = False
        feed.consecutive_failures += 1
        feed.health_score = max(
            0.0, 0.95**feed.consecutive_failures
        )
        feed.next_crawl_scheduled_at = self._calculate_next_crawl(
            feed
        )
        feed.updated_at = now
        self._db.commit()

    def _calculate_next_crawl(self, feed: Feed) -> datetime:
        base = settings.base_crawl_interval_seconds
        if feed.health_score < 0.5:
            backoff = 2**feed.consecutive_failures
            interval = min(backoff * base, 24 * HOURS)
        else:
            interval = base
        return datetime.now(timezone.utc) + timedelta(
            seconds=interval
        )

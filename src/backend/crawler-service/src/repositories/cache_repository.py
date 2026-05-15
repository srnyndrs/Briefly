"""Redis cache adapter."""

import redis as redis_lib

from src.config.settings import settings


class RedisCacheRepository:
    """Adapter for Redis-backed crawl metadata cache."""

    def __init__(self) -> None:
        self._client = redis_lib.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )

    def get_etag(self, feed_id: str) -> str | None:
        return self._client.get(f"feed:{feed_id}:etag")

    def set_etag(self, feed_id: str, etag: str) -> None:
        self._client.set(
            f"feed:{feed_id}:etag",
            etag,
            ex=settings.etag_ttl_seconds,
        )

    def get_last_modified(self, feed_id: str) -> str | None:
        return self._client.get(f"feed:{feed_id}:last_modified")

    def set_last_modified(self, feed_id: str, value: str) -> None:
        self._client.set(
            f"feed:{feed_id}:last_modified",
            value,
            ex=settings.etag_ttl_seconds,
        )

    def mark_seen(
        self, feed_id: str, ttl: int | None = None
    ) -> None:
        item_ttl = ttl or settings.crawl_interval_seconds
        self._client.set(f"feed:{feed_id}:seen", "1", ex=item_ttl)

    def is_seen(self, feed_id: str) -> bool:
        return self._client.exists(f"feed:{feed_id}:seen") == 1

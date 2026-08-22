import redis as redis_lib

from src.config.settings import settings


class RedisCacheRepository:
    def __init__(self) -> None:
        self._client = redis_lib.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )

    def get_etag(self, source_id: str) -> str | None:
        return self._client.get(f"source:{source_id}:etag")

    def set_etag(self, source_id: str, etag: str) -> None:
        self._client.set(
            f"source:{source_id}:etag",
            etag,
            ex=settings.etag_ttl_seconds,
        )

    def get_last_modified(self, source_id: str) -> str | None:
        return self._client.get(f"source:{source_id}:last_modified")

    def set_last_modified(self, source_id: str, value: str) -> None:
        self._client.set(
            f"source:{source_id}:last_modified",
            value,
            ex=settings.etag_ttl_seconds,
        )

    def mark_seen(
        self, source_id: str, ttl: int | None = None
    ) -> None:
        item_ttl = ttl or settings.crawl_interval_seconds
        self._client.set(f"source:{source_id}:seen", "1", ex=item_ttl)

    def is_seen(self, source_id: str) -> bool:
        return self._client.exists(f"source:{source_id}:seen") == 1

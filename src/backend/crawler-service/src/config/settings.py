"""
Centralised configuration via environment variables.
Copy `.env.example` to `.env` and adjust values for local development.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    env: str = "production"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    log_level: str = "INFO"

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/briefly"
    )

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    # TTL for ETag / Last-Modified cache entries (7 days)
    etag_ttl_seconds: int = 7 * 24 * 3600

    # ── RabbitMQ ──────────────────────────────────────────────────────────────
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    feed_exchange: str = "feed.content"

    # ── Crawler behavior ────────────────────────────────────────────────────
    # How often (seconds) the scheduler triggers a full crawl cycle
    crawl_interval_seconds: int = 300
    # HTTP request timeout for fetching a single feed
    fetch_timeout_seconds: int = 30
    # Maximum consecutive failures before a feed is suspended
    max_retries: int = 5
    # Base crawl interval in seconds (used by health-score scheduler)
    base_crawl_interval_seconds: int = 300


# Singleton instance imported by all other modules
settings = Settings()

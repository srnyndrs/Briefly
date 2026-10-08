from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    log_level: str = "INFO"
    sentry_dsn: str | None = None

    database_url: str = "postgresql://postgres:postgres@localhost:5432/briefly"

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    feed_exchange: str = "feed.content"

    # How often the scheduler triggers a full crawl cycle
    crawl_interval_seconds: int = 300
    # HTTP request timeout for fetching a single feed
    fetch_timeout_seconds: int = 30
    source_validation_timeout_seconds: int = 10
    source_validation_max_bytes: int = 1_048_576
    # Maximum consecutive failures before a feed is suspended
    max_retries: int = 5
    verified_crawl_interval_seconds: int = 300
    unverified_crawl_interval_seconds: int = 1800


settings = Settings()

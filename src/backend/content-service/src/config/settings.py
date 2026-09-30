from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8002
    log_level: str = "INFO"
    sentry_dsn: str | None = None

    database_url: str = "postgresql://postgres:postgres@localhost:5432/briefly"

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    feed_exchange: str = "feed.content"
    feed_queue: str = "feed.raw_fetched.v1.parser"
    parsed_exchange: str = "content.parsed"
    failed_exchange: str = "content.failed"
    feed_dlq: str = "feed.raw_fetched.v1.parser.dlq"
    blocked_timeout_seconds: int = 5
    article_request_timeout_seconds: int = 5

    admin_token: str | None = None


settings = Settings()

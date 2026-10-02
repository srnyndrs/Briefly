from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8005
    log_level: str = "INFO"
    sentry_dsn: str | None = None

    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/briefly"
    )
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    parsed_exchange: str = "content.parsed"
    failed_exchange: str = "enrichment.failed"
    post_queue: str = "enrichment.posts.v1"
    post_dlq: str = "enrichment.posts.v1.dlq"
    post_failed_routing_key: str = "post.failed"
    blocked_timeout_seconds: int = 5
    post_consumer_enabled: bool = False


settings = Settings()

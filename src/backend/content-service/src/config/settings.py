from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "production"
    app_host: str = "0.0.0.0"
    app_port: int = 8002
    log_level: str = "INFO"

    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/briefly"
    )

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    feed_exchange: str = "feed.content"
    feed_queue: str = "feed.raw_fetched.v1.parser"
    parsed_exchange: str = "content.parsed"

    admin_token: str | None = None


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8002
    log_level: str = "INFO"
    env: str = "production"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    feed_exchange: str = "feed.content"
    feed_queue: str = "feed.raw_fetched.v1.parser"
    parsed_exchange: str = "content.parsed"

    # Database
    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/briefly"
    )


settings = Settings()

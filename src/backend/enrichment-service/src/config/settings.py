from pydantic import Field
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
    gemini_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str | None = Field(default=None, max_length=200)
    ollama_timeout_seconds: float = Field(default=60, gt=0, le=300)

    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/briefly"
    )
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    parsed_exchange: str = "content.parsed"
    result_exchange: str = "enrichment.events"
    failed_exchange: str = "enrichment.failed"
    post_queue: str = "enrichment.posts.v1"
    post_dlq: str = "enrichment.posts.v1.dlq"
    post_failed_routing_key: str = "post.failed"
    blocked_timeout_seconds: int = 5


settings = Settings()

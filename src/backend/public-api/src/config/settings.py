from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    env: str = "production"

    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/briefly"
    )

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    account_exchange: str = "account.events"
    content_exchange: str = "content.parsed"
    query_queue: str = "public-api.query.v1"
    query_consumer_enabled: bool = True

    jwt_secret: str = "local-dev-secret-change-me"
    jwt_issuer: str = "briefly-account-service"
    jwt_audience: str = "briefly-public-api"

    account_service_url: str = "http://localhost:8003"
    ingestion_service_url: str = "http://localhost:8001"
    content_service_url: str = "http://localhost:8002"
    request_timeout_seconds: float = 10.0


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8003
    log_level: str = "INFO"
    env: str = "production"

    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/briefly"
    )
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    account_exchange: str = "account.events"

    jwt_secret: str = "change-me-in-env"
    jwt_issuer: str = "briefly-account-service"
    jwt_audience: str = "briefly-public-api"
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_seconds: int = 2_592_000
    password_reset_token_ttl_seconds: int = 3600
    admin_emails_csv: str = "alice@example.com"


settings = Settings()

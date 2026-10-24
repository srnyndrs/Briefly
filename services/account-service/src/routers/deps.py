import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from src.adapters.event_publisher import publish_event
from src.adapters.password_reset_mailer import PasswordResetMailer
from src.config.database import get_db
from src.config.message_broker import publisher_channel
from src.config.settings import settings
from src.repositories.account_repository import AccountRepository
from src.services.account_service import AccountService
from src.services.auth_service import AuthService


def get_account_repository(
    db: Session = Depends(get_db),
) -> AccountRepository:
    return AccountRepository(db)


def get_auth_service(
    repo: AccountRepository = Depends(get_account_repository),
) -> AuthService:
    return AuthService(repo)


def get_event_publisher() -> Callable[[dict[str, Any]], None]:
    def publish(envelope: dict[str, Any]) -> None:
        with publisher_channel(exchange=settings.account_exchange) as channel:
            publish_event(
                channel,
                exchange=settings.account_exchange,
                envelope=envelope,
            )

    return publish


def get_password_reset_mailer() -> PasswordResetMailer:
    return PasswordResetMailer()


def get_account_service(
    repo: AccountRepository = Depends(get_account_repository),
    auth_service: AuthService = Depends(get_auth_service),
    publisher: Callable[[dict[str, Any]], None] = Depends(get_event_publisher),
    mailer: PasswordResetMailer = Depends(get_password_reset_mailer),
) -> AccountService:
    return AccountService(repo, auth_service, publisher, mailer)


def correlation_id(value: str | None) -> str:
    return value or str(uuid.uuid4())

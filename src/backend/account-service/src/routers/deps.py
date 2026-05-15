import uuid

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.repositories.account_repository import AccountRepository
from src.repositories.event_publisher import EventPublisher
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


def get_event_publisher(request: Request) -> EventPublisher:
    return request.app.state.publisher


def get_account_service(
    repo: AccountRepository = Depends(get_account_repository),
    auth_service: AuthService = Depends(get_auth_service),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> AccountService:
    return AccountService(repo, auth_service, publisher)


def correlation_id(value: str | None) -> str:
    return value or str(uuid.uuid4())


def trace_ids(request_id: str) -> tuple[str, str]:
    return request_id, uuid.uuid4().hex[:16]

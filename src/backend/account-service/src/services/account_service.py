import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from src.adapters.account_event_publisher import (
    AccountEventPublisher,
)
from src.adapters.password_reset_mailer import (
    PasswordResetDeliveryError,
    PasswordResetMailer,
)
from src.models.account import User, UserPreferences, UserSubscription
from src.repositories.account_repository import AccountRepository
from src.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class ConflictError(Exception):
    pass


class NotFoundError(Exception):
    pass


class AccountService:
    def __init__(
        self,
        repo: AccountRepository,
        auth_service: AuthService,
        publisher: AccountEventPublisher,
        mailer: PasswordResetMailer,
    ) -> None:
        self._repo = repo
        self._auth_service = auth_service
        self._publisher = publisher
        self._mailer = mailer

    def register_user(
        self,
        *,
        email: str,
        password: str,
    ) -> tuple[str, str]:
        existing = self._repo.get_user_by_email(email)
        if existing:
            raise ConflictError("Email already registered")

        now = utc_now_naive()
        user_id = str(uuid.uuid4())
        password_hash = self._auth_service.hash_password(password)
        user = self._repo.create_user(
            user_id=user_id,
            email=email,
            password_hash=password_hash,
            now=now,
        )
        self._repo.create_default_preferences(user.user_id)
        return self._auth_service.issue_token_pair(user_id=user.user_id)

    def password_reset_request(self, email: str) -> None:
        reset = self._auth_service.create_password_reset(email=email)
        if reset is None:
            return

        user_email, reset_token = reset
        try:
            self._mailer.send(email=user_email, reset_token=reset_token)
        except PasswordResetDeliveryError:
            logger.exception(
                "Password reset delivery failed",
                extra={"email": user_email},
            )

    def get_user(self, user_id: str) -> User:
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def patch_display_name(
        self, *, user_id: str, fields: dict[str, Any]
    ) -> User:
        if "display_name" not in fields:
            return self.get_user(user_id)
        user = self._repo.update_display_name(
            user_id=user_id,
            display_name=fields["display_name"],
            now=utc_now_naive(),
        )
        if user is None:
            raise NotFoundError("User not found")
        return user

    def get_preferences(self, user_id: str) -> UserPreferences:
        preferences = self._repo.get_preferences(user_id)
        if preferences is None:
            raise NotFoundError("User preferences not found")
        return preferences

    def update_preferences(
        self,
        *,
        user_id: str,
        muted_keywords: list[str],
        muted_categories: list[str],
        blocked_source_ids: list[str],
        languages: list[str],
        correlation_id: str,
    ) -> UserPreferences:
        self.get_user(user_id)

        preferences = self._repo.upsert_preferences(
            user_id=user_id,
            muted_keywords=muted_keywords,
            muted_categories=muted_categories,
            blocked_source_ids=blocked_source_ids,
            languages=languages,
            now=utc_now_naive(),
        )

        self._publisher.publish(
            event_type="preferences.updated.v1",
            correlation_id=correlation_id,
            partition_key=f"user:{user_id}",
            payload={
                "user_id": user_id,
                "updated_at": preferences.updated_at.isoformat() + "Z",
                "muted_keywords": preferences.muted_keywords,
                "muted_categories": preferences.muted_categories,
                "blocked_source_ids": preferences.blocked_source_ids,
                "languages": preferences.languages,
            },
        )

        return preferences

    def patch_preferences(
        self,
        *,
        user_id: str,
        fields: dict[str, Any],
        correlation_id: str,
    ) -> UserPreferences:
        preferences = self.get_preferences(user_id)

        return self.update_preferences(
            user_id=user_id,
            muted_keywords=fields.get(
                "muted_keywords", preferences.muted_keywords
            )
            or [],
            muted_categories=fields.get(
                "muted_categories", preferences.muted_categories
            )
            or [],
            blocked_source_ids=[
                str(value)
                for value in fields.get(
                    "blocked_source_ids",
                    preferences.blocked_source_ids,
                )
                or []
            ],
            languages=fields.get("languages", preferences.languages)
            or [],
            correlation_id=correlation_id,
        )

    def create_subscription(
        self,
        *,
        user_id: str,
        source_id: str,
    ) -> UserSubscription:
        self.get_user(user_id)
        if self._repo.has_subscription(
            user_id=user_id, source_id=source_id
        ):
            raise ConflictError("Subscription already exists")

        return self._repo.create_subscription(
            user_id=user_id,
            source_id=source_id,
            now=utc_now_naive(),
        )

    def list_subscriptions(
        self, user_id: str
    ) -> Sequence[UserSubscription]:
        self.get_user(user_id)
        return self._repo.list_subscriptions(user_id=user_id)

    def delete_subscription(
        self,
        *,
        user_id: str,
        source_id: str,
    ) -> None:
        deleted = self._repo.delete_subscription(
            user_id=user_id, source_id=source_id
        )
        if not deleted:
            raise NotFoundError("Subscription not found")


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)

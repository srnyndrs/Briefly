import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import sentry_sdk

from src.adapters.password_reset_mailer import (
    PasswordResetDeliveryError,
    PasswordResetMailer,
)
from src.events.preferences_updated import build_preferences_updated_event
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
        publisher: Callable[[dict[str, Any]], None],
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

        now = datetime.now(UTC)
        user_id = uuid4()
        password_hash = self._auth_service.hash_password(password)
        user = self._repo.create_user(
            user_id=user_id,
            email=email,
            password_hash=password_hash,
            now=now,
        )
        try:
            self._repo.flush()
            self._repo.create_default_preferences(user.user_id)
            tokens = self._auth_service.issue_token_pair(user_id=user.user_id)
            self._repo.commit()
            return tokens
        except Exception:
            self._repo.rollback()
            raise

    def password_reset_request(self, email: str) -> None:
        reset = self._auth_service.create_password_reset(email=email)
        if reset is None:
            return

        user_email, reset_token = reset
        try:
            self._mailer.send(email=user_email, reset_token=reset_token)
        except PasswordResetDeliveryError as exc:
            logger.exception("Password reset delivery failed")
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("operation", "password_reset_delivery")
                sentry_sdk.capture_exception(exc)

    def get_user(self, user_id: UUID) -> User:
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def patch_display_name(
        self, *, user_id: UUID, fields: dict[str, Any]
    ) -> User:
        if "display_name" not in fields:
            return self.get_user(user_id)
        user = self._repo.update_display_name(
            user_id=user_id,
            display_name=fields["display_name"],
            now=datetime.now(UTC),
        )
        if user is None:
            raise NotFoundError("User not found")
        try:
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return user

    def get_preferences(self, user_id: UUID) -> UserPreferences:
        preferences = self._repo.get_preferences(user_id)
        if preferences is None:
            raise NotFoundError("User preferences not found")
        return preferences

    def update_preferences(
        self,
        *,
        user_id: UUID,
        muted_keywords: list[str],
        muted_categories: list[str],
        blocked_source_ids: list[str],
        languages: list[str],
        correlation_id: str,
    ) -> UserPreferences:
        self.get_user(user_id)

        try:
            preferences = self._repo.upsert_preferences(
                user_id=user_id,
                muted_keywords=muted_keywords,
                muted_categories=muted_categories,
                blocked_source_ids=blocked_source_ids,
                languages=languages,
                now=datetime.now(UTC),
            )
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise

        envelope = build_preferences_updated_event(
            preferences=preferences,
            correlation_id=correlation_id,
        )
        try:
            self._publisher(envelope)
        except Exception as exc:
            logger.exception("Failed to publish preferences updated event")
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("operation", "publish_account_event")
                scope.set_tag("event_type", envelope["event_type"])
                sentry_sdk.capture_exception(exc)

        return preferences

    def patch_preferences(
        self,
        *,
        user_id: UUID,
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
            languages=fields.get("languages", preferences.languages) or [],
            correlation_id=correlation_id,
        )

    def create_subscription(
        self,
        *,
        user_id: UUID,
        source_id: UUID,
    ) -> UserSubscription:
        self.get_user(user_id)
        if self._repo.has_subscription(user_id=user_id, source_id=source_id):
            raise ConflictError("Subscription already exists")

        try:
            subscription = self._repo.create_subscription(
                user_id=user_id,
                source_id=source_id,
                now=datetime.now(UTC),
            )
            self._repo.flush()
            self._repo.commit()
            return subscription
        except Exception:
            self._repo.rollback()
            raise

    def list_subscriptions(self, user_id: UUID) -> list[UserSubscription]:
        self.get_user(user_id)
        return self._repo.list_subscriptions(user_id=user_id)

    def delete_subscription(
        self,
        *,
        user_id: UUID,
        source_id: UUID,
    ) -> None:
        deleted = self._repo.delete_subscription(
            user_id=user_id, source_id=source_id
        )
        if not deleted:
            raise NotFoundError("Subscription not found")
        try:
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise

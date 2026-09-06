import uuid
from datetime import UTC, datetime
from typing import Any

from src.adapters.account_event_publisher import (
    AccountEventPublisher,
)
from src.repositories.account_repository import AccountRepository
from src.services.auth_service import AuthService


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
    ) -> None:
        self._repo = repo
        self._auth_service = auth_service
        self._publisher = publisher

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
        self._repo.create_default_profile(user.user_id)
        self._repo.create_default_preferences(user.user_id)
        return self._auth_service.issue_token_pair(user_id=user.user_id)

    def login(self, *, email: str, password: str) -> tuple[str, str]:
        return self._auth_service.login(email=email, password=password)

    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        return self._auth_service.refresh_tokens(refresh_token)

    def password_reset_request(self, email: str) -> str | None:
        return self._auth_service.generate_password_reset_token(
            email=email
        )

    def password_reset_confirm(
        self, *, reset_token: str, new_password: str
    ) -> None:
        self._auth_service.reset_password(
            reset_token=reset_token, new_password=new_password
        )

    def logout(
        self,
        *,
        refresh_token: str,
        reason: str = "logout",
    ) -> None:
        _ = reason
        self._auth_service.revoke_refresh_token(refresh_token)

    def get_user(self, user_id: str):
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def get_profile(self, user_id: str):
        profile = self._repo.get_profile(user_id)
        if profile is None:
            raise NotFoundError("User profile not found")
        return profile

    def update_profile(
        self,
        *,
        user_id: str,
        display_name: str | None,
        bio: str | None,
        avatar_url: str | None,
    ):
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        profile = self._repo.upsert_profile(
            user_id=user_id,
            display_name=display_name,
            bio=bio,
            avatar_url=avatar_url,
            now=utc_now_naive(),
        )

        return profile

    def patch_profile(self, *, user_id: str, fields: dict[str, Any]):
        profile = self._repo.get_profile(user_id)
        if profile is None:
            raise NotFoundError("User profile not found")

        return self.update_profile(
            user_id=user_id,
            display_name=(
                fields["display_name"]
                if "display_name" in fields
                else profile.display_name
            ),
            bio=fields["bio"] if "bio" in fields else profile.bio,
            avatar_url=(
                fields["avatar_url"]
                if "avatar_url" in fields
                else profile.avatar_url
            ),
        )

    def get_preferences(self, user_id: str):
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
        category_interests: list[str],
        correlation_id: str,
    ):
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        preferences = self._repo.upsert_preferences(
            user_id=user_id,
            muted_keywords=muted_keywords,
            muted_categories=muted_categories,
            blocked_source_ids=blocked_source_ids,
            languages=languages,
            category_interests=category_interests,
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
                "category_interests": preferences.category_interests,
            },
        )

        return preferences

    def patch_preferences(
        self,
        *,
        user_id: str,
        fields: dict[str, Any],
        correlation_id: str,
    ):
        preferences = self._repo.get_preferences(user_id)
        if preferences is None:
            raise NotFoundError("User preferences not found")

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
            category_interests=fields.get(
                "category_interests", preferences.category_interests
            )
            or [],
            correlation_id=correlation_id,
        )

    def create_subscription(
        self,
        *,
        user_id: str,
        source_id: str,
    ):
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if self._repo.has_subscription(
            user_id=user_id, source_id=source_id
        ):
            raise ConflictError("Subscription already exists")

        return self._repo.create_subscription(
            user_id=user_id,
            source_id=source_id,
            now=utc_now_naive(),
        )

    def list_subscriptions(self, user_id: str):
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

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

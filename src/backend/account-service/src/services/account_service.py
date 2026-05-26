import uuid
from datetime import UTC, datetime

from src.repositories.account_repository import AccountRepository
from src.repositories.event_publisher import EventPublisher
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
        publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._auth_service = auth_service
        self._publisher = publisher

    def register_user(
        self,
        *,
        username: str | None,
        email: str,
        password: str,
        correlation_id: str,
        trace_id: str,
        span_id: str,
    ) -> tuple[str, str]:
        existing = self._repo.get_user_by_email(email)
        if existing:
            raise ConflictError("Email already registered")

        now = utc_now_naive()
        user_id = str(uuid.uuid4())
        password_hash = self._auth_service.hash_password(password)
        effective_username = (
            username if username else email.split("@")[0]
        )
        user = self._repo.create_user(
            user_id=user_id,
            username=effective_username,
            email=email,
            password_hash=password_hash,
            now=now,
        )
        self._repo.create_default_profile(user.user_id)
        self._repo.create_default_preferences(user.user_id)
        access_token, refresh_token = (
            self._auth_service.issue_token_pair(
                user_id=user.user_id,
                token_version=user.token_version,
            )
        )

        self._publisher.publish(
            event_type="account.created.v1",
            correlation_id=correlation_id,
            partition_key=f"user:{user.user_id}",
            trace_id=trace_id,
            span_id=span_id,
            payload={
                "user_id": user.user_id,
                "email": user.email,
                "created_at": user.created_at.isoformat() + "Z",
                "status": user.status,
            },
        )
        return access_token, refresh_token

    def login(
        self, *, email: str, password: str
    ) -> tuple[str, str]:
        user_id, token_version = (
            self._auth_service.authenticate_user(
                email=email, password=password
            )
        )
        return self._auth_service.issue_token_pair(
            user_id=user_id, token_version=token_version
        )

    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        _, _, token_pair = self._auth_service.refresh_tokens(
            refresh_token
        )
        return token_pair

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
        reason: str,
        correlation_id: str,
        trace_id: str,
        span_id: str,
    ) -> None:
        user_id, token_version = (
            self._auth_service.revoke_refresh_token(refresh_token)
        )
        now = datetime.now(UTC)
        self._publisher.publish(
            event_type="account.token_revoked.v1",
            correlation_id=correlation_id,
            partition_key=f"user:{user_id}",
            trace_id=trace_id,
            span_id=span_id,
            payload={
                "user_id": user_id,
                "token_version": token_version,
                "revoked_at": now.isoformat(),
                "reason": reason,
            },
        )

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
        correlation_id: str,
        trace_id: str,
        span_id: str,
    ):
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        profile, changed_fields = self._repo.upsert_profile(
            user_id=user_id,
            display_name=display_name,
            bio=bio,
            avatar_url=avatar_url,
            now=utc_now_naive(),
        )
        self._repo.update_user_timestamp(user_id, utc_now_naive())

        if changed_fields:
            self._publisher.publish(
                event_type="account.updated.v1",
                correlation_id=correlation_id,
                partition_key=f"user:{user_id}",
                trace_id=trace_id,
                span_id=span_id,
                payload={
                    "user_id": user_id,
                    "updated_at": profile.updated_at.isoformat()
                    + "Z",
                    "changed_fields": changed_fields,
                },
            )

        return profile

    def get_preferences(self, user_id: str):
        preferences = self._repo.get_preferences(user_id)
        if preferences is None:
            raise NotFoundError("User preferences not found")
        return preferences

    def update_preferences(
        self,
        *,
        user_id: str,
        preferred_categories: list[str],
        preferred_languages: list[str],
        excluded_languages: list[str],
        blocked_source_ids: list[str],
        correlation_id: str,
        trace_id: str,
        span_id: str,
    ):
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        preferences = self._repo.upsert_preferences(
            user_id=user_id,
            preferred_categories=preferred_categories,
            preferred_languages=preferred_languages,
            excluded_languages=excluded_languages,
            blocked_source_ids=blocked_source_ids,
            now=utc_now_naive(),
        )
        self._repo.update_user_timestamp(user_id, utc_now_naive())

        self._publisher.publish(
            event_type="preferences.updated.v1",
            correlation_id=correlation_id,
            partition_key=f"user:{user_id}",
            trace_id=trace_id,
            span_id=span_id,
            payload={
                "user_id": user_id,
                "updated_at": preferences.updated_at.isoformat()
                + "Z",
                "preferred_categories": preferences.preferred_categories,
                "preferred_languages": preferences.preferred_languages,
                "excluded_languages": preferences.excluded_languages,
                "blocked_source_ids": preferences.blocked_source_ids,
            },
        )

        return preferences

    def create_subscription(
        self,
        *,
        user_id: str,
        source_id: str,
        correlation_id: str,
        trace_id: str,
        span_id: str,
    ):
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if self._repo.has_subscription(
            user_id=user_id, source_id=source_id
        ):
            raise ConflictError("Subscription already exists")

        created = self._repo.create_subscription(
            user_id=user_id,
            source_id=source_id,
            now=utc_now_naive(),
        )
        self._publisher.publish(
            event_type="subscription.created.v1",
            correlation_id=correlation_id,
            partition_key=f"user:{user_id}",
            trace_id=trace_id,
            span_id=span_id,
            payload={
                "user_id": user_id,
                "source_id": source_id,
                "created_at": created.created_at.isoformat() + "Z",
            },
        )
        return created

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
        correlation_id: str,
        trace_id: str,
        span_id: str,
    ) -> None:
        deleted = self._repo.delete_subscription(
            user_id=user_id, source_id=source_id
        )
        if not deleted:
            raise NotFoundError("Subscription not found")

        self._publisher.publish(
            event_type="subscription.deleted.v1",
            correlation_id=correlation_id,
            partition_key=f"user:{user_id}",
            trace_id=trace_id,
            span_id=span_id,
            payload={
                "user_id": user_id,
                "source_id": source_id,
                "deleted_at": datetime.now(UTC).isoformat(),
            },
        )


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.account import (
    RefreshToken,
    User,
    UserPreferences,
    UserProfile,
    UserSubscription,
)


class AccountRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self._db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._db.execute(
            select(User).where(User.user_id == user_id)
        ).scalar_one_or_none()

    def create_user(
        self,
        *,
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        now: datetime,
    ) -> User:
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            status="active",
            token_version=0,
            created_at=now,
            updated_at=now,
        )
        self._db.add(user)
        return user

    def create_default_profile(self, user_id: str) -> None:
        self._db.add(UserProfile(user_id=user_id))

    def get_profile(self, user_id: str) -> UserProfile | None:
        return self._db.execute(
            select(UserProfile).where(
                UserProfile.user_id == user_id
            )
        ).scalar_one_or_none()

    def upsert_profile(
        self,
        *,
        user_id: str,
        display_name: str | None,
        bio: str | None,
        avatar_url: str | None,
        now: datetime,
    ) -> UserProfile:
        profile = self.get_profile(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self._db.add(profile)

        profile.display_name = display_name
        profile.bio = bio
        profile.avatar_url = avatar_url
        profile.updated_at = now

        user = self.get_user_by_id(user_id)
        if user is not None:
            user.updated_at = now

        self._db.commit()
        return profile

    def create_default_preferences(self, user_id: str) -> None:
        self._db.add(UserPreferences(user_id=user_id))

    def get_preferences(
        self, user_id: str
    ) -> UserPreferences | None:
        return self._db.execute(
            select(UserPreferences).where(
                UserPreferences.user_id == user_id
            )
        ).scalar_one_or_none()

    def upsert_preferences(
        self,
        *,
        user_id: str,
        muted_keywords: list[str],
        muted_categories: list[str],
        blocked_source_ids: list[str],
        languages: list[str],
        category_interests: list[str],
        now: datetime,
    ) -> UserPreferences:
        preferences = self.get_preferences(user_id)
        if preferences is None:
            preferences = UserPreferences(user_id=user_id)
            self._db.add(preferences)

        preferences.muted_keywords = muted_keywords
        preferences.muted_categories = muted_categories
        preferences.blocked_source_ids = blocked_source_ids
        preferences.languages = languages
        preferences.category_interests = category_interests
        preferences.updated_at = now

        user = self.get_user_by_id(user_id)
        if user is not None:
            user.updated_at = now

        self._db.commit()
        return preferences

    def create_subscription(
        self, *, user_id: str, source_id: str, now: datetime
    ) -> UserSubscription:
        subscription = UserSubscription(
            user_id=user_id,
            source_id=source_id,
            created_at=now,
        )
        self._db.add(subscription)
        self._db.commit()
        self._db.refresh(subscription)
        return subscription

    def list_subscriptions(self, *, user_id: str) -> Sequence[Any]:
        return (
            self._db.execute(
                select(UserSubscription)
                .where(UserSubscription.user_id == user_id)
                .order_by(UserSubscription.created_at.desc())
            )
            .scalars()
            .all()
        )

    def has_subscription(
        self, *, user_id: str, source_id: str
    ) -> bool:
        subscription = self._db.execute(
            select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.source_id == source_id,
            )
        ).scalar_one_or_none()
        return subscription is not None

    def delete_subscription(
        self, *, user_id: str, source_id: str
    ) -> bool:
        subscription = self._db.execute(
            select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.source_id == source_id,
            )
        ).scalar_one_or_none()
        if subscription is None:
            return False
        self._db.delete(subscription)
        self._db.commit()
        return True

    def get_refresh_token(
        self, token_id: str
    ) -> RefreshToken | None:
        return self._db.execute(
            select(RefreshToken).where(
                RefreshToken.token_id == token_id
            )
        ).scalar_one_or_none()

    def list_active_refresh_tokens(
        self, user_id: str
    ) -> Sequence[Any]:
        return (
            self._db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            .scalars()
            .all()
        )

    def add_refresh_token(self, token: RefreshToken) -> None:
        self._db.add(token)
        self._db.commit()

    def commit(self) -> None:
        self._db.commit()

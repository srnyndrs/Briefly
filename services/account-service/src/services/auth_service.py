import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from authlib.jose import JoseError, jwt
from passlib.context import CryptContext

from src.config.settings import settings
from src.models.account import RefreshToken, User
from src.repositories.account_repository import AccountRepository


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, repo: AccountRepository) -> None:
        self._repo = repo
        self._pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def login(self, *, email: str, password: str) -> tuple[str, str]:
        user = self._authenticate_user(email=email, password=password)
        try:
            tokens = self.issue_token_pair(user_id=user.user_id)
            self._repo.commit()
            return tokens
        except Exception:
            self._repo.rollback()
            raise

    def _authenticate_user(self, *, email: str, password: str) -> User:
        user = self._repo.get_user_by_email(email)
        if user is None or not self._pwd_context.verify(
            password, user.password_hash
        ):
            raise AuthError("Invalid credentials")
        return user

    def issue_token_pair(self, *, user_id: UUID) -> tuple[str, str]:
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise AuthError("User not found")
        scopes = self._scopes_for_user(user)

        refresh_id = uuid4()
        access_claims = self._build_claims(
            user_id=str(user.user_id),
            token_type="access",
            ttl_seconds=settings.access_token_ttl_seconds,
            scopes=scopes,
        )
        refresh_claims = self._build_claims(
            user_id=str(user.user_id),
            token_type="refresh",
            ttl_seconds=settings.refresh_token_ttl_seconds,
            token_id=refresh_id,
            scopes=scopes,
        )
        access_token = self._encode_token(access_claims)
        refresh_token = self._encode_token(refresh_claims)

        expires_at = self._utc_now() + timedelta(
            seconds=settings.refresh_token_ttl_seconds
        )
        self._repo.add_refresh_token(
            RefreshToken(
                token_id=refresh_id,
                user_id=user.user_id,
                token_hash=self._token_hash(refresh_token),
                expires_at=expires_at,
            )
        )
        return access_token, refresh_token

    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        claims = self._decode_token(refresh_token)
        if claims.get("type") != "refresh":
            raise AuthError("Invalid refresh token")

        try:
            token_id = UUID(claims.get("jti", ""))
            user_id = UUID(claims.get("sub", ""))
        except (ValueError, TypeError):
            raise AuthError("Invalid refresh token")

        stored = self._repo.get_refresh_token(token_id)
        if stored is None:
            raise AuthError("Refresh token not found")
        if stored.revoked_at is not None:
            raise AuthError("Refresh token already revoked")
        if self._as_utc(stored.expires_at) < self._utc_now():
            raise AuthError("Refresh token expired")
        if stored.token_hash != self._token_hash(refresh_token):
            raise AuthError("Refresh token mismatch")

        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise AuthError("User not found")
        try:
            stored.revoked_at = self._utc_now()
            tokens = self.issue_token_pair(user_id=user.user_id)
            self._repo.commit()
            return tokens
        except Exception:
            self._repo.rollback()
            raise

    def revoke_refresh_token(self, refresh_token: str) -> None:
        claims = self._decode_token(refresh_token)
        if claims.get("type") != "refresh":
            raise AuthError("Invalid refresh token")

        try:
            token_id = UUID(claims.get("jti", ""))
            UUID(claims.get("sub", ""))
        except (ValueError, TypeError):
            raise AuthError("Invalid refresh token")

        stored = self._repo.get_refresh_token(token_id)
        if stored is None:
            raise AuthError("Refresh token not found")
        if stored.token_hash != self._token_hash(refresh_token):
            raise AuthError("Refresh token mismatch")

        try:
            stored.revoked_at = self._utc_now()
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise

    def create_password_reset(self, *, email: str) -> tuple[str, str] | None:
        user = self._repo.get_user_by_email(email)
        if user is None:
            return None

        reset_token = secrets.token_urlsafe(32)
        now = self._utc_now()
        try:
            self._repo.replace_password_reset_token(
                user_id=user.user_id,
                token_hash=self._token_hash(reset_token),
                expires_at=now
                + timedelta(seconds=settings.password_reset_token_ttl_seconds),
                created_at=now,
            )
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return user.email, reset_token

    def reset_password(self, *, reset_token: str, new_password: str) -> None:
        stored = self._repo.get_password_reset_token(
            self._token_hash(reset_token), lock=True
        )
        if stored is None:
            raise AuthError("Invalid password reset token")

        now = self._utc_now()
        if self._as_utc(stored.expires_at) <= now:
            raise AuthError("Invalid password reset token")

        user = self._repo.get_user_by_id(stored.user_id)
        if user is None:
            raise AuthError("Invalid password reset token")
        try:
            user.password_hash = self.hash_password(new_password)
            self._repo.revoke_active_refresh_tokens(user.user_id, now)
            self._repo.delete_password_reset_token(user.user_id)
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _build_claims(
        *,
        user_id: str,
        token_type: str,
        ttl_seconds: int,
        token_id: UUID | None = None,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        now = AuthService._utc_now()
        claims: dict[str, Any] = {
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
            "type": token_type,
        }
        if token_id:
            claims["jti"] = str(token_id)
        if scopes:
            claims["scopes"] = scopes
        return claims

    @staticmethod
    def _scopes_for_user(user: User) -> list[str]:
        configured_admin_ids = {
            uuid.UUID(user_id.strip())
            for user_id in settings.admin_user_ids_csv.split(",")
            if user_id.strip()
        }
        if user.user_id in configured_admin_ids:
            return ["admin"]
        return []

    @staticmethod
    def _encode_token(claims: dict[str, Any]) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        return jwt.encode(header, claims, settings.jwt_secret).decode("utf-8")

    @staticmethod
    def _decode_token(token: str) -> dict[str, Any]:
        try:
            claims = jwt.decode(token, settings.jwt_secret)
            claims.validate()
            return dict(claims)
        except JoseError as exc:
            raise AuthError("Invalid token") from exc

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

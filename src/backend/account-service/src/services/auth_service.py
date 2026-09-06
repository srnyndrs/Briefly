import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

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
        self._pwd_context = CryptContext(
            schemes=["argon2"], deprecated="auto"
        )

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def login(
        self, *, email: str, password: str
    ) -> tuple[str, str]:
        user = self._authenticate_user(
            email=email, password=password
        )
        return self.issue_token_pair(user_id=user.user_id)

    def _authenticate_user(
        self, *, email: str, password: str
    ) -> User:
        user = self._repo.get_user_by_email(email)
        if user is None or not self._pwd_context.verify(
            password, user.password_hash
        ):
            raise AuthError("Invalid credentials")
        if user.status != "active":
            raise AuthError("User account is not active")
        return user

    def issue_token_pair(self, *, user_id: str) -> tuple[str, str]:
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise AuthError("User not found")
        scopes = self._scopes_for_user(user)

        refresh_id = str(uuid.uuid4())
        access_claims = self._build_claims(
            user_id=user.user_id,
            token_type="access",
            ttl_seconds=settings.access_token_ttl_seconds,
            token_version=user.token_version,
            scopes=scopes,
        )
        refresh_claims = self._build_claims(
            user_id=user.user_id,
            token_type="refresh",
            ttl_seconds=settings.refresh_token_ttl_seconds,
            token_version=user.token_version,
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
                expires_at=expires_at.replace(tzinfo=None),
            )
        )
        return access_token, refresh_token

    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        claims = self._decode_token(refresh_token)
        if claims.get("type") != "refresh":
            raise AuthError("Invalid refresh token")

        token_id = claims.get("jti")
        user_id = claims.get("sub")
        token_version = claims.get("tv")
        if not token_id or not user_id:
            raise AuthError("Invalid refresh token")

        stored = self._repo.get_refresh_token(token_id)
        if stored is None:
            raise AuthError("Refresh token not found")
        if stored.revoked_at is not None:
            raise AuthError("Refresh token already revoked")
        if stored.expires_at < self._utc_now().replace(tzinfo=None):
            raise AuthError("Refresh token expired")
        if stored.token_hash != self._token_hash(refresh_token):
            raise AuthError("Refresh token mismatch")

        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise AuthError("User not found")
        if user.token_version != token_version:
            raise AuthError("Refresh token token-version mismatch")

        stored.revoked_at = self._utc_now().replace(tzinfo=None)
        self._repo.commit()
        return self.issue_token_pair(user_id=user.user_id)

    def revoke_refresh_token(self, refresh_token: str) -> None:
        claims = self._decode_token(refresh_token)
        if claims.get("type") != "refresh":
            raise AuthError("Invalid refresh token")

        token_id = claims.get("jti")
        user_id = claims.get("sub")
        if not token_id or not user_id:
            raise AuthError("Invalid refresh token")

        stored = self._repo.get_refresh_token(token_id)
        if stored is None:
            raise AuthError("Refresh token not found")
        if stored.token_hash != self._token_hash(refresh_token):
            raise AuthError("Refresh token mismatch")

        stored.revoked_at = self._utc_now().replace(tzinfo=None)
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise AuthError("User not found")

        user.token_version += 1
        self._repo.commit()

    def generate_password_reset_token(
        self, *, email: str
    ) -> str | None:
        user = self._repo.get_user_by_email(email)
        if user is None or user.status != "active":
            return None

        claims = self._build_claims(
            user_id=user.user_id,
            token_type="password_reset",
            ttl_seconds=settings.password_reset_token_ttl_seconds,
            token_version=user.token_version,
            token_id=str(uuid.uuid4()),
        )
        return self._encode_token(claims)

    def reset_password(
        self, *, reset_token: str, new_password: str
    ) -> None:
        claims = self._decode_token(reset_token)
        if claims.get("type") != "password_reset":
            raise AuthError("Invalid password reset token")

        user_id = claims.get("sub")
        if not user_id:
            raise AuthError("Invalid password reset token")

        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise AuthError("User not found")
        if user.status != "active":
            raise AuthError("User account is not active")

        now = self._utc_now().replace(tzinfo=None)
        user.password_hash = self.hash_password(new_password)
        user.token_version += 1

        active_tokens = self._repo.list_active_refresh_tokens(
            user_id=user.user_id
        )
        for token in active_tokens:
            token.revoked_at = now

        self._repo.commit()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _build_claims(
        *,
        user_id: str,
        token_type: str,
        ttl_seconds: int,
        token_version: int,
        token_id: str | None = None,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        now = AuthService._utc_now()
        claims: dict[str, Any] = {
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int(
                (now + timedelta(seconds=ttl_seconds)).timestamp()
            ),
            "type": token_type,
            "tv": token_version,
        }
        if token_id:
            claims["jti"] = token_id
        if scopes:
            claims["scopes"] = scopes
        return claims

    @staticmethod
    def _scopes_for_user(user: User) -> list[str]:
        configured_admins = {
            email.strip().lower()
            for email in settings.admin_emails_csv.split(",")
            if email.strip()
        }
        if user.email.lower() in configured_admins:
            return ["admin"]
        return []

    @staticmethod
    def _encode_token(claims: dict[str, Any]) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        return jwt.encode(
            header, claims, settings.jwt_secret
        ).decode("utf-8")

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

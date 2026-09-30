from datetime import UTC, datetime, timedelta

from authlib.jose import jwt
from sqlalchemy import select

from src.config.settings import settings
from src.models.account import (
    PasswordResetToken,
    RefreshToken,
    User,
    UserPreferences,
)
from src.repositories.account_repository import AccountRepository
from src.services.auth_service import AuthService


def test_registration_and_login(
    client, credentials, monkeypatch, db_session
) -> None:
    registered = client.post("/auth/register", json=credentials)
    assert registered.status_code == 201
    tokens = registered.json()
    assert tokens["token_type"] == "Bearer"
    for token_type in ("access", "refresh"):
        claims = jwt.decode(tokens[f"{token_type}_token"], settings.jwt_secret)
        claims.validate()
        assert claims["type"] == token_type
        assert claims["iss"] == settings.jwt_issuer
        assert claims["aud"] == settings.jwt_audience
        assert not claims.get("scopes")
    account_id = claims["sub"]
    assert db_session.get(User, account_id) is not None
    assert db_session.get(UserPreferences, account_id) is not None
    refresh_claims = jwt.decode(tokens["refresh_token"], settings.jwt_secret)
    assert db_session.get(RefreshToken, refresh_claims["jti"]) is not None

    assert client.post("/auth/register", json=credentials).status_code == 409
    assert (
        client.post(
            "/auth/login",
            json={**credentials, "password": "wrong-password"},
        ).status_code
        == 401
    )

    monkeypatch.setattr(settings, "admin_user_ids_csv", account_id)
    login = client.post("/auth/login", json=credentials)
    assert login.status_code == 200
    claims = jwt.decode(login.json()["access_token"], settings.jwt_secret)
    claims.validate()
    assert claims["scopes"] == ["admin"]


def test_admin_scope_uses_current_configured_user_ids(
    client, credentials, monkeypatch
) -> None:
    registered = client.post("/auth/register", json=credentials)
    assert registered.status_code == 201
    claims = jwt.decode(registered.json()["access_token"], settings.jwt_secret)
    claims.validate()
    user_id = claims["sub"]

    monkeypatch.setattr(settings, "admin_user_ids_csv", f"{user_id}")
    listed_login = client.post("/auth/login", json=credentials)
    listed_claims = jwt.decode(
        listed_login.json()["access_token"], settings.jwt_secret
    )
    listed_claims.validate()
    assert listed_claims["scopes"] == ["admin"]

    monkeypatch.setattr(settings, "admin_user_ids_csv", "")
    unlisted_login = client.post("/auth/login", json=credentials)
    unlisted_claims = jwt.decode(
        unlisted_login.json()["access_token"], settings.jwt_secret
    )
    unlisted_claims.validate()
    assert not unlisted_claims.get("scopes")


def test_refresh_rotation_and_logout(client, account, credentials) -> None:
    other_session = client.post("/auth/login", json=credentials)
    assert other_session.status_code == 200
    original = {"refresh_token": account["refresh_token"]}
    rotated = client.post("/auth/refresh", json=original)
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != original["refresh_token"]
    assert client.post("/auth/refresh", json=original).status_code == 401
    current = {"refresh_token": rotated.json()["refresh_token"]}
    assert client.post("/auth/logout", json=current).status_code == 204
    assert client.post("/auth/refresh", json=current).status_code == 401
    assert (
        client.post(
            "/auth/refresh",
            json={"refresh_token": other_session.json()["refresh_token"]},
        ).status_code
        == 200
    )


def test_failed_refresh_rotation_rolls_back_revocation(
    account, db_session, monkeypatch
) -> None:
    repository = AccountRepository(db_session)
    service = AuthService(repository)
    claims = AuthService._decode_token(account["refresh_token"])

    def fail_after_staging(token: RefreshToken) -> None:
        db_session.add(token)
        raise RuntimeError("token staging failed")

    monkeypatch.setattr(repository, "add_refresh_token", fail_after_staging)
    try:
        service.refresh_tokens(account["refresh_token"])
    except RuntimeError as exc:
        assert str(exc) == "token staging failed"
    else:
        raise AssertionError("refresh rotation should fail")

    db_session.expire_all()
    original = db_session.get(RefreshToken, claims["jti"])
    assert original is not None
    assert original.revoked_at is None
    assert (
        len(
            db_session.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == account["user_id"]
                )
            )
            .scalars()
            .all()
        )
        == 1
    )


def test_failed_password_reset_rolls_back_all_changes(
    client, account, mailer, db_session, monkeypatch
) -> None:
    response = client.post(
        "/auth/password-reset/request", json={"email": account["email"]}
    )
    assert response.status_code == 202
    reset_token = mailer.messages[0]["reset_token"]
    user = db_session.get(User, account["user_id"])
    assert user is not None
    original_password_hash = user.password_hash

    repository = AccountRepository(db_session)
    service = AuthService(repository)

    def fail_commit() -> None:
        raise RuntimeError("commit failed")

    monkeypatch.setattr(repository, "commit", fail_commit)
    try:
        service.reset_password(
            reset_token=reset_token, new_password="updated-password"
        )
    except RuntimeError as exc:
        assert str(exc) == "commit failed"
    else:
        raise AssertionError("password reset should fail")

    db_session.expire_all()
    user = db_session.get(User, account["user_id"])
    assert user is not None
    assert user.password_hash == original_password_hash
    assert db_session.get(PasswordResetToken, account["user_id"]) is not None
    active_tokens = (
        db_session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == account["user_id"],
                RefreshToken.revoked_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    assert active_tokens


def test_invalid_refresh_tokens(client, account) -> None:
    for token in ("invalid-token", account["access_token"]):
        for path in ("/auth/refresh", "/auth/logout"):
            response = client.post(path, json={"refresh_token": token})
            assert response.status_code == 401


def test_password_reset(client, account, credentials, mailer) -> None:
    other_session = client.post("/auth/login", json=credentials)
    assert other_session.status_code == 200
    for email in (account["email"], "unknown@example.com"):
        response = client.post(
            "/auth/password-reset/request", json={"email": email}
        )
        assert response.status_code == 202
        assert response.json() == {"status": "accepted"}
    assert len(mailer.messages) == 1
    assert mailer.messages[0]["email"] == account["email"]

    confirmation = {
        "reset_token": mailer.messages[0]["reset_token"],
        "new_password": "updated-password",
    }
    confirmed = client.post("/auth/password-reset/confirm", json=confirmation)
    assert confirmed.status_code == 200
    assert confirmed.json() == {"status": "ok"}
    assert (
        client.post(
            "/auth/password-reset/confirm", json=confirmation
        ).status_code
        == 401
    )
    for token in (
        account["refresh_token"],
        other_session.json()["refresh_token"],
    ):
        assert (
            client.post(
                "/auth/refresh", json={"refresh_token": token}
            ).status_code
            == 401
        )
    assert client.post("/auth/login", json=credentials).status_code == 401
    assert (
        client.post(
            "/auth/login",
            json={
                **credentials,
                "password": confirmation["new_password"],
            },
        ).status_code
        == 200
    )


def test_password_reset_replaces_previous_secret(
    client, account, mailer
) -> None:
    for _ in range(2):
        response = client.post(
            "/auth/password-reset/request",
            json={"email": account["email"]},
        )
        assert response.status_code == 202
    first, current = mailer.messages
    assert first["reset_token"] != current["reset_token"]
    for message, expected_status in ((first, 401), (current, 200)):
        response = client.post(
            "/auth/password-reset/confirm",
            json={
                "reset_token": message["reset_token"],
                "new_password": "updated-password",
            },
        )
        assert response.status_code == expected_status


def test_password_reset_expiry(client, account, mailer, db_session) -> None:
    requested = client.post(
        "/auth/password-reset/request", json={"email": account["email"]}
    )
    assert requested.status_code == 202
    stored = db_session.get(PasswordResetToken, account["user_id"])
    stored.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(
        minutes=1
    )
    db_session.commit()

    response = client.post(
        "/auth/password-reset/confirm",
        json={
            "reset_token": mailer.messages[0]["reset_token"],
            "new_password": "updated-password",
        },
    )
    assert response.status_code == 401

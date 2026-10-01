from datetime import UTC, datetime, timedelta

from authlib.jose import jwt

from src.config.settings import settings
from src.models.account import PasswordResetToken


def test_registration_and_login(
    client, credentials, monkeypatch
) -> None:
    registered = client.post("/auth/register", json=credentials)
    assert registered.status_code == 201
    tokens = registered.json()
    assert tokens["token_type"] == "Bearer"
    for token_type in ("access", "refresh"):
        claims = jwt.decode(
            tokens[f"{token_type}_token"], settings.jwt_secret
        )
        claims.validate()
        assert claims["type"] == token_type
        assert claims["iss"] == settings.jwt_issuer
        assert claims["aud"] == settings.jwt_audience
        assert not claims.get("scopes")
    account_id = claims["sub"]

    assert (
        client.post("/auth/register", json=credentials).status_code
        == 409
    )
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
    claims = jwt.decode(
        login.json()["access_token"], settings.jwt_secret
    )
    claims.validate()
    assert claims["scopes"] == ["admin"]


def test_admin_scope_uses_current_configured_user_ids(
    client, credentials, monkeypatch
) -> None:
    registered = client.post("/auth/register", json=credentials)
    assert registered.status_code == 201
    claims = jwt.decode(
        registered.json()["access_token"], settings.jwt_secret
    )
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


def test_refresh_rotation_and_logout(
    client, account, credentials
) -> None:
    other_session = client.post("/auth/login", json=credentials)
    assert other_session.status_code == 200
    original = {"refresh_token": account["refresh_token"]}
    rotated = client.post("/auth/refresh", json=original)
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != original["refresh_token"]
    assert (
        client.post("/auth/refresh", json=original).status_code == 401
    )

    current = {"refresh_token": rotated.json()["refresh_token"]}
    assert client.post("/auth/logout", json=current).status_code == 204
    assert client.post("/auth/refresh", json=current).status_code == 401
    assert (
        client.post(
            "/auth/refresh",
            json={
                "refresh_token": other_session.json()["refresh_token"]
            },
        ).status_code
        == 200
    )


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
    confirmed = client.post(
        "/auth/password-reset/confirm", json=confirmation
    )
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
    assert (
        client.post("/auth/login", json=credentials).status_code == 401
    )
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


def test_password_reset_expiry(
    client, account, mailer, db_session
) -> None:
    requested = client.post(
        "/auth/password-reset/request", json={"email": account["email"]}
    )
    assert requested.status_code == 202
    stored = db_session.get(PasswordResetToken, account["user_id"])
    stored.expires_at = datetime.now(UTC).replace(
        tzinfo=None
    ) - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        "/auth/password-reset/confirm",
        json={
            "reset_token": mailer.messages[0]["reset_token"],
            "new_password": "updated-password",
        },
    )
    assert response.status_code == 401

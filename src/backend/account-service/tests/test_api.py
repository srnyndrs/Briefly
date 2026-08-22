import uuid

from authlib.jose import jwt
from sqlalchemy import text

from src.config.settings import settings


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "account-service"


def test_register_login_and_get_user(client, db_session) -> None:
    register = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "strong-password",
        },
    )
    assert register.status_code == 201
    assert "access_token" in register.json()
    assert "refresh_token" in register.json()

    login = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "strong-password",
        },
    )
    assert login.status_code == 200
    access_token = login.json()["access_token"]
    claims = jwt.decode(access_token, settings.jwt_secret)
    claims.validate()
    assert "admin" in list(claims.get("scopes", []))

    user_id = db_session.execute(
        text(
            "SELECT user_id FROM accounts WHERE email='alice@example.com'"
        )
    ).scalar()

    user = client.get(f"/users/{user_id}")
    assert user.status_code == 200
    assert user.json()["email"] == "alice@example.com"


def test_preferences_and_subscription_flow(
    client, db_session
) -> None:
    reg = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "strong-password",
        },
    )
    assert reg.status_code == 201

    user_id = db_session.execute(
        text(
            "SELECT user_id FROM accounts WHERE email='bob@example.com'"
        )
    ).scalar()

    source_id = str(uuid.uuid4())
    put_prefs = client.put(
        f"/users/{user_id}/preferences",
        json={
            "muted_keywords": ["crypto", "gossip"],
            "muted_categories": ["sports"],
            "blocked_source_ids": [source_id],
            "languages": ["en", "hu"],
            "category_interests": ["tech", "science"],
        },
    )
    assert put_prefs.status_code == 200
    assert put_prefs.json()["category_interests"] == [
        "tech",
        "science",
    ]
    assert put_prefs.json()["muted_keywords"] == ["crypto", "gossip"]
    assert put_prefs.json()["muted_categories"] == ["sports"]
    assert put_prefs.json()["languages"] == ["en", "hu"]
    assert put_prefs.json()["blocked_source_ids"] == [source_id]

    create_sub = client.post(
        f"/users/{user_id}/subscriptions",
        json={"source_id": source_id},
    )
    assert create_sub.status_code == 201

    list_subs = client.get(f"/users/{user_id}/subscriptions")
    assert list_subs.status_code == 200
    assert len(list_subs.json()) == 1
    assert list_subs.json()[0]["source_id"] == source_id

    patch_profile = client.patch(
        f"/users/{user_id}/profile",
        json={"display_name": "Bob"},
    )
    assert patch_profile.status_code == 200
    assert patch_profile.json()["display_name"] == "Bob"

    patch_prefs = client.patch(
        f"/users/{user_id}/preferences",
        json={"languages": ["en", "de"]},
    )
    assert patch_prefs.status_code == 200
    assert patch_prefs.json()["category_interests"] == [
        "tech",
        "science",
    ]
    assert patch_prefs.json()["languages"] == ["en", "de"]
    assert patch_prefs.json()["muted_keywords"] == ["crypto", "gossip"]

    delete_sub = client.delete(
        f"/users/{user_id}/subscriptions/{source_id}"
    )
    assert delete_sub.status_code == 204


def test_password_reset_flow(client) -> None:
    register = client.post(
        "/auth/register",
        json={
            "email": "reset@example.com",
            "password": "old-password",
        },
    )
    assert register.status_code == 201

    request_reset = client.post(
        "/auth/password-reset/request",
        json={"email": "reset@example.com"},
    )
    assert request_reset.status_code == 200
    token = request_reset.json().get("reset_token")
    assert token

    confirm_reset = client.post(
        "/auth/password-reset/confirm",
        json={"reset_token": token, "new_password": "new-password"},
    )
    assert confirm_reset.status_code == 200
    assert confirm_reset.json()["status"] == "ok"

    old_login = client.post(
        "/auth/login",
        json={
            "email": "reset@example.com",
            "password": "old-password",
        },
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/auth/login",
        json={
            "email": "reset@example.com",
            "password": "new-password",
        },
    )
    assert new_login.status_code == 200

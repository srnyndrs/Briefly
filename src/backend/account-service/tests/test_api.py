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

    persisted = db_session.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM accounts),
                (SELECT COUNT(*) FROM user_profiles),
                (SELECT COUNT(*) FROM user_preferences),
                (SELECT COUNT(*) FROM refresh_tokens)
            """
        )
    ).one()
    assert persisted == (1, 1, 1, 1)

    failed_register = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "strong-password",
        },
    )
    assert failed_register.status_code == 409
    assert "access_token" not in failed_register.json()
    assert "refresh_token" not in failed_register.json()
    assert (
        db_session.execute(
            text("SELECT COUNT(*) FROM refresh_tokens")
        ).scalar_one()
        == 1
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "strong-password",
        },
    )
    assert login.status_code == 200
    access_token = login.json()["access_token"]
    refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": register.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()
    assert "refresh_token" in refresh.json()

    logout = client.post(
        "/auth/logout",
        json={"refresh_token": refresh.json()["refresh_token"]},
    )
    assert logout.status_code == 204

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
    client, db_session, publisher
) -> None:
    reg = client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "strong-password",
        },
    )
    assert reg.status_code == 201
    assert publisher.events == []

    user_id = db_session.execute(
        text(
            "SELECT user_id FROM accounts WHERE email='bob@example.com'"
        )
    ).scalar()

    source_id = str(uuid.uuid4())
    original_updated_at = db_session.execute(
        text("SELECT updated_at FROM accounts WHERE user_id=:user_id"),
        {"user_id": user_id},
    ).scalar_one()
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
    assert put_prefs.json()["muted_keywords"] == [
        "crypto",
        "gossip",
    ]
    assert put_prefs.json()["muted_categories"] == ["sports"]
    assert put_prefs.json()["languages"] == ["en", "hu"]
    assert put_prefs.json()["blocked_source_ids"] == [source_id]
    preferences_updated_at = db_session.execute(
        text("SELECT updated_at FROM accounts WHERE user_id=:user_id"),
        {"user_id": user_id},
    ).scalar_one()
    assert preferences_updated_at > original_updated_at

    create_sub = client.post(
        f"/users/{user_id}/subscriptions",
        json={"source_id": source_id},
    )
    assert create_sub.status_code == 201

    list_subs = client.get(f"/users/{user_id}/subscriptions")
    assert list_subs.status_code == 200
    assert len(list_subs.json()) == 1
    assert list_subs.json()[0]["source_id"] == source_id

    put_profile = client.put(
        f"/users/{user_id}/profile",
        json={
            "display_name": "Bob",
            "bio": "About Bob",
            "avatar_url": "https://example.com/bob.png",
        },
    )
    assert put_profile.status_code == 200

    patch_profile = client.patch(
        f"/users/{user_id}/profile",
        json={"display_name": "Alice"},
    )
    assert patch_profile.status_code == 200
    profile_data = patch_profile.json()
    assert profile_data["user_id"] == user_id
    assert profile_data["display_name"] == "Alice"
    assert profile_data["bio"] == "About Bob"
    assert profile_data["avatar_url"] == "https://example.com/bob.png"

    clear_bio = client.patch(
        f"/users/{user_id}/profile", json={"bio": None}
    )
    assert clear_bio.status_code == 200
    assert clear_bio.json()["display_name"] == "Alice"
    assert clear_bio.json()["bio"] is None
    assert (
        clear_bio.json()["avatar_url"] == "https://example.com/bob.png"
    )
    assert [event["event_type"] for event in publisher.events] == [
        "preferences.updated.v1",
    ]
    profile_updated_at = db_session.execute(
        text("SELECT updated_at FROM accounts WHERE user_id=:user_id"),
        {"user_id": user_id},
    ).scalar_one()
    assert profile_updated_at > preferences_updated_at

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
    assert patch_prefs.json()["muted_keywords"] == [
        "crypto",
        "gossip",
    ]

    delete_sub = client.delete(
        f"/users/{user_id}/subscriptions/{source_id}"
    )
    assert delete_sub.status_code == 204
    assert [event["event_type"] for event in publisher.events] == [
        "preferences.updated.v1",
        "preferences.updated.v1",
    ]


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

import uuid
from datetime import UTC, datetime, timedelta

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
                (SELECT COUNT(*) FROM user_preferences),
                (SELECT COUNT(*) FROM refresh_tokens)
            """
        )
    ).one()
    assert persisted == (1, 1, 1)

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
    assert "tv" not in claims

    user_id = db_session.execute(
        text(
            "SELECT user_id FROM accounts WHERE email='alice@example.com'"
        )
    ).scalar()

    user = client.get(f"/users/{user_id}")
    assert user.status_code == 200
    assert user.json()["email"] == "alice@example.com"
    assert "status" not in user.json()


def test_display_name_account_contract(client, db_session) -> None:
    register = client.post(
        "/auth/register",
        json={
            "email": "display-name@example.com",
            "password": "strong-password",
        },
    )
    assert register.status_code == 201
    user_id = db_session.execute(
        text(
            "SELECT user_id FROM accounts "
            "WHERE email='display-name@example.com'"
        )
    ).scalar_one()

    account = client.get(f"/users/{user_id}")
    assert account.status_code == 200
    assert account.json()["display_name"] is None

    updated = client.patch(
        f"/users/{user_id}", json={"display_name": "  Alice  "}
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Alice"

    unchanged = client.patch(f"/users/{user_id}", json={})
    assert unchanged.status_code == 200
    assert unchanged.json()["display_name"] == "Alice"

    cleared = client.patch(
        f"/users/{user_id}", json={"display_name": None}
    )
    assert cleared.status_code == 200
    assert cleared.json()["display_name"] is None

    assert (
        client.patch(
            f"/users/{user_id}", json={"display_name": "   "}
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/users/{user_id}", json={"display_name": "x" * 81}
        ).status_code
        == 422
    )

    assert client.get(f"/users/{user_id}/profile").status_code == 404
    assert client.put(f"/users/{user_id}/profile").status_code == 404
    assert client.patch(f"/users/{user_id}/profile").status_code == 404


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

    assert [event["event_type"] for event in publisher.events] == [
        "preferences.updated.v1",
    ]

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
    second_session = client.post(
        "/auth/login",
        json={
            "email": "reset@example.com",
            "password": "old-password",
        },
    )
    assert second_session.status_code == 200

    request_reset = client.post(
        "/auth/password-reset/request",
        json={"email": "reset@example.com"},
    )
    assert request_reset.status_code == 202
    assert request_reset.json() == {"status": "accepted"}
    unknown_reset = client.post(
        "/auth/password-reset/request",
        json={"email": "unknown@example.com"},
    )
    assert unknown_reset.status_code == 202
    assert unknown_reset.json() == request_reset.json()
    token = client.app.state.password_reset_mailer.messages[0][
        "reset_token"
    ]

    confirm_reset = client.post(
        "/auth/password-reset/confirm",
        json={"reset_token": token, "new_password": "new-password"},
    )
    assert confirm_reset.status_code == 200
    assert confirm_reset.json()["status"] == "ok"

    for refresh_token in (
        register.json()["refresh_token"],
        second_session.json()["refresh_token"],
    ):
        revoked_refresh = client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert revoked_refresh.status_code == 401

    reused_reset = client.post(
        "/auth/password-reset/confirm",
        json={"reset_token": token, "new_password": "third-password"},
    )
    assert reused_reset.status_code == 401

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


def test_password_reset_replaces_the_previous_request(client) -> None:
    register = client.post(
        "/auth/register",
        json={
            "email": "replacement@example.com",
            "password": "old-password",
        },
    )
    assert register.status_code == 201

    for _ in range(2):
        response = client.post(
            "/auth/password-reset/request",
            json={"email": "replacement@example.com"},
        )
        assert response.status_code == 202

    messages = client.app.state.password_reset_mailer.messages
    first_token = messages[0]["reset_token"]
    second_token = messages[1]["reset_token"]
    assert first_token != second_token

    first_confirmation = client.post(
        "/auth/password-reset/confirm",
        json={
            "reset_token": first_token,
            "new_password": "new-password",
        },
    )
    assert first_confirmation.status_code == 401

    second_confirmation = client.post(
        "/auth/password-reset/confirm",
        json={
            "reset_token": second_token,
            "new_password": "new-password",
        },
    )
    assert second_confirmation.status_code == 200


def test_password_reset_rejects_an_expired_token(
    client, db_session
) -> None:
    register = client.post(
        "/auth/register",
        json={
            "email": "expired@example.com",
            "password": "old-password",
        },
    )
    assert register.status_code == 201
    request = client.post(
        "/auth/password-reset/request",
        json={"email": "expired@example.com"},
    )
    assert request.status_code == 202
    token = client.app.state.password_reset_mailer.messages[0][
        "reset_token"
    ]
    db_session.execute(
        text(
            "UPDATE password_reset_tokens SET expires_at=:expires_at "
            "WHERE user_id=(SELECT user_id FROM accounts WHERE email=:email)"
        ),
        {
            "expires_at": datetime.now(UTC).replace(tzinfo=None)
            - timedelta(minutes=1),
            "email": "expired@example.com",
        },
    )
    db_session.commit()

    confirm = client.post(
        "/auth/password-reset/confirm",
        json={"reset_token": token, "new_password": "new-password"},
    )
    assert confirm.status_code == 401


def test_logout_revokes_only_the_submitted_refresh_token(
    client,
) -> None:
    register = client.post(
        "/auth/register",
        json={
            "email": "sessions@example.com",
            "password": "strong-password",
        },
    )
    assert register.status_code == 201
    second_session = client.post(
        "/auth/login",
        json={
            "email": "sessions@example.com",
            "password": "strong-password",
        },
    )
    assert second_session.status_code == 200

    logout = client.post(
        "/auth/logout",
        json={"refresh_token": register.json()["refresh_token"]},
    )
    assert logout.status_code == 204

    logged_out_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": register.json()["refresh_token"]},
    )
    assert logged_out_refresh.status_code == 401
    remaining_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": second_session.json()["refresh_token"]},
    )
    assert remaining_refresh.status_code == 200


def test_password_reset_token_replacement_and_deletion(
    db_session,
) -> None:
    from datetime import datetime, timedelta

    from src.repositories.account_repository import AccountRepository

    now = datetime(2026, 1, 1, 12, 0, 0)
    repository = AccountRepository(db_session)
    user = repository.create_user(
        user_id="user-1",
        email="token@example.com",
        password_hash="hash",
        now=now,
    )
    db_session.flush()

    first = repository.replace_password_reset_token(
        user_id=user.user_id,
        token_hash="a" * 64,
        expires_at=now + timedelta(minutes=15),
        created_at=now,
    )
    second = repository.replace_password_reset_token(
        user_id=user.user_id,
        token_hash="b" * 64,
        expires_at=now + timedelta(minutes=30),
        created_at=now + timedelta(minutes=1),
    )

    assert first.user_id == second.user_id == user.user_id
    assert repository.get_password_reset_token("a" * 64) is None
    stored = repository.get_password_reset_token("b" * 64)
    assert stored is not None
    assert stored.expires_at == now + timedelta(minutes=30)
    assert repository.delete_password_reset_token(user.user_id) is True
    assert repository.get_password_reset_token("b" * 64) is None
    assert repository.delete_password_reset_token(user.user_id) is False


def test_revoke_active_refresh_tokens_leaves_revoked_tokens_unchanged(
    db_session,
) -> None:
    from datetime import datetime, timedelta

    from src.models.account import RefreshToken
    from src.repositories.account_repository import AccountRepository

    now = datetime(2026, 1, 1, 12, 0, 0)
    repository = AccountRepository(db_session)
    user = repository.create_user(
        user_id="user-2",
        email="repository-sessions@example.com",
        password_hash="hash",
        now=now,
    )
    db_session.flush()
    db_session.add_all(
        [
            RefreshToken(
                token_id="active",
                user_id=user.user_id,
                token_hash="active-hash",
                expires_at=now,
            ),
            RefreshToken(
                token_id="revoked",
                user_id=user.user_id,
                token_hash="revoked-hash",
                expires_at=now,
                revoked_at=now - timedelta(minutes=1),
            ),
        ]
    )
    db_session.commit()

    revoked_count = repository.revoke_active_refresh_tokens(
        user.user_id, now
    )

    assert revoked_count == 1
    assert repository.get_refresh_token("active").revoked_at == now
    assert repository.get_refresh_token(
        "revoked"
    ).revoked_at == now - timedelta(minutes=1)

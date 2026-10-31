from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from src.adapters import service_clients
from src.app import app
from src.config.database import get_db
from src.config.settings import settings
from src.models.read_models import (
    PostProjection,
    UserPreferencesProjection,
)
from src.schemas.api import AuthContext
from src.services.auth import get_current_user


@pytest.fixture
def client(session_factory):
    overrides = app.dependency_overrides.copy()
    state = app.state._state.copy()
    fixed_user = AuthContext(user_id=uuid4(), token_type="access", scopes=["admin"])

    def override_get_db():
        with session_factory() as session:
            yield session

    app.state.testing = True
    app.state.projector = None
    app.state.projector_thread = None
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: fixed_user
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)
        app.state._state.clear()
        app.state._state.update(state)


@pytest.fixture
def feed_client(client, db, monkeypatch):
    def list_projected_sources(*, verified_only=False):
        return [
            {"source_id": source_id}
            for (source_id,) in db.query(PostProjection.source_id).distinct()
        ]

    monkeypatch.setattr(
        "src.services.feed_service.crawler_list_sources", list_projected_sources
    )
    return client


@pytest.fixture
def source_payload():
    return {
        "source_id": str(uuid4()),
        "url": "https://example.com/feed.xml",
        "title": "Source",
        "description": "Description",
        "favicon": None,
        "site_url": "https://example.com",
        "verified": False,
        "last_crawled_at": None,
        "next_crawl_scheduled_at": "2026-01-01T00:00:00+00:00",
        "last_crawl_succeeded": True,
        "consecutive_failures": 0,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


def _post(title, source_id, **metadata):
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return PostProjection(
        **{
            "post_id": UUID(str(metadata.pop("post_id", uuid4()))),
            "source_id": UUID(str(source_id)),
            "source_title": "Test Source",
            "title": title,
            "canonical_url": f"https://example.com/{uuid4()}",
            "language": "en",
            "categories": [],
            "keywords": [],
            "published_at": now,
            "updated_at": now,
            **metadata,
        }
    )


def test_health(client, monkeypatch) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "public-api"
    thread = MagicMock()
    projector = MagicMock(is_consuming=True)
    monkeypatch.setattr(app.state, "projector_thread", thread)
    monkeypatch.setattr(app.state, "projector", projector)
    monkeypatch.setattr(settings, "query_consumer_enabled", True)
    monkeypatch.setattr("src.app.database_ready", lambda: True)
    assert client.get("/live").status_code == 200
    assert client.get("/ready").status_code == 200
    projector.is_consuming = False
    assert client.get("/ready").status_code == 503
    assert client.get("/live").status_code == 200
    projector.is_consuming = True
    monkeypatch.setattr("src.app.database_ready", lambda: False)
    assert client.get("/ready").status_code == 503
    assert client.get("/live").status_code == 200
    monkeypatch.setattr("src.app.database_ready", lambda: True)
    assert client.get("/ready").status_code == 200
    thread.is_alive.return_value = False
    assert client.get("/live").status_code == 503
    assert client.get("/ready").status_code == 503
    monkeypatch.setattr(settings, "query_consumer_enabled", False)
    monkeypatch.setattr(app.state, "projector", None)
    monkeypatch.setattr(app.state, "projector_thread", None)
    assert client.get("/live").status_code == 200
    assert client.get("/ready").status_code == 200


def test_personal_feed_applies_subscriptions_languages_and_category(
    monkeypatch, client, db
):
    user = app.dependency_overrides[get_current_user]()
    subscribed, blocked, unsubscribed = (str(uuid4()) for _ in range(3))
    db.add(
        UserPreferencesProjection(
            user_id=user.user_id,
            muted_keywords=[],
            muted_categories=["sports"],
            blocked_source_ids=[blocked],
            languages=["en"],
        )
    )
    db.add_all(
        [
            _post("Technology Story", subscribed, categories=["technology"]),
            _post("Business Story", subscribed, categories=["business"]),
            _post("Muted Sports Story", subscribed, categories=["sports"]),
            _post(
                "Hungarian Story",
                subscribed,
                language="hu",
                categories=["technology"],
            ),
            _post("Blocked Story", blocked, categories=["technology"]),
            _post("Unsubscribed Story", unsubscribed, categories=["technology"]),
        ]
    )
    db.commit()
    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": subscribed}, {"source_id": blocked}],
    )
    selected = client.get(
        "/feed",
        params={"category": "technology", "include_filter_options": True},
    )
    assert selected.status_code == 200
    payload = selected.json()
    assert payload["total"] == 1
    assert [item["title"] for item in payload["items"]] == ["Technology Story"]
    assert {item["title"] for item in payload["headlines"]} == {
        "Technology Story",
        "Business Story",
    }
    assert "sources" not in payload["filter_options"]
    empty = client.get("/feed", params={"category": "science"})
    assert empty.status_code == 200
    assert empty.json()["total"] == 0
    assert empty.json()["items"] == []
    assert empty.json()["headlines"] == payload["headlines"]


def test_explore_uses_explicit_filters_and_visibility_exclusions(
    feed_client, db
) -> None:
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)
    blocked_source_id = str(uuid4())

    db.add(
        UserPreferencesProjection(
            user_id=user.user_id,
            muted_keywords=[],
            muted_categories=["sports"],
            blocked_source_ids=[blocked_source_id],
            languages=["hu"],
            updated_at=now,
        )
    )
    db.add_all(
        [
            _post(
                "Older English Story",
                str(uuid4()),
                source_title="Older Source",
                categories=["technology"],
                published_at=now.replace(year=now.year - 1),
                updated_at=now.replace(year=now.year - 1),
            ),
            _post(
                "Newer English Story",
                str(uuid4()),
                source_title="Newer Source",
                categories=["technology"],
            ),
            _post(
                "Blocked Story",
                blocked_source_id,
                source_title="Blocked Source",
                categories=["technology"],
            ),
            _post(
                "Muted Story",
                str(uuid4()),
                source_title="Muted Source",
                categories=["sports"],
            ),
            _post(
                "Hungarian Story",
                str(uuid4()),
                source_title="Hungarian Source",
                language="hu",
                categories=["technology"],
            ),
        ]
    )
    db.commit()

    response = feed_client.get(
        "/explore",
        params=[
            ("categories", "technology"),
            ("languages", "en"),
            ("sort", "oldest"),
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert [item["title"] for item in payload["items"]] == [
        "Older English Story",
        "Newer English Story",
    ]

    for apply_preferences in (True, False):
        response = feed_client.get(
            "/explore",
            params={
                "source_ids": blocked_source_id,
                "apply_user_preferences": apply_preferences,
                "include_filter_options": True,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == (0 if apply_preferences else 1)
        assert [item["title"] for item in payload["items"]] == (
            [] if apply_preferences else ["Blocked Story"]
        )

    response = feed_client.get(
        "/explore",
        params={"apply_user_preferences": False, "languages": "en"},
    )
    assert response.status_code == 200
    assert {item["title"] for item in response.json()["items"]} == {
        "Older English Story",
        "Newer English Story",
        "Blocked Story",
        "Muted Story",
    }


def test_auth_login_endpoint(monkeypatch, client) -> None:

    def fake_login(body: dict) -> dict:
        assert body["email"] == "user@example.com"
        return {
            "access_token": "access-123",
            "refresh_token": "refresh-123",
            "token_type": "Bearer",
        }

    monkeypatch.setattr("src.routers.auth.account_login", fake_login)

    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "access-123"
    assert payload["refresh_token"] == "refresh-123"


def test_password_reset_forwarding(monkeypatch, client) -> None:

    def fake_password_reset_request(body: dict) -> dict:
        assert body["email"] == "user@example.com"
        return {"status": "accepted"}

    monkeypatch.setattr(
        "src.routers.auth.account_password_reset_request",
        fake_password_reset_request,
    )

    response = client.post(
        "/auth/password-reset/request",
        json={"email": "user@example.com"},
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload == {"status": "accepted"}

    def fake_password_reset_confirm(body: dict) -> dict:
        assert body["reset_token"] == "reset-token-123"
        assert body["new_password"] == "new-password"
        return {"status": "ok"}

    monkeypatch.setattr(
        "src.routers.auth.account_password_reset_confirm",
        fake_password_reset_confirm,
    )

    response = client.post(
        "/auth/password-reset/confirm",
        json={
            "reset_token": "reset-token-123",
            "new_password": "new-password",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_patch_preferences_endpoint(monkeypatch, client) -> None:
    user = app.dependency_overrides[get_current_user]()

    def fake_patch_preferences(
        user_id: str, body: dict, correlation_id: str | None
    ) -> dict:
        assert user_id == str(user.user_id)
        assert body == {"languages": ["en", "hu"], "muted_categories": None}
        assert correlation_id == "preferences-request"
        return {
            "user_id": user_id,
            "muted_keywords": ["crypto"],
            "muted_categories": ["sports"],
            "blocked_source_ids": [],
            "languages": ["en", "hu"],
            "updated_at": datetime.now(UTC).isoformat(),
        }

    monkeypatch.setattr(
        "src.routers.user.account_patch_preferences",
        fake_patch_preferences,
    )

    response = client.patch(
        "/me/preferences",
        json={"languages": ["en", "hu"], "muted_categories": None},
        headers={"x-correlation-id": "preferences-request"},
    )
    assert response.status_code == 200
    assert response.json()["languages"] == ["en", "hu"]
    assert response.json()["muted_keywords"] == ["crypto"]


def test_discover_sources_endpoint(monkeypatch, client) -> None:

    def fake_discover_sources(body: dict) -> list[dict]:
        assert body["url"] == "24.hu"
        return [
            {
                "url": "https://example.com/feed.xml",
                "title": "Discovered",
                "content_type": "application/rss+xml",
                "favicon": "https://example.com/favicon.ico",
                "description": "Feed description",
                "site_url": "https://example.com",
                "site_name": "Example News",
                "language": "hu-HU",
            }
        ]

    monkeypatch.setattr(
        "src.routers.sources.crawler_discover_sources",
        fake_discover_sources,
    )

    response = client.post("/sources/discover", json={"url": "24.hu"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Discovered"
    assert payload[0]["site_url"] == "https://example.com"
    assert payload[0]["site_name"] == "Example News"
    assert payload[0]["language"] == "hu-HU"


def test_create_source_endpoint_forwards_json_payload(
    monkeypatch, client, source_payload
) -> None:
    captured: dict = {}
    ordinary_user = AuthContext(user_id=uuid4(), token_type="access", scopes=[])
    app.dependency_overrides[get_current_user] = lambda: ordinary_user

    def fake_create_source(body: dict) -> dict:
        captured.update(body)
        return {
            **source_payload,
            "source_id": str(uuid4()),
            "title": body["title"],
            "description": body["description"],
            "favicon": body["favicon"],
            "verified": False,
        }

    monkeypatch.setattr(
        "src.routers.sources.crawler_create_source",
        fake_create_source,
    )

    response = client.post(
        "/sources",
        json={
            "url": "https://example.com",
            "title": "  Example  ",
            "description": "Feed description",
            "favicon": "https://example.com/favicon.ico",
            "site_url": "https://example.com",
            "site_name": "Example News",
            "language": "hu-HU",
        },
    )

    assert response.status_code == 201
    current_user = app.dependency_overrides[get_current_user]()
    assert captured == {
        "url": "https://example.com",
        "title": "Example",
        "description": "Feed description",
        "favicon": "https://example.com/favicon.ico",
        "site_url": "https://example.com/",
        "site_name": "Example News",
        "language": "hu-HU",
        "submitted_by_user_id": str(current_user.user_id),
    }


@pytest.mark.parametrize(
    "operation,method,owner,path,args",
    [
        (
            "crawler_create_source",
            "POST",
            "crawler",
            "/sources",
            ({"title": "Example"},),
        ),
        (
            "crawler_patch_source",
            "PATCH",
            "crawler",
            "/sources/id",
            ("id", {"title": "Changed"}),
        ),
        ("crawler_delete_source", "DELETE", "crawler", "/sources/id", ("id",)),
        (
            "content_patch_post",
            "PATCH",
            "content",
            "/posts/id",
            ("id", {"title": "Changed"}),
        ),
        ("content_delete_post", "DELETE", "content", "/posts/id", ("id",)),
    ],
)
def test_owner_write_forwards_internal_credential(
    monkeypatch, operation, method, owner, path, args
) -> None:
    request = MagicMock(return_value=httpx.Response(200, json={"ok": True}))
    monkeypatch.setattr(httpx.Client, "request", request)
    monkeypatch.setattr(settings, "internal_admin_token", "test-internal-token")
    owner_url = getattr(settings, f"{owner}_service_url")

    getattr(service_clients, operation)(*args)

    forwarded = request.call_args.kwargs
    assert forwarded["method"] == method
    assert forwarded["url"] == f"{owner_url}{path}"
    assert forwarded["headers"] == {"x-admin-token": "test-internal-token"}
    assert forwarded["json"] == (args[-1] if isinstance(args[-1], dict) else None)

    request.reset_mock()
    monkeypatch.setattr(settings, "internal_admin_token", None)
    with pytest.raises(service_clients.ServiceClientError) as error:
        getattr(service_clients, operation)(*args)
    assert error.value.status_code == 503
    assert error.value.detail == "INTERNAL_ADMIN_TOKEN is not configured"
    request.assert_not_called()


def test_owner_reads_do_not_require_or_forward_internal_credential(
    monkeypatch,
) -> None:
    request = MagicMock(return_value=httpx.Response(200, json={"post_id": "id"}))
    monkeypatch.setattr(httpx.Client, "request", request)
    monkeypatch.setattr(settings, "internal_admin_token", None)

    assert service_clients.content_get_post("id") == {"post_id": "id"}
    assert request.call_args.kwargs["headers"] == {}


def test_create_source_rejects_client_policy_fields(client, monkeypatch) -> None:
    from unittest.mock import MagicMock

    create = MagicMock()
    monkeypatch.setattr("src.routers.sources.crawler_create_source", create)
    response = client.post(
        "/sources",
        json={
            "url": "https://example.com/feed.xml",
            "title": "Valid title",
            "verified": True,
            "submitted_by_user_id": str(uuid4()),
        },
    )
    assert response.status_code == 422

    create.assert_not_called()


def test_patch_source_endpoint(monkeypatch, client, source_payload) -> None:
    source_id = str(uuid4())
    captured: dict = {}

    def fake_patch_source(sid: str, body: dict) -> dict:
        assert sid == source_id
        captured.update(body)
        return {
            **source_payload,
            "source_id": sid,
            "title": body.get("title", "Existing title"),
            "description": body.get("description", "Feed description"),
            "favicon": body.get("favicon", "https://example.com/icon.png"),
            "verified": body.get("verified", False),
        }

    monkeypatch.setattr(
        "src.routers.sources.crawler_patch_source", fake_patch_source
    )
    response = client.patch(
        f"/sources/{source_id}",
        json={
            "title": "  Updated  ",
            "favicon": "https://example.com/icon.png",
            "site_url": "https://example.com/",
            "site_name": "Example News",
            "language": "hu-HU",
        },
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert captured == {
        "title": "Updated",
        "favicon": "https://example.com/icon.png",
        "site_url": "https://example.com/",
        "site_name": "Example News",
        "language": "hu-HU",
    }

    captured.clear()
    response = client.patch(f"/sources/{source_id}", json={"verified": True})
    assert response.status_code == 200
    assert captured == {"verified": True}


def test_source_metadata_validation(client):
    assert (
        client.patch(f"/sources/{uuid4()}", json={"title": " "}).status_code == 422
    )


def test_admin_get_post_endpoint(monkeypatch, client) -> None:
    post_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    def fake_get(target_id: str) -> dict:
        assert target_id == post_id
        return {
            "post_id": target_id,
            "post_revision": 1,
            "source_id": str(uuid4()),
            "source_title": "Admin Source",
            "item_guid": "guid-1",
            "url": "https://example.com/article",
            "title": "Admin Post",
            "description": "desc",
            "content": "body",
            "author": "Author",
            "published_at": now,
            "crawled_at": now,
            "parsed_at": now,
            "image_url": None,
            "language": "en",
            "keywords": ["technology"],
        }

    monkeypatch.setattr("src.routers.posts.content_get_post", fake_get)

    response = client.get(f"/admin/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["post_id"] == post_id


def test_admin_patch_post_forwards_only_supplied_fields(
    monkeypatch, client
) -> None:
    post_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    captured = {}

    def fake_patch(target_id: str, body: dict) -> dict:
        captured.update(body)
        return {
            "post_id": target_id,
            "post_revision": 2,
            "source_id": str(uuid4()),
            "source_title": "Source",
            "item_guid": "guid",
            "url": "https://example.com/post",
            "title": body["title"],
            "parsed_at": now,
            "publication_status": "published",
        }

    monkeypatch.setattr("src.routers.posts.content_patch_post", fake_patch)
    response = client.patch(
        f"/admin/posts/{post_id}",
        json={"title": "  Edited  ", "description": None, "published_at": now},
    )
    assert response.status_code == 200
    assert response.json()["post_revision"] == 2
    assert captured == {
        "title": "Edited",
        "description": None,
        "published_at": now.replace("+00:00", "Z"),
    }
    assert client.patch(f"/admin/posts/{post_id}", json={}).status_code == 422


@pytest.mark.parametrize(
    "path,owner_call",
    [
        ("/admin/posts/{id}", "src.routers.posts.content_delete_post"),
        ("/sources/{id}", "src.routers.sources.crawler_delete_source"),
    ],
)
def test_admin_delete_forwards_to_owner(
    monkeypatch, client, path, owner_call
) -> None:
    item_id = uuid4()
    calls = []
    monkeypatch.setattr(
        owner_call,
        lambda target_id: calls.append(target_id),
    )

    response = client.delete(path.format(id=item_id))

    assert response.status_code == 204
    assert response.content == b""
    assert calls == [str(item_id)]


def test_profile_composition_and_partial_update(monkeypatch, client) -> None:
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC).isoformat()

    def fake_get_user(u_id: str) -> dict:
        assert u_id == str(user.user_id)
        return {
            "user_id": u_id,
            "email": "test@example.com",
            "display_name": "Test User",
            "created_at": now,
        }

    def fake_get_preferences(u_id: str) -> dict:
        assert u_id == str(user.user_id)
        return {
            "user_id": u_id,
            "muted_keywords": ["crypto"],
            "muted_categories": ["sports"],
            "blocked_source_ids": [],
            "languages": ["en"],
            "updated_at": now,
        }

    monkeypatch.setattr("src.routers.user.account_get_user", fake_get_user)
    monkeypatch.setattr(
        "src.routers.user.account_get_preferences",
        fake_get_preferences,
    )

    response = client.get("/me")
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == str(user.user_id)
    assert payload["email"] == "test@example.com"
    assert payload["display_name"] == "Test User"
    assert payload["preferences"]["muted_keywords"] == ["crypto"]

    def fake_patch_user(user_id: str, body: dict) -> dict:
        assert user_id == str(user.user_id)
        assert body == {"display_name": "New Name"}
        return {
            "user_id": user_id,
            "email": "test@example.com",
            "display_name": "New Name",
            "created_at": datetime.now(UTC).isoformat(),
        }

    monkeypatch.setattr("src.routers.user.account_patch_user", fake_patch_user)
    response = client.patch("/me", json={"display_name": "New Name"})
    assert response.status_code == 200
    assert response.json()["display_name"] == "New Name"
    assert response.json()["preferences"]["languages"] == ["en"]


def test_explore_filter_options_are_opt_in_and_cover_all_pages(
    feed_client, db
) -> None:
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    db.add(
        UserPreferencesProjection(
            user_id=user.user_id,
            muted_keywords=[],
            muted_categories=[],
            blocked_source_ids=[],
            languages=["hu"],
            updated_at=now,
        )
    )
    db.add_all(
        [
            _post(
                "Technology English",
                str(uuid4()),
                source_title="Technology Source",
                categories=["technology"],
                author="Example Author",
                keywords=["Climate", "policy"],
            ),
            _post(
                "Business Hungarian",
                str(uuid4()),
                source_title="Business Source",
                language="hu",
                categories=["business"],
            ),
            _post(
                "Business English",
                str(uuid4()),
                source_title="Business Source",
                categories=["business"],
            ),
            _post(
                "Technology Hungarian",
                str(uuid4()),
                source_title="Technology Source",
                language="hu",
                categories=["technology"],
            ),
        ]
    )
    db.commit()

    without_options = feed_client.get(
        "/explore", params={"categories": "technology"}
    )
    assert without_options.status_code == 200
    assert "filter_options" not in without_options.json()

    response = feed_client.get(
        "/explore",
        params=[
            ("page_size", "1"),
            ("languages", "en"),
            ("include_filter_options", "true"),
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 1
    assert payload["filter_options"]["categories"] == [
        "business",
        "technology",
    ]
    assert payload["filter_options"]["languages"] == ["en", "hu"]
    assert payload["filter_options"]["authors"] == ["Example Author"]
    assert payload["filter_options"]["keywords"] == [
        "Climate",
        "policy",
    ]
    assert {option["title"] for option in payload["filter_options"]["sources"]} == {
        "Technology Source",
        "Business Source",
    }
    assert all(
        set(option) == {"id", "title"}
        for option in payload["filter_options"]["sources"]
    )


def test_explore_binds_repeatable_source_ids(feed_client, db) -> None:
    source_ids = [str(uuid4()) for _ in range(3)]
    now = datetime.now(UTC)
    db.add_all(
        [
            _post(
                f"Source {index} story",
                source_id,
                source_title=f"Source {index}",
                categories=["technology"],
                published_at=now,
                updated_at=now,
            )
            for index, source_id in enumerate(source_ids)
        ]
    )
    db.commit()

    response = feed_client.get(
        "/explore",
        params=[
            ("source_ids", source_ids[0]),
            ("source_ids", source_ids[1]),
            ("include_filter_options", "true"),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert {item["source_id"] for item in payload["items"]} == set(source_ids[:2])
    assert payload["filter_options"]["sources"]
    assert all(
        set(option) == {"id", "title"}
        for option in payload["filter_options"]["sources"]
    )


def test_explore_searches_public_fields_and_excludes_body(feed_client, db) -> None:
    source_id = str(uuid4())
    db.add_all(
        [
            _post(
                "Climate change report",
                source_id,
                post_id="00000000-0000-0000-0000-000000000001",
                source_title="Search Source",
                keywords=["Technology trends"],
            ),
            _post(
                "Economy outlook",
                source_id,
                post_id="00000000-0000-0000-0000-000000000002",
                source_title="Search Source",
                description="Climate policy update",
            ),
            _post(
                "Research notes",
                source_id,
                post_id="00000000-0000-0000-0000-000000000003",
                source_title="Search Source",
                content="Climate adaptation matters",
            ),
        ]
    )
    db.commit()

    response = feed_client.get("/explore", params={"query": "  CLIMATE "})
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {item["post_id"] for item in response.json()["items"]} == {
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
    }
    keyword = feed_client.get("/explore", params={"query": "trends"})
    assert keyword.status_code == 200
    assert keyword.json()["total"] == 1
    assert keyword.json()["items"][0]["post_id"].endswith("1")


def test_explore_query_validation_rejects_empty_and_sort_combinations(
    feed_client,
) -> None:

    assert feed_client.get("/explore", params={"query": "   "}).status_code == 422
    assert feed_client.get("/explore", params={"query": "..."}).status_code == 422
    assert (
        feed_client.get(
            "/explore",
            params={"query": "climate", "sort": "oldest"},
        ).status_code
        == 422
    )


def test_list_and_detail_post_contracts(monkeypatch, feed_client, db) -> None:

    post_id = str(uuid4())
    source_id = str(uuid4())
    db.add(
        _post(
            "Single Post",
            source_id,
            post_id=post_id,
            source_title="Single Source",
            categories=["science", "health"],
            description="Detail",
            author="Example Author",
            keywords=["climate", "policy"],
            content="Full body text",
        )
    )
    empty_id = str(uuid4())
    db.add(
        _post(
            "Empty article",
            source_id,
            post_id=empty_id,
            source_title="Single Source",
            categories=[],
        )
    )
    db.commit()

    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": source_id}],
    )

    for path in ("/feed", "/explore", "/admin/feed"):
        response = feed_client.get(path)
        assert response.status_code == 200
        items = {item["post_id"]: item for item in response.json()["items"]}
        assert items[post_id]["has_content"] is True
        assert items[empty_id]["has_content"] is False
        assert items[post_id]["categories"] == ["science", "health"]
        assert items[empty_id]["categories"] == []
        assert all("content" not in item for item in items.values())
    response = feed_client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["post_id"] == post_id
    assert payload["title"] == "Single Post"
    assert payload["content"] == "Full body text"
    assert payload["author"] == "Example Author"
    assert payload["keywords"] == ["climate", "policy"]

    assert payload["categories"] == ["science", "health"]
    empty = feed_client.get(f"/posts/{empty_id}")
    assert empty.status_code == 200
    assert empty.json()["categories"] == []
    assert feed_client.get(f"/posts/{uuid4()}").status_code == 404


def test_source_catalog_composition_and_filters(
    monkeypatch, client, source_payload
) -> None:
    now = datetime.now(UTC).isoformat()
    source_1 = str(uuid4())
    source_2 = str(uuid4())

    def fake_list_sources() -> list[dict]:
        return [
            {
                **source_payload,
                "source_id": source_1,
                "title": "Subscribed Source",
                "description": "Desc",
                "favicon": None,
                "verified": True,
            },
            {
                **source_payload,
                "source_id": source_2,
                "title": "Unsubscribed Source",
                "description": "Desc",
                "favicon": None,
                "verified": False,
            },
        ]

    def fake_list_subscriptions(user_id: str) -> list[dict]:
        assert user_id == str(app.dependency_overrides[get_current_user]().user_id)
        return [
            {
                "user_id": user_id,
                "source_id": source_1,
                "created_at": now,
            }
        ]

    monkeypatch.setattr(
        "src.routers.sources.crawler_list_sources",
        fake_list_sources,
    )
    monkeypatch.setattr(
        "src.routers.sources.account_list_subscriptions",
        fake_list_subscriptions,
    )

    all_res = client.get("/sources")
    assert all_res.status_code == 200
    assert len(all_res.json()) == 2

    sub_res = client.get("/sources", params={"subscribed_only": "true"})
    assert sub_res.status_code == 200
    sub_items = sub_res.json()
    assert len(sub_items) == 1
    assert sub_items[0]["source_id"] == source_1
    assert sub_items[0]["is_subscribed"] is True

    assert [item["is_subscribed"] for item in all_res.json()] == [True, False]
    query = client.get("/sources", params={"query": "UNSUBSCRIBED"})
    assert query.status_code == 200
    assert [item["source_id"] for item in query.json()] == [source_2]
    monkeypatch.setattr(
        "src.routers.sources.crawler_get_source",
        lambda sid: next(
            source for source in fake_list_sources() if source["source_id"] == sid
        ),
    )
    detail = client.get(f"/sources/{source_1}")
    assert detail.status_code == 200
    assert detail.json()["is_subscribed"] is True
    assert detail.json()["consecutive_failures"] == 0
    assert (
        detail.json()["next_crawl_scheduled_at"]
        == source_payload["next_crawl_scheduled_at"]
    )


def test_feed_pagination_pages_and_counts(monkeypatch, client, db) -> None:
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    db.add(
        UserPreferencesProjection(
            user_id=user.user_id,
            muted_keywords=[],
            muted_categories=[],
            blocked_source_ids=[],
            languages=["en"],
            updated_at=now,
        )
    )

    source_ids = [str(uuid4()) for _ in range(5)]
    for i, source_id in enumerate(source_ids):
        db.add(
            _post(
                f"Post {i}",
                source_id,
                post_id=f"00000000-0000-0000-0000-{i + 1:012d}",
                source_title=f"Source {i}",
                published_at=datetime.fromtimestamp(1700000000 + i * 100, tz=UTC),
                updated_at=now,
            )
        )
    db.add(_post("Wrong language", source_ids[0], language="hu"))
    db.commit()
    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": source_id} for source_id in source_ids],
    )

    # Page 1 with page_size=2
    res_p1 = client.get("/feed", params={"page": 1, "page_size": 2})
    assert res_p1.status_code == 200
    p1 = res_p1.json()
    assert [item["title"] for item in p1["headlines"]] == [
        "Post 4",
        "Post 3",
        "Post 2",
    ]
    assert p1["total"] == 5
    assert p1["page"] == 1
    assert p1["page_count"] == 3
    assert p1["page_size"] == 2
    assert len(p1["items"]) == 2
    assert p1["items"][0]["title"] == "Post 4"
    assert p1["items"][1]["title"] == "Post 3"
    assert {item["post_id"] for item in p1["items"]} <= {
        item["post_id"] for item in p1["headlines"]
    }

    # Page 2 with page_size=2
    res_p2 = client.get("/feed", params={"page": 2, "page_size": 2})
    assert res_p2.status_code == 200
    p2 = res_p2.json()
    assert p2["page"] == 2
    assert p2["page_count"] == 3
    assert [item["title"] for item in p2["items"]] == ["Post 2", "Post 1"]
    assert "headlines" not in p2

    res_p3 = client.get("/feed", params={"page": 3, "page_size": 2})
    assert res_p3.status_code == 200
    assert [item["title"] for item in res_p3.json()["items"]] == ["Post 0"]


def test_admin_feed_pagination_and_search_ignore_personal_and_verified_filters(
    client, db, monkeypatch
) -> None:
    now = datetime.now(UTC)
    unverified_source_id = uuid4()
    verified_catalog = MagicMock(return_value=[])
    monkeypatch.setattr(
        "src.services.feed_service.crawler_list_sources", verified_catalog
    )
    user_id = app.dependency_overrides[get_current_user]().user_id
    db.add(
        UserPreferencesProjection(
            user_id=user_id,
            blocked_source_ids=[str(unverified_source_id)],
            muted_keywords=["Admin"],
            languages=["de"],
        )
    )

    for i in range(3):
        db.add(
            _post(
                f"Admin Post {i}",
                str(unverified_source_id if i else uuid4()),
                source_title=f"Admin Source {i}",
                published_at=datetime.fromtimestamp(1700000000 + i * 100, tz=UTC),
                updated_at=now,
            )
        )
    db.commit()

    db.add(
        _post(
            "Deleted Admin Post",
            str(uuid4()),
            is_deleted=True,
            language="zz",
            categories=["deleted"],
        )
    )
    db.commit()

    res = client.get(
        "/admin/feed",
        params={"page": 1, "page_size": 2, "include_filter_options": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_count"] == 2
    assert data["page_size"] == 2
    assert len(data["items"]) == 2

    assert [item["title"] for item in data["items"]] == [
        "Admin Post 2",
        "Admin Post 1",
    ]
    assert "zz" not in data["filter_options"]["languages"]
    assert "deleted" not in data["filter_options"]["categories"]

    filtered = client.get(
        "/admin/feed",
        params={
            "query": "Admin",
            "source_ids": str(unverified_source_id),
            "languages": "en",
            "page_size": 1,
            "include_filter_options": True,
        },
    )
    assert filtered.status_code == 200
    results = filtered.json()
    assert results["total"] == 2
    assert results["page_count"] == 2
    assert [item["title"] for item in results["items"]] == ["Admin Post 2"]
    assert results["filter_options"]["languages"] == ["en"]
    verified_catalog.assert_not_called()


def test_subscription_forwarding(monkeypatch, client):
    user_id = str(app.dependency_overrides[get_current_user]().user_id)
    source_id = str(uuid4())
    subscription = {
        "user_id": user_id,
        "source_id": source_id,
        "created_at": "2026-01-01T00:00:00Z",
    }

    def list_subscriptions(uid):
        assert uid == user_id
        return [subscription]

    def create_subscription(uid, body):
        assert uid == user_id
        assert body == {"source_id": source_id}
        return subscription

    def delete_subscription(uid, sid):
        assert (uid, sid) == (user_id, source_id)

    monkeypatch.setattr(
        "src.routers.user.account_list_subscriptions", list_subscriptions
    )
    monkeypatch.setattr(
        "src.routers.user.account_create_subscription", create_subscription
    )
    monkeypatch.setattr(
        "src.routers.user.account_delete_subscription", delete_subscription
    )
    created = client.post("/me/subscriptions", json={"source_id": source_id})
    assert created.status_code == 201
    assert created.json()["source_id"] == source_id
    listed = client.get("/me/subscriptions")
    assert listed.status_code == 200
    assert listed.json()[0]["user_id"] == user_id
    assert listed.json()[0]["source_id"] == source_id
    deleted = client.delete(f"/me/subscriptions/{source_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""


def test_create_my_subscription_conflict(monkeypatch, client) -> None:
    from src.adapters.service_clients import ServiceClientError

    src_id = str(uuid4())

    def mock_conflict(*args, **kwargs):
        raise ServiceClientError(
            status_code=409, detail="Subscription already exists"
        )

    monkeypatch.setattr(
        "src.routers.user.account_create_subscription",
        mock_conflict,
    )

    res = client.post(
        "/me/subscriptions",
        json={"source_id": src_id},
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Subscription already exists"


def test_feed_and_explore_filter_muted_keywords(monkeypatch, feed_client, db):
    user = app.dependency_overrides[get_current_user]()
    source = str(uuid4())
    db.add(
        UserPreferencesProjection(
            user_id=user.user_id,
            muted_keywords=["paramount"],
            muted_categories=[],
            blocked_source_ids=[],
            languages=[],
        )
    )
    db.add_all(
        [
            _post("Clean Post", source, keywords=["technology"]),
            _post("Studio merger", source, keywords=["Paramount"]),
        ]
    )
    db.commit()
    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": source}],
    )
    for path in ("/feed", "/explore"):
        response = feed_client.get(path)
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert [item["title"] for item in response.json()["items"]] == [
            "Clean Post"
        ]
    response = feed_client.get("/explore", params={"apply_user_preferences": False})
    assert response.status_code == 200
    assert response.json()["total"] == 2


@pytest.mark.parametrize("apply_preferences", ["true", "false"])
def test_explore_explicit_source_filter_cannot_include_unverified(
    monkeypatch, apply_preferences, client, db
):
    verified, unverified = str(uuid4()), str(uuid4())
    db.add_all(
        [
            _post(
                "Visible",
                verified,
                source_title="Verified",
                categories=["science"],
                author="Verified Author",
                keywords=["verified"],
            ),
            _post(
                "Hidden",
                unverified,
                source_title="Unverified",
                language="hu",
                categories=["sports"],
                author="Hidden Author",
                keywords=["hidden"],
            ),
        ]
    )
    db.commit()

    def list_verified_sources(*, verified_only):
        assert verified_only is True
        return [{"source_id": verified}]

    monkeypatch.setattr(
        "src.services.feed_service.crawler_list_sources", list_verified_sources
    )
    response = client.get(
        "/explore",
        params=[
            ("source_ids", verified),
            ("source_ids", unverified),
            ("apply_user_preferences", apply_preferences),
            ("include_filter_options", "true"),
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["source_id"] for item in payload["items"]] == [verified]
    assert payload["filter_options"] == {
        "categories": ["science"],
        "languages": ["en"],
        "authors": ["Verified Author"],
        "keywords": ["verified"],
        "sources": [{"id": verified, "title": "Verified"}],
    }


def test_personal_feed_returns_empty_page_without_subscriptions(
    monkeypatch, client, db
):
    db.add(_post("Unsubscribed", str(uuid4())))
    db.commit()
    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions", lambda _: []
    )
    response = client.get("/feed", params={"include_filter_options": True})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == payload["page_count"] == 0
    assert payload["items"] == payload["headlines"] == []
    assert payload["filter_options"] == {
        "categories": [],
        "languages": [],
        "authors": [],
        "keywords": [],
    }


def test_upstream_request_error_returns_502(monkeypatch, client) -> None:
    import httpx

    orig_request = httpx.Client.request

    def fake_request(self, *args, **kwargs):
        if isinstance(self, TestClient):
            return orig_request(self, *args, **kwargs)
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.Client, "request", fake_request)

    response = client.get("/sources")
    assert response.status_code == 502
    assert response.json()["detail"] == "Upstream service unavailable"


@pytest.fixture
def access_token(client, monkeypatch):
    from authlib.jose import jwt

    from src.config.settings import settings

    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "jwt_secret", "public-api-test-secret")
    monkeypatch.setattr(settings, "jwt_issuer", "test-issuer")
    monkeypatch.setattr(settings, "jwt_audience", "test-audience")
    user_id = str(uuid4())

    def sign(*, expired=False, token_type="access"):
        return jwt.encode(
            {"alg": "HS256"},
            {
                "sub": user_id,
                "iss": settings.jwt_issuer,
                "aud": settings.jwt_audience,
                "type": token_type,
                "exp": 1 if expired else 4102444800,
                "scopes": [],
            },
            settings.jwt_secret,
        ).decode()

    return user_id, sign


def test_access_token_subject_reaches_profile(monkeypatch, client, access_token):
    user_id, sign = access_token

    def get_user(uid):
        assert uid == user_id
        return {
            "user_id": uid,
            "email": "test@example.com",
            "display_name": "Test User",
            "created_at": "2026-01-01T00:00:00Z",
        }

    def get_preferences(uid):
        assert uid == user_id
        return {
            "user_id": uid,
            "muted_keywords": [],
            "muted_categories": [],
            "blocked_source_ids": [],
            "languages": [],
            "updated_at": "2026-01-01T00:00:00Z",
        }

    monkeypatch.setattr("src.routers.user.account_get_user", get_user)
    monkeypatch.setattr("src.routers.user.account_get_preferences", get_preferences)
    response = client.get("/me", headers={"Authorization": f"Bearer {sign()}"})
    assert response.status_code == 200
    assert response.json()["user_id"] == user_id


@pytest.mark.parametrize("kind", ["missing", "expired", "refresh"])
def test_protected_profile_rejects_invalid_access(
    client, access_token, monkeypatch, kind
):
    from unittest.mock import MagicMock

    _, sign = access_token
    upstream = MagicMock(side_effect=AssertionError("Unauthorized upstream call"))
    monkeypatch.setattr("src.routers.user.account_get_user", upstream)
    headers = (
        {}
        if kind == "missing"
        else {
            "Authorization": "Bearer "
            + sign(
                expired=kind == "expired",
                token_type="refresh" if kind == "refresh" else "access",
            )
        }
    )
    assert client.get("/me", headers=headers).status_code == 401
    upstream.assert_not_called()


@pytest.mark.parametrize(
    "method,path,operation",
    [
        ("PATCH", "/sources/{id}", "src.routers.sources.crawler_patch_source"),
        ("DELETE", "/sources/{id}", "src.routers.sources.crawler_delete_source"),
        (
            "GET",
            "/admin/feed",
            "src.services.feed_service.FeedService.get_admin_feed",
        ),
        ("GET", "/admin/posts/{id}", "src.routers.posts.content_get_post"),
        ("DELETE", "/admin/posts/{id}", "src.routers.posts.content_delete_post"),
    ],
)
def test_admin_routes_reject_ordinary_access(
    client, access_token, monkeypatch, method, path, operation
):
    from unittest.mock import MagicMock

    _, sign = access_token
    upstream = MagicMock(side_effect=AssertionError("Unauthorized operation"))
    monkeypatch.setattr(operation, upstream)
    response = client.request(
        method,
        path.format(id=uuid4()),
        headers={"Authorization": f"Bearer {sign()}"},
        **({"json": {"verified": True}} if method == "PATCH" else {}),
    )
    assert response.status_code == 403
    upstream.assert_not_called()


def test_explore_empty_verified_catalog(monkeypatch, client, db):
    db.add(_post("Previously verified", str(uuid4()), categories=["science"]))
    db.commit()
    monkeypatch.setattr(
        "src.services.feed_service.crawler_list_sources",
        lambda *, verified_only: [],
    )
    response = client.get(
        "/explore",
        params={
            "include_filter_options": True,
            "apply_user_preferences": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0
    assert response.json()["filter_options"] == {
        "categories": [],
        "languages": [],
        "authors": [],
        "keywords": [],
        "sources": [],
    }

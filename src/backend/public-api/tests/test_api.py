from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.config.database import get_db
from src.models.read_models import (
    Base,
    PostProjection,
    UserPreferencesProjection,
)
from src.schemas.api import AuthContext
from src.services.auth import get_current_user


@pytest.fixture(autouse=True)
def _use_projected_sources_as_verified_for_existing_explore_tests(
    monkeypatch,
) -> None:
    def list_projected_sources(*, verified_only: bool = False) -> list[dict]:
        db_dependency = app.dependency_overrides[get_db]()
        db = next(db_dependency)
        try:
            source_ids = db.query(PostProjection.source_id).distinct().all()
            return [{"source_id": source_id} for (source_id,) in source_ids]
        finally:
            try:
                next(db_dependency)
            except StopIteration:
                pass

    monkeypatch.setattr(
        "src.services.feed_service.ingestion_list_sources",
        list_projected_sources,
    )


def _build_client() -> TestClient:
    app.state.testing = True

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={"schema_translate_map": {"query": None}},
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)
    fixed_user = AuthContext(
        user_id=uuid4(),
        token_type="access",
        scopes=["admin"],
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_user() -> AuthContext:
        return fixed_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_user
    return TestClient(app)


def test_health() -> None:
    client = _build_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "public-api"


def test_admin_api_surface_is_minimal() -> None:
    _build_client()
    paths = app.openapi()["paths"]

    assert "delete" not in paths["/sources/{source_id}"]
    assert "/admin/posts" not in paths
    assert "/admin/posts/count" not in paths
    assert "get" in paths["/admin/posts/{post_id}"]


def test_overlapping_feeds_can_project_the_same_article_url() -> None:
    _build_client()
    db = next(app.dependency_overrides[get_db]())
    url = "https://example.com/article"
    db.add_all(
        [
            PostProjection(
                post_id=str(uuid4()),
                source_id=source_id,
                source_title=source_id,
                canonical_url=url,
            )
            for source_id in ("overall", "category")
        ]
    )
    db.commit()
    assert db.query(PostProjection).filter_by(canonical_url=url).count() == 2


def test_personal_feed_applies_subscriptions_languages_and_category(
    monkeypatch,
) -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    subscribed_source_id = str(uuid4())
    unsubscribed_source_id = str(uuid4())
    now = datetime.now(UTC)
    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            muted_keywords=[],
            muted_categories=["sports"],
            blocked_source_ids=[],
            languages=["en"],
            updated_at=now,
        )
    )
    db.add_all(
        [
            PostProjection(
                post_id=str(uuid4()),
                source_id=subscribed_source_id,
                source_title="Subscribed Source",
                canonical_url="https://example.com/technology",
                title="Technology Story",
                language="en",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=subscribed_source_id,
                source_title="Subscribed Source",
                canonical_url="https://example.com/sports",
                title="Muted Sports Story",
                language="en",
                categories=["sports"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=subscribed_source_id,
                source_title="Subscribed Source",
                canonical_url="https://example.com/hungarian",
                title="Hungarian Story",
                language="hu",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=unsubscribed_source_id,
                source_title="Unsubscribed Source",
                canonical_url="https://example.com/unsubscribed",
                title="Unsubscribed Story",
                language="en",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()

    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": subscribed_source_id}],
    )

    response = client.get(
        "/feed",
        params={
            "category": "business",
            "include_filter_options": "true",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert [item["title"] for item in payload["headlines"]] == [
        "Technology Story"
    ]
    assert payload["total"] == 0
    assert payload["items"] == []
    assert "sources" not in payload["filter_options"]


def test_explore_uses_explicit_filters_and_visibility_exclusions() -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)
    blocked_source_id = str(uuid4())

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            muted_keywords=[],
            muted_categories=["sports"],
            blocked_source_ids=[blocked_source_id],
            languages=["en"],
            updated_at=now,
        )
    )
    db.add_all(
        [
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Older Source",
                canonical_url="https://example.com/older",
                title="Older English Story",
                language="en",
                categories=["technology"],
                keywords=[],
                published_at=now.replace(year=now.year - 1),
                updated_at=now.replace(year=now.year - 1),
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Newer Source",
                canonical_url="https://example.com/newer",
                title="Newer English Story",
                language="en",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=blocked_source_id,
                source_title="Blocked Source",
                canonical_url="https://example.com/blocked",
                title="Blocked Story",
                language="en",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Muted Source",
                canonical_url="https://example.com/muted",
                title="Muted Story",
                language="en",
                categories=["sports"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Hungarian Source",
                canonical_url="https://example.com/hungarian",
                title="Hungarian Story",
                language="hu",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()

    response = client.get(
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


def test_auth_login_endpoint(monkeypatch) -> None:
    client = _build_client()

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


def test_password_reset_request_endpoint(monkeypatch) -> None:
    client = _build_client()

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


def test_password_reset_confirm_endpoint(monkeypatch) -> None:
    client = _build_client()

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


def test_patch_me_endpoint(monkeypatch) -> None:
    client = _build_client()
    user = app.dependency_overrides[get_current_user]()

    def fake_patch_user(user_id: str, body: dict) -> dict:
        assert user_id == str(user.user_id)
        assert body == {"display_name": "New Name"}
        return {
            "user_id": user_id,
            "email": "test@example.com",
            "display_name": "New Name",
            "created_at": datetime.now(UTC).isoformat(),
        }

    def fake_get_preferences(user_id: str) -> dict:
        return {
            "user_id": user_id,
            "muted_keywords": [],
            "muted_categories": [],
            "blocked_source_ids": [],
            "languages": [],
            "updated_at": datetime.now(UTC).isoformat(),
        }

    monkeypatch.setattr("src.routers.user.account_patch_user", fake_patch_user)
    monkeypatch.setattr(
        "src.routers.user.account_get_preferences", fake_get_preferences
    )

    response = client.patch("/me", json={"display_name": "New Name"})
    assert response.status_code == 200
    assert response.json()["display_name"] == "New Name"
    assert response.json()["preferences"]["languages"] == []
    assert client.patch("/me/profile").status_code == 404


def test_patch_preferences_endpoint(monkeypatch) -> None:
    client = _build_client()
    user = app.dependency_overrides[get_current_user]()

    def fake_patch_preferences(
        user_id: str, body: dict, correlation_id: str | None
    ) -> dict:
        assert user_id == str(user.user_id)
        assert body == {"languages": ["en", "hu"]}
        assert correlation_id is not None
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

    response = client.patch("/me/preferences", json={"languages": ["en", "hu"]})
    assert response.status_code == 200
    assert response.json()["languages"] == ["en", "hu"]
    assert response.json()["muted_keywords"] == ["crypto"]


def test_get_source_endpoint(monkeypatch) -> None:
    client = _build_client()
    source_id = str(uuid4())

    def fake_get_source(sid: str) -> dict:
        now = datetime.now(UTC).isoformat()
        assert sid == source_id
        return {
            "source_id": sid,
            "url": "https://example.com/feed.xml",
            "title": "Source",
            "description": "Desc",
            "favicon": None,
            "site_url": "https://example.com",
            "verified": True,
            "last_crawled_at": None,
            "next_crawl_scheduled_at": now,
            "last_crawl_succeeded": True,
            "consecutive_failures": 0,
            "created_at": now,
            "updated_at": now,
        }

    def fake_list_subscriptions(user_id: str) -> list[dict]:
        return []

    monkeypatch.setattr(
        "src.routers.sources.ingestion_get_source", fake_get_source
    )
    monkeypatch.setattr(
        "src.routers.sources.account_list_subscriptions",
        fake_list_subscriptions,
    )

    response = client.get(f"/sources/{source_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == source_id
    assert "consecutive_failures" in data
    assert "next_crawl_scheduled_at" in data
    assert "health_score" not in data


def test_list_sources_endpoint(monkeypatch) -> None:
    client = _build_client()

    def fake_list_sources() -> list[dict]:
        now = datetime.now(UTC).isoformat()
        return [
            {
                "source_id": str(uuid4()),
                "url": "https://example.com/feed.xml",
                "title": "Source",
                "description": "Desc",
                "favicon": None,
                "site_url": "https://example.com",
                "verified": False,
                "last_crawled_at": None,
                "next_crawl_scheduled_at": now,
                "last_crawl_succeeded": True,
                "consecutive_failures": 0,
                "created_at": now,
                "updated_at": now,
            }
        ]

    def fake_list_subscriptions(user_id: str) -> list[dict]:
        return []

    monkeypatch.setattr(
        "src.routers.sources.ingestion_list_sources",
        fake_list_sources,
    )
    monkeypatch.setattr(
        "src.routers.sources.account_list_subscriptions",
        fake_list_subscriptions,
    )

    response = client.get("/sources")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Source"


def test_discover_sources_endpoint(monkeypatch) -> None:
    client = _build_client()

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
        "src.routers.sources.ingestion_discover_sources",
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
    monkeypatch,
) -> None:
    client = _build_client()
    captured: dict = {}

    def fake_create_source(body: dict) -> dict:
        captured.update(body)
        now = datetime.now(UTC).isoformat()
        return {
            "source_id": str(uuid4()),
            "url": "https://example.com/feed.xml",
            "title": body["title"],
            "description": body["description"],
            "favicon": body["favicon"],
            "site_url": "https://example.com",
            "verified": False,
            "last_crawled_at": None,
            "next_crawl_scheduled_at": now,
            "last_crawl_succeeded": False,
            "consecutive_failures": 0,
            "created_at": now,
            "updated_at": now,
        }

    monkeypatch.setattr(
        "src.routers.sources.ingestion_create_source",
        fake_create_source,
    )

    response = client.post(
        "/sources",
        json={
            "url": "https://example.com",
            "title": "Example",
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


def test_create_source_rejects_client_policy_fields() -> None:
    client = _build_client()
    response = client.post(
        "/sources",
        json={
            "url": "https://example.com/feed.xml",
            "verified": True,
            "submitted_by_user_id": str(uuid4()),
        },
    )
    assert response.status_code == 422


def test_patch_source_endpoint(monkeypatch) -> None:
    client = _build_client()
    source_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    captured: dict = {}

    def fake_patch_source(sid: str, body: dict) -> dict:
        assert sid == source_id
        captured.update(body)
        return {
            "source_id": sid,
            "url": "https://example.com/feed.xml",
            "title": body.get("title", "Existing title"),
            "description": body.get("description", "Feed description"),
            "favicon": body.get("favicon", "https://example.com/icon.png"),
            "site_url": "https://example.com",
            "verified": body.get("verified", False),
            "last_crawled_at": None,
            "next_crawl_scheduled_at": now,
            "last_crawl_succeeded": False,
            "consecutive_failures": 0,
            "created_at": now,
            "updated_at": now,
        }

    monkeypatch.setattr(
        "src.routers.sources.ingestion_patch_source", fake_patch_source
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

    for verified in (True, False):
        captured.clear()
        response = client.patch(
            f"/sources/{source_id}", json={"verified": verified}
        )
        assert response.status_code == 200
        assert captured == {"verified": verified}


def test_patch_source_requires_admin_scope() -> None:
    client = _build_client()
    source_id = str(uuid4())
    current_user = app.dependency_overrides[get_current_user]

    app.dependency_overrides[get_current_user] = lambda: AuthContext(
        user_id=uuid4(), token_type="access"
    )
    assert client.patch(f"/sources/{source_id}", json={}).status_code == 403

    def anonymous_user() -> AuthContext:
        raise HTTPException(
            status_code=401, detail="Missing Authorization header"
        )

    app.dependency_overrides[get_current_user] = anonymous_user
    assert client.patch(f"/sources/{source_id}", json={}).status_code == 401
    app.dependency_overrides[get_current_user] = current_user


@pytest.mark.parametrize(
    "method, payload",
    [
        ("post", {}),
        ("patch", {"title": " "}),
        ("patch", {"url": None}),
        ("patch", {"verified": None}),
    ],
)
def test_source_metadata_validation(method, payload) -> None:
    client = _build_client()
    if method == "post":
        path = "/sources"
        payload = {"url": "https://example.com/feed.xml"} | payload
    else:
        path = f"/sources/{uuid4()}"
    assert client.request(method, path, json=payload).status_code == 422


def test_admin_feed_returns_items() -> None:
    client = _build_client()

    db = next(app.dependency_overrides[get_db]())
    now = datetime.now(UTC)
    db.add(
        PostProjection(
            post_id=str(uuid4()),
            source_id=str(uuid4()),
            source_title="Admin Source",
            canonical_url="https://example.com/admin",
            title="General Story",
            language="en",
            keywords=["general"],
            published_at=now,
            updated_at=now,
        )
    )
    db.commit()

    response = client.get("/admin/feed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "General Story"


def test_admin_feed_requires_admin_scope() -> None:
    client = _build_client()

    def non_admin_user() -> AuthContext:
        return AuthContext(user_id=uuid4(), token_type="access")

    app.dependency_overrides[get_current_user] = non_admin_user
    response = client.get("/admin/feed")
    assert response.status_code == 403


def test_admin_get_post_endpoint(monkeypatch) -> None:
    client = _build_client()
    post_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    def fake_get(target_id: str) -> dict:
        assert target_id == post_id
        return {
            "post_id": target_id,
            "source_id": "source-1",
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


def test_get_me_composite_response(monkeypatch) -> None:
    client = _build_client()
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


def test_explore_filter_options_are_opt_in_and_self_excluding() -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            muted_keywords=[],
            muted_categories=[],
            blocked_source_ids=[],
            languages=["hu"],
            updated_at=now,
        )
    )
    db.add_all(
        [
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Technology Source",
                canonical_url="https://example.com/technology-en",
                title="Technology English",
                language="en",
                categories=["technology"],
                author="Example Author",
                keywords=["Climate", "policy"],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Business Source",
                canonical_url="https://example.com/business-hu",
                title="Business Hungarian",
                language="hu",
                categories=["business"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Business Source",
                canonical_url="https://example.com/business-en",
                title="Business English",
                language="en",
                categories=["business"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Technology Source",
                canonical_url="https://example.com/technology-hu",
                title="Technology Hungarian",
                language="hu",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()

    without_options = client.get(
        "/explore", params={"categories": "technology"}
    )
    assert without_options.status_code == 200
    assert "filter_options" not in without_options.json()

    response = client.get(
        "/explore",
        params=[
            ("categories", "technology"),
            ("languages", "en"),
            ("include_filter_options", "true"),
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert [item["title"] for item in payload["items"]] == [
        "Technology English"
    ]
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
    assert [
        option["title"] for option in payload["filter_options"]["sources"]
    ] == ["Technology Source"]


def test_explore_source_ids_are_repeatable_and_options_ignore_selection() -> (
    None
):
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    source_ids = [str(uuid4()) for _ in range(3)]
    now = datetime.now(UTC)
    db.add_all(
        [
            PostProjection(
                post_id=str(uuid4()),
                source_id=source_id,
                source_title=f"Source {index}",
                canonical_url=f"https://example.com/source/{index}",
                title=f"Source {index} story",
                language="en",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            )
            for index, source_id in enumerate(source_ids)
        ]
    )
    db.commit()

    response = client.get(
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
    assert {item["source_id"] for item in payload["items"]} == set(
        source_ids[:2]
    )
    assert {
        option["id"] for option in payload["filter_options"]["sources"]
    } == set(source_ids)


def test_filter_options_openapi_exposes_metadata_arrays() -> None:
    properties = app.openapi()["components"]["schemas"][
        "FilterOptionsResponse"
    ]["properties"]

    for field in ("authors", "keywords"):
        assert properties[field]["type"] == "array"
        assert properties[field]["items"] == {"type": "string"}


def test_explore_query_searches_fields_and_supports_web_syntax() -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    now = datetime.now(UTC)
    source_id = str(uuid4())
    db.add_all(
        [
            PostProjection(
                post_id="00000000-0000-0000-0000-000000000001",
                source_id=source_id,
                source_title="Search Source",
                canonical_url="https://example.com/search-title",
                title="Climate change report",
                language="en",
                keywords=["Technology trends"],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id="00000000-0000-0000-0000-000000000002",
                source_id=source_id,
                source_title="Search Source",
                canonical_url="https://example.com/search-description",
                title="Economy outlook",
                description="Climate policy update",
                language="en",
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id="00000000-0000-0000-0000-000000000003",
                source_id=source_id,
                source_title="Search Source",
                canonical_url="https://example.com/search-content",
                title="Research notes",
                content="Climate adaptation matters",
                language="en",
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id="00000000-0000-0000-0000-000000000004",
                source_id=source_id,
                source_title="Search Source",
                canonical_url="https://example.com/search-sports",
                title="Sports climate report",
                language="en",
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id="00000000-0000-0000-0000-000000000005",
                source_id=source_id,
                source_title="Search Source",
                canonical_url="https://example.com/search-accent",
                title="Café review",
                language="en",
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()

    climate = client.get("/explore", params={"query": "  CLIMATE "})
    keyword = client.get("/explore", params={"query": "Technology"})
    phrase = client.get("/explore", params={"query": '"climate change"'})
    negated = client.get("/explore", params={"query": "climate -sports"})
    cafe = client.get("/explore", params={"query": "cafe"})
    accented = client.get("/explore", params={"query": "Café"})

    assert climate.json()["total"] == 3
    assert keyword.json()["total"] == 1
    assert keyword.json()["items"][0]["post_id"] == (
        "00000000-0000-0000-0000-000000000001"
    )
    assert phrase.json()["total"] == 1
    assert phrase.json()["items"][0]["post_id"] == (
        "00000000-0000-0000-0000-000000000001"
    )
    assert negated.json()["total"] == 2
    assert cafe.json()["total"] == 0
    assert accented.json()["total"] == 1


def test_explore_query_validation_rejects_empty_and_sort_combinations() -> None:
    client = _build_client()

    assert client.get("/explore", params={"query": "   "}).status_code == 422
    assert client.get("/explore", params={"query": "..."}).status_code == 422
    assert (
        client.get(
            "/explore",
            params={"query": "climate", "sort": "oldest"},
        ).status_code
        == 422
    )
    assert (
        client.get("/explore", params={"query": "x" * 201}).status_code == 422
    )


def test_list_and_detail_post_contracts(monkeypatch) -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    now = datetime.now(UTC)

    post_id = str(uuid4())
    source_id = str(uuid4())
    db.add(
        PostProjection(
            post_id=post_id,
            source_id=source_id,
            source_title="Single Source",
            canonical_url="https://example.com/single-article",
            title="Single Post",
            description="Detail",
            author="Example Author",
            language="en",
            keywords=["climate", "policy"],
            content="Full body text",
            published_at=now,
            updated_at=now,
        )
    )
    db.commit()

    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": source_id}],
    )

    for path in ("/feed", "/explore"):
        list_response = client.get(path)
        assert list_response.status_code == 200
        payload = list_response.json()
        list_item = (
            payload["headlines"][0] if path == "/feed" else payload["items"][0]
        )
        assert list_item["has_content"] is True
        assert "content" not in list_item

    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["post_id"] == post_id
    assert payload["title"] == "Single Post"
    assert payload["content"] == "Full body text"
    assert payload["author"] == "Example Author"
    assert payload["keywords"] == ["climate", "policy"]


def test_list_sources_subscribed_only_filter(monkeypatch) -> None:
    client = _build_client()
    now = datetime.now(UTC).isoformat()
    source_1 = str(uuid4())
    source_2 = str(uuid4())

    def fake_list_sources() -> list[dict]:
        return [
            {
                "source_id": source_1,
                "url": "https://example.com/1",
                "title": "Subscribed Source",
                "description": "Desc",
                "favicon": None,
                "site_url": "https://example.com",
                "verified": True,
                "last_crawled_at": None,
                "next_crawl_scheduled_at": now,
                "last_crawl_succeeded": True,
                "consecutive_failures": 0,
                "created_at": now,
                "updated_at": now,
            },
            {
                "source_id": source_2,
                "url": "https://example.com/2",
                "title": "Unsubscribed Source",
                "description": "Desc",
                "favicon": None,
                "site_url": "https://example.com",
                "verified": False,
                "last_crawled_at": None,
                "next_crawl_scheduled_at": now,
                "last_crawl_succeeded": True,
                "consecutive_failures": 0,
                "created_at": now,
                "updated_at": now,
            },
        ]

    def fake_list_subscriptions(user_id: str) -> list[dict]:
        return [
            {
                "user_id": user_id,
                "source_id": source_1,
                "created_at": now,
            }
        ]

    monkeypatch.setattr(
        "src.routers.sources.ingestion_list_sources",
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


def test_feed_pagination_pages_and_counts(monkeypatch) -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            muted_keywords=[],
            muted_categories=[],
            blocked_source_ids=[],
            languages=[],
            updated_at=now,
        )
    )

    source_ids = [str(uuid4()) for _ in range(5)]
    for i, source_id in enumerate(source_ids):
        db.add(
            PostProjection(
                post_id=str(uuid4()),
                source_id=source_id,
                source_title=f"Source {i}",
                canonical_url=f"https://example.com/{i}",
                title=f"Post {i}",
                language="en",
                keywords=[],
                published_at=datetime.fromtimestamp(
                    1700000000 + i * 100, tz=UTC
                ),
                updated_at=now,
            )
        )
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
    assert p1["total"] == 2
    assert p1["page"] == 1
    assert p1["page_count"] == 1
    assert p1["page_size"] == 2
    assert len(p1["items"]) == 2
    assert p1["items"][0]["title"] == "Post 1"
    assert p1["items"][1]["title"] == "Post 0"

    # Page 2 with page_size=2
    res_p2 = client.get("/feed", params={"page": 2, "page_size": 2})
    assert res_p2.status_code == 200
    p2 = res_p2.json()
    assert p2["page"] == 2
    assert p2["page_count"] == 1
    assert p2["items"] == []
    assert "headlines" not in p2


def test_admin_feed_pagination() -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    now = datetime.now(UTC)

    for i in range(3):
        db.add(
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title=f"Admin Source {i}",
                canonical_url=f"https://example.com/admin/{i}",
                title=f"Admin Post {i}",
                language="en",
                keywords=[],
                published_at=datetime.fromtimestamp(
                    1700000000 + i * 100, tz=UTC
                ),
                updated_at=now,
            )
        )
    db.commit()

    res = client.get("/admin/feed", params={"page": 1, "page_size": 2})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_count"] == 2
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


def test_get_my_subscriptions(monkeypatch) -> None:
    client = _build_client()
    user = app.dependency_overrides[get_current_user]()
    src_id = str(uuid4())
    now_iso = datetime.now(UTC).isoformat()

    mock_subs = [
        {
            "user_id": str(user.user_id),
            "source_id": src_id,
            "created_at": now_iso,
        }
    ]

    monkeypatch.setattr(
        "src.routers.user.account_list_subscriptions",
        lambda uid: mock_subs if uid == str(user.user_id) else [],
    )

    res = client.get("/me/subscriptions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["source_id"] == src_id
    assert data[0]["user_id"] == str(user.user_id)


def test_create_my_subscription_success(monkeypatch) -> None:
    client = _build_client()
    user = app.dependency_overrides[get_current_user]()
    src_id = str(uuid4())
    now_iso = datetime.now(UTC).isoformat()

    def mock_create(uid, body, correlation_id=None):
        return {
            "user_id": uid,
            "source_id": body["source_id"],
            "created_at": now_iso,
        }

    monkeypatch.setattr(
        "src.routers.user.account_create_subscription",
        mock_create,
    )

    res = client.post(
        "/me/subscriptions",
        json={"source_id": src_id},
        headers={"x-correlation-id": "test-corr-id"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["source_id"] == src_id
    assert data["user_id"] == str(user.user_id)


def test_create_my_subscription_conflict(monkeypatch) -> None:
    from src.adapters.service_clients import ServiceClientError

    client = _build_client()
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


def test_delete_my_subscription_success(monkeypatch) -> None:
    client = _build_client()
    src_id = str(uuid4())
    deleted = []

    def mock_delete(uid, source_id, correlation_id=None):
        deleted.append((uid, source_id))

    monkeypatch.setattr(
        "src.routers.user.account_delete_subscription",
        mock_delete,
    )

    res = client.delete(f"/me/subscriptions/{src_id}")
    assert res.status_code == 204
    assert len(deleted) == 1
    assert deleted[0][1] == src_id


def test_delete_my_subscription_not_found(monkeypatch) -> None:
    from src.adapters.service_clients import ServiceClientError

    client = _build_client()
    src_id = str(uuid4())

    def mock_not_found(*args, **kwargs):
        raise ServiceClientError(
            status_code=404, detail="Subscription not found"
        )

    monkeypatch.setattr(
        "src.routers.user.account_delete_subscription",
        mock_not_found,
    )

    res = client.delete(f"/me/subscriptions/{src_id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Subscription not found"


def test_feed_and_explore_filter_muted_keywords(monkeypatch) -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)
    clean_source_id = str(uuid4())
    muted_source_id = str(uuid4())
    paramount_source_id = str(uuid4())

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            muted_keywords=["A$AP Rocky", "paramount"],
            muted_categories=[],
            blocked_source_ids=[],
            languages=["en"],
            updated_at=now,
        )
    )
    db.add(
        PostProjection(
            post_id=str(uuid4()),
            source_id=clean_source_id,
            source_title="Clean Source",
            canonical_url="https://example.com/clean-article",
            title="Clean Post",
            language="en",
            keywords=["technology", "ai"],
            published_at=now,
            updated_at=now,
        )
    )
    db.add(
        PostProjection(
            post_id=str(uuid4()),
            source_id=muted_source_id,
            source_title="Music Source",
            canonical_url="https://example.com/music-article",
            title="asap rocky returns to Budapest",
            language="en",
            keywords=["ASAP Rocky", "concert"],
            published_at=now,
            updated_at=now,
        )
    )
    db.add(
        PostProjection(
            post_id=str(uuid4()),
            source_id=paramount_source_id,
            source_title="Film Source",
            canonical_url="https://example.com/film-article",
            title="Studio merger finalized",
            language="en",
            keywords=["Paramount", "Warner Bros."],
            published_at=now,
            updated_at=now,
        )
    )
    db.commit()

    response = client.get("/explore")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "Clean Post"

    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [
            {"source_id": clean_source_id},
            {"source_id": muted_source_id},
            {"source_id": paramount_source_id},
        ],
    )
    response = client.get("/feed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert [item["title"] for item in payload["headlines"]] == ["Clean Post"]


def test_explore_explicit_source_filter_cannot_include_unverified(
    monkeypatch,
) -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    verified_source_id = str(uuid4())
    unverified_source_id = str(uuid4())
    now = datetime.now(UTC)
    db.add_all(
        [
            PostProjection(
                post_id=str(uuid4()),
                source_id=verified_source_id,
                source_title="Verified",
                canonical_url="https://example.com/verified",
                title="Visible verified article",
                language="en",
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=unverified_source_id,
                source_title="Unverified",
                canonical_url="https://example.com/unverified",
                title="Hidden unverified article",
                language="hu",
                published_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()

    current_verified_ids = {verified_source_id}

    def list_verified_sources(*, verified_only: bool) -> list[dict]:
        assert verified_only is True
        return [{"source_id": source_id} for source_id in current_verified_ids]

    monkeypatch.setattr(
        "src.services.feed_service.ingestion_list_sources",
        list_verified_sources,
    )

    response = client.get(
        "/explore",
        params=[
            ("source_ids", verified_source_id),
            ("source_ids", unverified_source_id),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["source_id"] for item in payload["items"]] == [
        verified_source_id
    ]

    current_verified_ids.clear()
    no_longer_verified = client.get("/explore")
    assert no_longer_verified.status_code == 200
    assert no_longer_verified.json()["total"] == 0

    monkeypatch.setattr(
        "src.services.feed_service.ingestion_list_sources",
        lambda *, verified_only: [],
    )
    empty = client.get("/explore", params={"include_filter_options": "true"})
    assert empty.status_code == 200
    assert empty.json()["total"] == 0
    assert empty.json()["filter_options"]["sources"] == []


def test_explore_category_filter_uses_normalized_category_not_keywords() -> (
    None
):
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            muted_keywords=[],
            muted_categories=[" SPORTS "],
            blocked_source_ids=[],
            languages=["en"],
            updated_at=now,
        )
    )
    db.add_all(
        [
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Technology Source",
                canonical_url="https://example.com/technology",
                title="Technology Category",
                language="en",
                categories=["technology"],
                keywords=["business"],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Business Source",
                canonical_url="https://example.com/business",
                title="Technology Keyword",
                language="en",
                categories=["business"],
                keywords=["technology"],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Sports Source",
                canonical_url="https://example.com/sports",
                title="Muted Sports Category",
                language="en",
                categories=["sports"],
                keywords=["technology"],
                published_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()

    response = client.get("/explore", params={"categories": " TECHNOLOGY "})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["title"] for item in payload["items"]] == [
        "Technology Category"
    ]


def test_explore_filter_options_are_opt_in_and_cover_all_pages() -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    now = datetime.now(UTC)

    db.add_all(
        [
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="One Source",
                canonical_url="https://example.com/one",
                title="One",
                language="en",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Two Source",
                canonical_url="https://example.com/two",
                title="Two",
                language="en",
                categories=["technology"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Three Source",
                canonical_url="https://example.com/three",
                title="Three",
                language="en",
                categories=["business"],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
            PostProjection(
                post_id=str(uuid4()),
                source_id=str(uuid4()),
                source_title="Four Source",
                canonical_url="https://example.com/four",
                title="Four",
                language="en",
                categories=[],
                keywords=[],
                published_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()

    without_options = client.get("/explore", params={"page_size": 1})
    with_options = client.get(
        "/explore",
        params={"page_size": 1, "include_filter_options": "true"},
    )
    selected = client.get(
        "/explore",
        params={
            "categories": "TECHNOLOGY",
            "include_filter_options": "true",
        },
    )

    assert without_options.status_code == 200
    assert "filter_options" not in without_options.json()
    assert with_options.status_code == 200
    assert with_options.json()["filter_options"]["categories"] == [
        "business",
        "technology",
    ]
    assert len(with_options.json()["filter_options"]["sources"]) == 4
    assert selected.status_code == 200
    assert selected.json()["total"] == 2
    assert selected.json()["filter_options"]["categories"] == [
        "business",
        "technology",
    ]
    assert len(selected.json()["filter_options"]["sources"]) == 2


def test_personal_feed_returns_empty_page_without_subscriptions(
    monkeypatch,
) -> None:
    client = _build_client()
    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    sub_source_id = str(uuid4())
    unsub_source_id = str(uuid4())

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            muted_keywords=[],
            muted_categories=[],
            blocked_source_ids=[],
            languages=["en"],
            updated_at=now,
        )
    )
    db.add(
        PostProjection(
            post_id=str(uuid4()),
            source_id=sub_source_id,
            source_title="Subscribed Source",
            canonical_url="https://example.com/sub",
            title="Subscribed Post",
            language="en",
            keywords=[],
            published_at=now,
            updated_at=now,
        )
    )
    db.add(
        PostProjection(
            post_id=str(uuid4()),
            source_id=unsub_source_id,
            source_title="Unsubscribed Source",
            canonical_url="https://example.com/unsub",
            title="Unsubscribed Post",
            language="en",
            keywords=[],
            published_at=now,
            updated_at=now,
        )
    )
    db.commit()

    subscriptions = [{"user_id": str(user.user_id), "source_id": sub_source_id}]

    def fake_list_subscriptions(user_id: str) -> list[dict]:
        return subscriptions if user_id == str(user.user_id) else []

    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        fake_list_subscriptions,
    )

    personal_res = client.get("/feed")
    assert personal_res.status_code == 200
    assert personal_res.json()["total"] == 0
    assert personal_res.json()["items"] == []
    assert personal_res.json()["headlines"][0]["title"] == "Subscribed Post"

    subscriptions.clear()
    empty_res = client.get("/feed", params={"include_filter_options": "true"})
    assert empty_res.status_code == 200
    assert empty_res.json()["total"] == 0
    assert empty_res.json()["filter_options"] == {
        "categories": [],
        "languages": [],
        "authors": [],
        "keywords": [],
    }


def test_upstream_request_error_returns_502(monkeypatch) -> None:
    import httpx

    client = _build_client()
    orig_request = httpx.Client.request

    def fake_request(self, *args, **kwargs):
        if isinstance(self, TestClient):
            return orig_request(self, *args, **kwargs)
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.Client, "request", fake_request)

    response = client.get("/sources")
    assert response.status_code == 502
    assert response.json()["detail"] == "Upstream service unavailable"


def test_public_post_responses_always_use_category_lists():
    client = _build_client()
    source = str(uuid4())
    one, empty = uuid4(), uuid4()
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    db.add_all(
        [
            PostProjection(
                post_id=str(one),
                source_id=source,
                source_title="Publisher",
                title="Research",
                categories=["science", "health"],
                keywords=[],
            ),
            PostProjection(
                post_id=str(empty),
                source_id=source,
                source_title="Publisher",
                title="Other article",
                categories=[],
                keywords=[],
            ),
        ]
    )
    db.commit()
    db.close()
    for post_id, categories in [(one, ["science", "health"]), (empty, [])]:
        response = client.get(f"/posts/{post_id}")
        assert response.status_code == 200
        assert response.json()["categories"] == categories
        assert "category" not in response.json()
    response = client.get(
        "/explore",
        params=[
            ("categories", "science"),
            ("categories", "health"),
            ("include_filter_options", "true"),
        ],
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["categories"] == ["science", "health"]
    assert "category" not in response.json()["items"][0]
    schema = app.openapi()["components"]["schemas"]["PostListItemResponse"]
    assert (
        "categories" in schema["properties"]
        and "category" not in schema["properties"]
    )

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.config.database import get_db
from src.models.read_models import (
    ArticleProjection,
    Base,
    UserPreferencesProjection,
)
from src.schemas.api import AuthContext
from src.services.auth import get_current_user


def _build_client() -> TestClient:
    app.state.testing = True

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
        token_version=1,
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


def test_feed_returns_items() -> None:
    client = _build_client()

    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()

    source_id = str(uuid4())
    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            preferred_categories=["technology"],
            preferred_languages=["en"],
            excluded_languages=[],
            blocked_source_ids=[],
            updated_at=datetime.now(UTC),
        )
    )
    db.add(
        ArticleProjection(
            article_id=str(uuid4()),
            source_id=source_id,
            canonical_url="https://example.com/1",
            title="Tech Story",
            language="en",
            keywords=["technology"],
            topics=[],
            published_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    db.commit()

    response = client.get("/feed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "Tech Story"


def test_feed_prioritizes_recency_with_preference_ties() -> None:
    client = _build_client()

    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            preferred_categories=["technology"],
            preferred_languages=["en"],
            excluded_languages=[],
            blocked_source_ids=[],
            updated_at=now,
        )
    )

    db.add(
        ArticleProjection(
            article_id=str(uuid4()),
            source_id=str(uuid4()),
            canonical_url="https://example.com/older",
            title="Older Preferred",
            language="en",
            keywords=["technology"],
            topics=[],
            published_at=now.replace(year=now.year - 1),
            updated_at=now.replace(year=now.year - 1),
        )
    )
    db.add(
        ArticleProjection(
            article_id=str(uuid4()),
            source_id=str(uuid4()),
            canonical_url="https://example.com/newer",
            title="Newer Preferred",
            language="en",
            keywords=["technology"],
            topics=[],
            published_at=now,
            updated_at=now,
        )
    )
    db.commit()

    response = client.get("/feed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["items"][0]["title"] == "Newer Preferred"
    assert payload["items"][1]["title"] == "Older Preferred"


def test_feed_use_profile_false_ignores_profile_filters() -> None:
    client = _build_client()

    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            preferred_categories=[],
            preferred_languages=[],
            excluded_languages=["en"],
            blocked_source_ids=[],
            updated_at=now,
        )
    )
    db.add(
        ArticleProjection(
            article_id=str(uuid4()),
            source_id=str(uuid4()),
            canonical_url="https://example.com/en-story",
            title="English Story",
            language="en",
            keywords=["technology"],
            topics=[],
            published_at=now,
            updated_at=now,
        )
    )
    db.commit()

    profiled = client.get("/feed")
    assert profiled.status_code == 200
    assert profiled.json()["total"] == 0

    unprofiled = client.get(
        "/feed", params={"use_profile": "false"}
    )
    assert unprofiled.status_code == 200
    assert unprofiled.json()["total"] == 1


def test_feed_override_exclude_languages_replaces_profile_value() -> (
    None
):
    client = _build_client()

    db = next(app.dependency_overrides[get_db]())
    user = app.dependency_overrides[get_current_user]()
    now = datetime.now(UTC)

    db.add(
        UserPreferencesProjection(
            user_id=str(user.user_id),
            preferred_categories=[],
            preferred_languages=[],
            excluded_languages=["fr"],
            blocked_source_ids=[],
            updated_at=now,
        )
    )

    db.add(
        ArticleProjection(
            article_id=str(uuid4()),
            source_id=str(uuid4()),
            canonical_url="https://example.com/en",
            title="EN Story",
            language="en",
            keywords=["technology"],
            topics=[],
            published_at=now,
            updated_at=now,
        )
    )
    db.add(
        ArticleProjection(
            article_id=str(uuid4()),
            source_id=str(uuid4()),
            canonical_url="https://example.com/fr",
            title="FR Story",
            language="fr",
            keywords=["technology"],
            topics=[],
            published_at=now,
            updated_at=now,
        )
    )
    db.commit()

    response = client.get(
        "/feed", params=[("exclude_languages", "en")]
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "FR Story"


def test_auth_login_endpoint(monkeypatch) -> None:
    client = _build_client()

    def fake_login(body: dict) -> dict:
        assert body["email"] == "user@example.com"
        return {
            "access_token": "access-123",
            "refresh_token": "refresh-123",
            "token_type": "Bearer",
        }

    monkeypatch.setattr(
        "src.routers.auth.account_login", fake_login
    )

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
        return {
            "status": "accepted",
            "reset_token": "reset-token-123",
        }

    monkeypatch.setattr(
        "src.routers.auth.account_password_reset_request",
        fake_password_reset_request,
    )

    response = client.post(
        "/auth/password-reset/request",
        json={"email": "user@example.com"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["reset_token"] == "reset-token-123"


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


def test_create_subscription_endpoint(monkeypatch) -> None:
    client = _build_client()
    user = app.dependency_overrides[get_current_user]()
    source_id = str(uuid4())

    def fake_create_subscription(
        user_id: str, body: dict, correlation_id: str | None
    ) -> dict:
        assert user_id == str(user.user_id)
        assert correlation_id is not None
        return {
            "user_id": user_id,
            "source_id": body["source_id"],
            "created_at": datetime.now(UTC).isoformat(),
        }

    monkeypatch.setattr(
        "src.routers.sources.account_create_subscription",
        fake_create_subscription,
    )

    response = client.post(
        "/me/subscriptions", json={"source_id": source_id}
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["user_id"] == str(user.user_id)
    assert payload["source_id"] == source_id


def test_list_subscriptions_endpoint(monkeypatch) -> None:
    client = _build_client()
    user = app.dependency_overrides[get_current_user]()
    source_id = str(uuid4())

    def fake_list_subscriptions(user_id: str) -> list[dict]:
        assert user_id == str(user.user_id)
        return [
            {
                "user_id": user_id,
                "source_id": source_id,
                "created_at": datetime.now(UTC).isoformat(),
            }
        ]

    monkeypatch.setattr(
        "src.routers.sources.account_list_subscriptions",
        fake_list_subscriptions,
    )

    response = client.get("/me/subscriptions")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["source_id"] == source_id


def test_patch_profile_endpoint(monkeypatch) -> None:
    client = _build_client()
    user = app.dependency_overrides[get_current_user]()

    def fake_patch_profile(
        user_id: str, body: dict, correlation_id: str | None
    ) -> dict:
        assert user_id == str(user.user_id)
        assert body == {"display_name": "New Name"}
        assert correlation_id is not None
        return {
            "user_id": user_id,
            "display_name": "New Name",
            "bio": None,
            "avatar_url": None,
            "updated_at": datetime.now(UTC).isoformat(),
        }

    monkeypatch.setattr(
        "src.routers.user.account_patch_profile", fake_patch_profile
    )

    response = client.patch(
        "/me/profile", json={"display_name": "New Name"}
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "New Name"


def test_patch_preferences_endpoint(monkeypatch) -> None:
    client = _build_client()
    user = app.dependency_overrides[get_current_user]()

    def fake_patch_preferences(
        user_id: str, body: dict, correlation_id: str | None
    ) -> dict:
        assert user_id == str(user.user_id)
        assert body == {"excluded_languages": ["fr"]}
        assert correlation_id is not None
        return {
            "user_id": user_id,
            "preferred_categories": ["technology"],
            "preferred_languages": ["en"],
            "excluded_languages": ["fr"],
            "blocked_source_ids": [],
            "updated_at": datetime.now(UTC).isoformat(),
        }

    monkeypatch.setattr(
        "src.routers.user.account_patch_preferences",
        fake_patch_preferences,
    )

    response = client.patch(
        "/me/preferences", json={"excluded_languages": ["fr"]}
    )
    assert response.status_code == 200
    assert response.json()["excluded_languages"] == ["fr"]


def test_get_source_endpoint(monkeypatch) -> None:
    client = _build_client()
    source_id = str(uuid4())

    def fake_get_source(feed_id: str) -> dict:
        now = datetime.now(UTC).isoformat()
        assert feed_id == source_id
        return {
            "feed_id": feed_id,
            "user_id": str(uuid4()),
            "url": "https://example.com/feed.xml",
            "title": "Source",
            "description": "Desc",
            "favicon": None,
            "last_crawled_at": None,
            "next_crawl_scheduled_at": now,
            "last_crawl_succeeded": True,
            "consecutive_failures": 0,
            "health_score": 1.0,
            "created_at": now,
            "updated_at": now,
        }

    monkeypatch.setattr(
        "src.routers.sources.ingestion_get_source", fake_get_source
    )

    response = client.get(f"/sources/{source_id}")
    assert response.status_code == 200
    assert response.json()["feed_id"] == source_id


def test_list_sources_endpoint(monkeypatch) -> None:
    client = _build_client()

    def fake_list_sources() -> list[dict]:
        now = datetime.now(UTC).isoformat()
        return [
            {
                "feed_id": str(uuid4()),
                "user_id": str(uuid4()),
                "url": "https://example.com/feed.xml",
                "title": "Source",
                "description": "Desc",
                "favicon": None,
                "last_crawled_at": None,
                "next_crawl_scheduled_at": now,
                "last_crawl_succeeded": True,
                "consecutive_failures": 0,
                "health_score": 1.0,
                "created_at": now,
                "updated_at": now,
            }
        ]

    monkeypatch.setattr(
        "src.routers.sources.ingestion_list_sources",
        fake_list_sources,
    )

    response = client.get("/sources")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Source"


def test_explore_sources_endpoint(monkeypatch) -> None:
    client = _build_client()

    def fake_explore_sources(body: dict) -> list[dict]:
        assert body["url"] == "https://example.com"
        return [
            {
                "url": "https://example.com/feed.xml",
                "title": "Discovered",
                "content_type": "application/rss+xml",
                "favicon": "https://example.com/favicon.ico",
                "description": "Feed description",
            }
        ]

    monkeypatch.setattr(
        "src.routers.sources.ingestion_explore_sources",
        fake_explore_sources,
    )

    response = client.post(
        "/sources/explore", json={"url": "https://example.com"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Discovered"


def test_delete_source_endpoint(monkeypatch) -> None:
    client = _build_client()
    source_id = str(uuid4())

    called = {"value": False}

    def fake_delete_source(feed_id: str) -> None:
        assert feed_id == source_id
        called["value"] = True

    monkeypatch.setattr(
        "src.routers.sources.ingestion_delete_source",
        fake_delete_source,
    )

    response = client.delete(f"/sources/{source_id}")
    assert response.status_code == 204
    assert called["value"] is True


def test_patch_source_endpoint(monkeypatch) -> None:
    client = _build_client()
    source_id = str(uuid4())

    def fake_patch_source(feed_id: str, body: dict) -> dict:
        now = datetime.now(UTC).isoformat()
        assert feed_id == source_id
        assert body == {"title": "Updated"}
        return {
            "feed_id": feed_id,
            "user_id": str(uuid4()),
            "url": "https://example.com/feed.xml",
            "title": "Updated",
            "description": "Desc",
            "favicon": None,
            "last_crawled_at": None,
            "next_crawl_scheduled_at": now,
            "last_crawl_succeeded": True,
            "consecutive_failures": 0,
            "health_score": 1.0,
            "created_at": now,
            "updated_at": now,
        }

    monkeypatch.setattr(
        "src.routers.sources.ingestion_patch_source",
        fake_patch_source,
    )

    response = client.patch(
        f"/sources/{source_id}", json={"title": "Updated"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


def test_admin_feed_returns_items() -> None:
    client = _build_client()

    db = next(app.dependency_overrides[get_db]())
    now = datetime.now(UTC)
    db.add(
        ArticleProjection(
            article_id=str(uuid4()),
            source_id=str(uuid4()),
            canonical_url="https://example.com/admin",
            title="General Story",
            language="en",
            keywords=["general"],
            topics=[],
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
        return AuthContext(
            user_id=uuid4(), token_type="access", token_version=1
        )

    app.dependency_overrides[get_current_user] = non_admin_user
    response = client.get("/admin/feed")
    assert response.status_code == 403


def test_admin_articles_count_endpoint(monkeypatch) -> None:
    client = _build_client()

    def fake_count() -> dict:
        return {"count": 42}

    monkeypatch.setattr(
        "src.routers.feed.content_articles_count", fake_count
    )

    response = client.get("/admin/articles/count")
    assert response.status_code == 200
    assert response.json()["count"] == 42


def test_admin_articles_list_endpoint(monkeypatch) -> None:
    client = _build_client()

    now = datetime.now(UTC).isoformat()

    def fake_list(params: dict) -> list[dict]:
        assert params["limit"] == 25
        assert params["skip"] == 5
        assert params["source_id"] == "source-1"
        return [
            {
                "id": str(uuid4()),
                "feed_id": "source-1",
                "item_guid": "guid-1",
                "url": "https://example.com/article",
                "title": "Admin Article",
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
        ]

    monkeypatch.setattr(
        "src.routers.feed.content_list_articles", fake_list
    )

    response = client.get(
        "/admin/articles",
        params={"limit": 25, "skip": 5, "source_id": "source-1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Admin Article"


def test_admin_get_article_endpoint(monkeypatch) -> None:
    client = _build_client()
    article_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    def fake_get(target_id: str) -> dict:
        assert target_id == article_id
        return {
            "id": target_id,
            "feed_id": "source-1",
            "item_guid": "guid-1",
            "url": "https://example.com/article",
            "title": "Admin Article",
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

    monkeypatch.setattr(
        "src.routers.feed.content_get_article", fake_get
    )

    response = client.get(f"/admin/articles/{article_id}")
    assert response.status_code == 200
    assert response.json()["id"] == article_id

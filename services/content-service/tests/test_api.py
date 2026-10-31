import json
from contextlib import nullcontext
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.config.settings import settings
from src.models.post import Post

SOURCE_ONE = UUID("00000000-0000-0000-0000-000000000001")
SOURCE_TWO = UUID("00000000-0000-0000-0000-000000000002")


def _seed_posts(db_session, post_id: UUID, other_id: UUID):
    now = datetime.now(UTC).replace(tzinfo=None)
    db_session.add(
        Post(
            post_id=post_id,
            source_id=SOURCE_ONE,
            item_guid="guid-1",
            url="https://example.com/a",
            source_title="Source One",
            title="Tech News",
            description="desc",
            category="technology",
            content="content",
            author="Author",
            published_at=now,
            crawled_at=now,
            parsed_at=now,
            image_url=None,
            language="en",
            keywords=["technology", "ai"],
        )
    )
    db_session.add(
        Post(
            post_id=other_id,
            source_id=SOURCE_TWO,
            item_guid="guid-2",
            url="https://example.com/b",
            source_title="Source Two",
            title="Sports",
            description="desc",
            category="sports",
            content="content",
            author="Author",
            published_at=now,
            crawled_at=now,
            parsed_at=now,
            image_url=None,
            language="fr",
            keywords=["sports", "football"],
        )
    )
    db_session.commit()


def test_health(client: TestClient, monkeypatch) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "content-service"
    thread = MagicMock()
    consumer = MagicMock(is_consuming=True)
    monkeypatch.setattr(app.state, "consumer_thread", thread)
    monkeypatch.setattr(app.state, "consumer", consumer)
    monkeypatch.setattr("src.app.database_ready", lambda: True)
    assert client.get("/live").status_code == 200
    assert client.get("/ready").status_code == 200
    consumer.is_consuming = False
    assert client.get("/ready").status_code == 503
    assert client.get("/live").status_code == 200
    consumer.is_consuming = True
    monkeypatch.setattr("src.app.database_ready", lambda: False)
    assert client.get("/ready").status_code == 503
    assert client.get("/live").status_code == 200
    monkeypatch.setattr("src.app.database_ready", lambda: True)
    assert client.get("/ready").status_code == 200
    thread.is_alive.return_value = False
    assert client.get("/live").status_code == 503
    assert client.get("/ready").status_code == 503


def test_get_post_by_id(client: TestClient, db_session) -> None:
    post_id = uuid4()
    other_id = uuid4()
    _seed_posts(db_session, post_id, other_id)

    by_id = client.get(f"/posts/{post_id}")
    assert by_id.status_code == 200
    assert by_id.json()["post_id"] == str(post_id)
    assert by_id.json()["post_revision"] == 1
    assert client.get(f"/posts/{uuid4()}").status_code == 404


def test_patch_post_updates_revision_and_publishes_snapshot(
    client: TestClient, db_session, monkeypatch
) -> None:
    post_id = uuid4()
    _seed_posts(db_session, post_id, uuid4())
    channel = MagicMock()
    monkeypatch.setattr(
        "src.routers.posts.publisher_channel", lambda **_: nullcontext(channel)
    )

    response = client.patch(
        f"/posts/{post_id}",
        json={
            "title": "  Corrected title  ",
            "description": None,
            "published_at": "2026-01-02T12:30:00Z",
        },
        headers={"x-admin-token": "test-admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Corrected title"
    assert response.json()["description"] is None
    assert response.json()["post_revision"] == 2
    assert response.json()["publication_status"] == "published"
    payload = json.loads(channel.basic_publish.call_args.kwargs["body"])["payload"]
    assert payload["post_revision"] == 2
    assert payload["title"] == "Corrected title"
    assert payload["description"] is None
    assert payload["published_at"] == "2026-01-02T12:30:00+00:00"
    assert db_session.get(Post, post_id).post_revision == 2


@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
def test_post_write_rolls_back_before_publication_when_commit_fails(
    client: TestClient, db_session, monkeypatch, method
) -> None:
    post_id = uuid4()
    _seed_posts(db_session, post_id, uuid4())
    publisher = MagicMock()
    monkeypatch.setattr("src.routers.posts.publisher_channel", publisher)
    with patch.object(
        db_session, "commit", side_effect=RuntimeError("commit failed")
    ):
        with pytest.raises(RuntimeError, match="commit failed"):
            client.request(
                method,
                f"/posts/{post_id}",
                json={"title": "Should roll back"},
                headers={"x-admin-token": "test-admin-token"},
            )
    publisher.assert_not_called()
    stored = db_session.get(Post, post_id)
    assert stored.title == "Tech News"
    assert stored.post_revision == 1
    assert not stored.is_deleted


def test_patch_post_fails_closed_and_reports_publication_failure(
    client: TestClient, db_session, monkeypatch
) -> None:
    post_id = uuid4()
    _seed_posts(db_session, post_id, uuid4())
    denied = client.patch(f"/posts/{post_id}", json={"title": "Edited"})
    assert denied.status_code == 401
    assert db_session.get(Post, post_id).title == "Tech News"

    monkeypatch.setattr(
        "src.routers.posts.publisher_channel",
        lambda **_: (_ for _ in ()).throw(RuntimeError("broker unavailable")),
    )
    partial = client.patch(
        f"/posts/{post_id}",
        json={"title": "Edited"},
        headers={"x-admin-token": "test-admin-token"},
    )
    assert partial.status_code == 200
    assert partial.json()["title"] == "Edited"
    assert partial.json()["post_revision"] == 2
    assert partial.json()["publication_status"] == "event_pending"


def test_patch_post_rejects_identity_fields_and_null_title(
    client: TestClient,
) -> None:
    post_id = uuid4()
    assert (
        client.patch(
            f"/posts/{post_id}",
            json={},
            headers={"x-admin-token": "test-admin-token"},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/posts/{post_id}",
            json={"source_id": str(SOURCE_ONE)},
            headers={"x-admin-token": "test-admin-token"},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/posts/{post_id}",
            json={"title": None},
            headers={"x-admin-token": "test-admin-token"},
        ).status_code
        == 422
    )


def test_delete_post_retains_marker_and_publishes_revisioned_event(
    client: TestClient, db_session, monkeypatch
) -> None:
    post_id = uuid4()
    _seed_posts(db_session, post_id, uuid4())
    channel = MagicMock()
    monkeypatch.setattr(
        "src.routers.posts.publisher_channel", lambda **_: nullcontext(channel)
    )
    headers = {"x-admin-token": "test-admin-token"}

    assert client.delete(f"/posts/{post_id}").status_code == 401
    assert client.get(f"/posts/{post_id}").status_code == 200
    channel.basic_publish.side_effect = RuntimeError("broker unavailable")
    partial = client.delete(f"/posts/{post_id}", headers=headers)
    assert partial.status_code == 503
    assert "Post is deleted" in partial.json()["detail"]
    retained = db_session.get(Post, post_id)
    assert retained.is_deleted is True
    assert retained.post_revision == 2
    deleted_at = retained.deleted_at

    channel.basic_publish.side_effect = None
    response = client.delete(f"/posts/{post_id}", headers=headers)

    assert response.status_code == 204
    assert client.get(f"/posts/{post_id}").status_code == 404
    assert client.get("/posts/count").json() == {"count": 1}
    assert retained.is_deleted is True
    assert retained.post_revision == 2
    assert retained.deleted_at == deleted_at
    event = json.loads(channel.basic_publish.call_args.kwargs["body"])
    assert event["event_type"] == "post.deleted.v1"
    assert event["payload"]["post_id"] == str(post_id)
    assert event["payload"]["post_revision"] == 2

    assert client.delete(f"/posts/{post_id}", headers=headers).status_code == 204
    assert retained.post_revision == 2


def test_deleted_post_replay_publishes_tombstone(
    client: TestClient, db_session
) -> None:
    post_id = uuid4()
    _seed_posts(db_session, post_id, uuid4())
    post = db_session.get(Post, post_id)
    post.is_deleted = True
    post.deleted_at = datetime.now(UTC)
    post.post_revision = 8
    db_session.commit()
    channel = MagicMock()

    with patch(
        "src.routers.admin.publisher_channel", return_value=nullcontext(channel)
    ):
        response = client.post(
            "/admin/posts/replay",
            params={"post_id": str(post_id)},
            headers={"x-admin-token": "test-admin-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"replayed": 1}
    envelope = json.loads(channel.basic_publish.call_args.kwargs["body"])
    assert envelope["event_type"] == "post.deleted.v1"
    assert envelope["payload"]["post_revision"] == 8


def test_list_posts_with_filters(client: TestClient, db_session) -> None:
    post_id = uuid4()
    other_id = uuid4()
    _seed_posts(db_session, post_id, other_id)

    # Each decoy differs in just one filtered dimension.
    for index, changes in enumerate(
        [
            {"source_id": SOURCE_TWO},
            {"language": "fr"},
            {"category": "sports", "keywords": ["technology"]},
        ]
    ):
        values = {
            "source_id": SOURCE_ONE,
            "item_guid": f"decoy-{index}",
            "url": f"https://example.com/decoy-{index}",
            "title": "Decoy",
            "source_title": "Decoy source",
            "language": "en",
            "category": "technology",
        }
        db_session.add(Post(**(values | changes)))
    db_session.commit()
    assert client.get("/posts/count").json() == {"count": 5}

    filtered = client.get(
        "/posts",
        params={
            "source_id": str(SOURCE_ONE),
            "language": "en",
            "category": "technology",
        },
    )
    assert filtered.status_code == 200
    payload = filtered.json()
    assert len(payload) == 1
    assert payload[0]["post_id"] == str(post_id)


def test_replay_posts_emits_complete_stored_snapshot(
    client: TestClient, db_session
) -> None:
    post_id = uuid4()
    now = datetime.now(UTC).replace(tzinfo=None)
    post = Post(
        post_id=post_id,
        post_revision=7,
        source_id=SOURCE_ONE,
        item_guid="guid-replay-title",
        url="https://example.com/replay-title",
        source_title="Tech Blog",
        title="Tech News",
        description="desc",
        category="technology",
        content="content",
        author="Author",
        published_at=now,
        crawled_at=now,
        parsed_at=now,
        image_url=None,
        language="en",
        keywords=["technology"],
    )
    db_session.add(post)
    db_session.commit()
    db_session.expunge_all()

    channel = MagicMock()
    with (
        patch(
            "src.routers.admin.publisher_channel",
            return_value=nullcontext(channel),
        ),
        patch("src.adapters.content_extractor.extract_article") as extract,
    ):
        response = client.post(
            "/admin/posts/replay",
            params={"limit": 1},
            headers={"x-admin-token": "test-admin-token"},
        )
    extract.assert_not_called()
    assert response.status_code == 200
    assert response.json() == {"replayed": 1}
    published = channel.basic_publish.call_args.kwargs
    assert published["routing_key"] == "post.parsed.v1"
    payload = json.loads(published["body"])["payload"]
    assert payload["post_id"] == str(post_id)
    assert payload["post_revision"] == 7
    assert payload["source_title"] == "Tech Blog"
    assert payload["title"] == "Tech News"
    assert payload["content"] == "content"
    assert payload["content_length"] == 7
    assert payload["published_at"] == now.replace(tzinfo=UTC).isoformat()
    assert payload["keywords"] == ["technology"]
    assert payload == {
        "post_id": str(post_id),
        "post_revision": 7,
        "source_id": str(SOURCE_ONE),
        "item_guid": "guid-replay-title",
        "url": "https://example.com/replay-title",
        "source_title": "Tech Blog",
        "title": "Tech News",
        "description": "desc",
        "category": "technology",
        "content": "content",
        "content_length": 7,
        "author": "Author",
        "published_at": now.replace(tzinfo=UTC).isoformat(),
        "language": "en",
        "keywords": ["technology"],
        "image_url": None,
        "parsed_at": payload["parsed_at"],
    }
    assert db_session.get(Post, post_id).post_revision == 7


@pytest.mark.parametrize(
    "method,path",
    [
        ("PATCH", "/posts/{id}"),
        ("DELETE", "/posts/{id}"),
        ("POST", "/admin/posts/replay"),
    ],
)
@pytest.mark.parametrize(
    "configured_token,request_token",
    [
        (None, "test-admin-token"),
        ("test-admin-token", None),
        ("test-admin-token", "wrong"),
    ],
    ids=["unconfigured", "missing", "incorrect"],
)
def test_post_writes_require_internal_credential(
    client: TestClient,
    db_session,
    monkeypatch,
    method,
    path,
    configured_token,
    request_token,
) -> None:
    post_id = uuid4()
    _seed_posts(db_session, post_id, uuid4())
    monkeypatch.setattr(settings, "internal_admin_token", configured_token)
    headers = {"x-admin-token": request_token} if request_token is not None else {}
    with (
        patch("src.routers.admin.publisher_channel") as replay_publisher,
        patch("src.routers.posts.publisher_channel") as post_publisher,
    ):
        response = client.request(
            method,
            path.format(id=post_id),
            json={"title": "Changed"},
            headers=headers,
        )
    assert response.status_code == 401
    replay_publisher.assert_not_called()
    post_publisher.assert_not_called()
    stored = db_session.get(Post, post_id)
    assert stored.title == "Tech News"
    assert not stored.is_deleted

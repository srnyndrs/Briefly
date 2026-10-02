import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

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


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "content-service"


def test_get_post_by_id(client: TestClient, db_session) -> None:
    post_id = uuid4()
    other_id = uuid4()
    _seed_posts(db_session, post_id, other_id)

    by_id = client.get(f"/posts/{post_id}")
    assert by_id.status_code == 200
    assert by_id.json()["post_id"] == str(post_id)


def test_list_posts_with_filters(client: TestClient, db_session) -> None:
    post_id = uuid4()
    other_id = uuid4()
    _seed_posts(db_session, post_id, other_id)

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


def test_count_posts(client: TestClient, db_session) -> None:
    _seed_posts(db_session, uuid4(), uuid4())

    response = client.get("/posts/count")

    assert response.status_code == 200
    assert response.json() == {"count": 2}


def test_get_post_not_found(client: TestClient) -> None:
    missing = client.get(f"/posts/{uuid4()}")
    assert missing.status_code == 404


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
    with patch(
        "src.routers.admin.create_replay_publisher_channel",
        return_value=channel,
    ):
        response = client.post(
            "/admin/posts/replay",
            params={"limit": 1},
        )
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
    assert payload["published_at"] == now.isoformat()
    assert payload["keywords"] == ["technology"]
    channel.connection.close.assert_called_once()

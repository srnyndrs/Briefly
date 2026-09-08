from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from src.models.post import Post


def _seed_posts(db_session, post_id: str, other_id: str):
    now = datetime.now(UTC).replace(tzinfo=None)
    db_session.add(
        Post(
            post_id=post_id,
            source_id="source-1",
            item_guid="guid-1",
            url="https://example.com/a",
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
            source_id="source-2",
            item_guid="guid-2",
            url="https://example.com/b",
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
    post_id = str(uuid4())
    other_id = str(uuid4())
    _seed_posts(db_session, post_id, other_id)

    by_id = client.get(f"/posts/{post_id}")
    assert by_id.status_code == 200
    assert by_id.json()["post_id"] == post_id


def test_list_posts_with_filters(
    client: TestClient, db_session
) -> None:
    post_id = str(uuid4())
    other_id = str(uuid4())
    _seed_posts(db_session, post_id, other_id)

    filtered = client.get(
        "/posts",
        params={
            "source_id": "source-1",
            "language": "en",
            "category": "technology",
        },
    )
    assert filtered.status_code == 200
    payload = filtered.json()
    assert len(payload) == 1
    assert payload[0]["post_id"] == post_id


def test_count_posts(client: TestClient, db_session) -> None:
    _seed_posts(db_session, str(uuid4()), str(uuid4()))

    response = client.get("/posts/count")

    assert response.status_code == 200
    assert response.json() == {"count": 2}


def test_get_post_not_found(client: TestClient) -> None:
    missing = client.get(f"/posts/{uuid4()}")
    assert missing.status_code == 404


def test_replay_posts_publishes_events(
    client: TestClient, db_session
) -> None:
    post_id = str(uuid4())
    other_id = str(uuid4())
    _seed_posts(db_session, post_id, other_id)

    with (
        patch(
            "src.routers.admin.create_replay_publisher_channel",
            return_value=MagicMock(),
        ),
        patch(
            "src.routers.admin.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        response = client.post("/admin/posts/replay")
        assert response.status_code == 200
        assert response.json() == {"replayed": 2}
        assert mock_publish.call_count == 2


def test_replay_posts_emits_stored_source_title(
    client: TestClient, db_session
) -> None:
    post_id = str(uuid4())
    now = datetime.now(UTC).replace(tzinfo=None)
    post = Post(
        post_id=post_id,
        source_id="source-1",
        item_guid="guid-replay-title",
        url="https://example.com/replay-title",
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
    post.source_title = "Tech Blog"
    db_session.add(post)
    db_session.commit()
    db_session.expunge_all()

    with (
        patch(
            "src.routers.admin.create_replay_publisher_channel",
            return_value=MagicMock(),
        ),
        patch(
            "src.routers.admin.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        response = client.post(
            "/admin/posts/replay",
            params={"limit": 1},
        )
        assert response.status_code == 200
        assert mock_publish.called
        assert (
            mock_publish.call_args.kwargs.get("source_title")
            == "Tech Blog"
        )


def test_post_routes_publish_pydantic_response_contracts(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})

    count_response = (
        paths.get("/posts/count", {})
        .get("get", {})
        .get("responses", {})
        .get("200", {})
    )
    count_schema_ref = (
        count_response.get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref", "")
    )
    assert "PostCountResponse" in count_schema_ref

    list_response = (
        paths.get("/posts", {})
        .get("get", {})
        .get("responses", {})
        .get("200", {})
    )
    list_items_ref = (
        list_response.get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("items", {})
        .get("$ref", "")
    )
    assert "PostResponse" in list_items_ref

    get_response = (
        paths.get("/posts/{post_id}", {})
        .get("get", {})
        .get("responses", {})
        .get("200", {})
    )
    get_schema_ref = (
        get_response.get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref", "")
    )
    assert "PostResponse" in get_schema_ref

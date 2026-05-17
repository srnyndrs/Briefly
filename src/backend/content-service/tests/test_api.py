from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from src.models.article import Article


def _seed_articles(db_session, article_id: str, other_id: str):
    now = datetime.now(UTC).replace(tzinfo=None)
    db_session.add(
        Article(
            id=article_id,
            feed_id="source-1",
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
        Article(
            id=other_id,
            feed_id="source-2",
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


def test_get_article_by_id(client: TestClient, db_session) -> None:
    article_id = str(uuid4())
    other_id = str(uuid4())
    _seed_articles(db_session, article_id, other_id)

    by_id = client.get(f"/articles/{article_id}")
    assert by_id.status_code == 200
    assert by_id.json()["id"] == article_id


def test_list_articles_with_filters(
    client: TestClient, db_session
) -> None:
    article_id = str(uuid4())
    other_id = str(uuid4())
    _seed_articles(db_session, article_id, other_id)

    filtered = client.get(
        "/articles",
        params={
            "source_id": "source-1",
            "language": "en",
            "category": "technology",
        },
    )
    assert filtered.status_code == 200
    payload = filtered.json()
    assert len(payload) == 1
    assert payload[0]["id"] == article_id


def test_get_article_not_found(client: TestClient) -> None:
    missing = client.get(f"/articles/{uuid4()}")
    assert missing.status_code == 404

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.schemas.schemas import ExploreResult
from src.models.feed import Feed


@patch("src.routers.feeds.discover_feeds")
def test_explore_endpoint(mock_discover, client):
    mock_discover.return_value = [
        ExploreResult(
            url="https://example.com/feed",
            title="Example",
            description="Desc",
        )
    ]
    response = client.post(
        "/feeds/explore", json={"url": "https://example.com"}
    )
    assert response.status_code == 200
    assert response.json()[0]["url"] == "https://example.com/feed"
    assert response.json()[0]["title"] == "Example"


@patch("src.routers.feeds.discover_feeds")
def test_explore_endpoint_no_results(mock_discover, client):
    mock_discover.return_value = []
    response = client.post(
        "/feeds/explore", json={"url": "https://example.com"}
    )
    assert response.status_code == 200
    assert response.json() == []


@patch("src.routers.feeds.discover_feeds")
@patch("src.routers.feeds.SqlAlchemyFeedRepository")
def test_register_feed_success(
    mock_repo_cls, mock_discover, client
):
    mock_discover.return_value = [
        ExploreResult(
            url="https://example.com/feed",
            title="Example",
            description="Desc",
            favicon="icon.ico",
        )
    ]

    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    repository = MagicMock()
    repository.get_feed_by_url.return_value = None
    repository.create_feed.return_value = Feed(
        feed_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        url="https://example.com/feed",
        title="Example",
        description="Desc",
        favicon="icon.ico",
        health_score=1.0,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=False,
        created_at=now_dt,
        updated_at=now_dt,
    )
    mock_repo_cls.return_value = repository

    response = client.post(
        "/feeds",
        json={"url": "https://example.com", "title": "My Title"},
    )
    assert response.status_code == 201
    assert response.json()["url"] == "https://example.com/feed"
    assert response.json()["title"] == "Example"


@patch("src.routers.feeds.discover_feeds")
def test_register_feed_not_found(mock_discover, client):
    mock_discover.return_value = []

    response = client.post(
        "/feeds", json={"url": "https://example.com"}
    )
    assert response.status_code == 400
    assert "No valid RSS/Atom feed found" in response.text


@patch("src.routers.feeds.SqlAlchemyFeedRepository")
def test_get_feed_success(mock_repo_cls, client):
    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    feed_id = uuid.uuid4()
    repository = MagicMock()
    repository.get_feed_by_id.return_value = Feed(
        feed_id=feed_id,
        user_id=uuid.uuid4(),
        url="https://example.com/feed",
        title="Example",
        description="Desc",
        favicon="icon.ico",
        health_score=1.0,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    mock_repo_cls.return_value = repository

    response = client.get(f"/feeds/{feed_id}")
    assert response.status_code == 200
    assert response.json()["feed_id"] == str(feed_id)


@patch("src.routers.feeds.SqlAlchemyFeedRepository")
def test_patch_feed_success(mock_repo_cls, client):
    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    feed_id = uuid.uuid4()
    existing = Feed(
        feed_id=feed_id,
        user_id=uuid.uuid4(),
        url="https://example.com/feed",
        title="Example",
        description="Desc",
        favicon="icon.ico",
        health_score=1.0,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    updated = Feed(
        feed_id=feed_id,
        user_id=existing.user_id,
        url=existing.url,
        title="Updated Title",
        description=existing.description,
        favicon=existing.favicon,
        health_score=1.0,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    repository = MagicMock()
    repository.get_feed_by_id.return_value = existing
    repository.get_feed_by_url.return_value = None
    repository.update_feed.return_value = updated
    mock_repo_cls.return_value = repository

    response = client.patch(
        f"/feeds/{feed_id}", json={"title": "Updated Title"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

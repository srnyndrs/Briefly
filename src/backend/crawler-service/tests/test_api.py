import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.models.source import Source
from src.schemas.schemas import SourceDiscoverResult


def test_discover_sources_success(client):
    with patch("src.routers.sources.discover_sources") as mock_discover:
        mock_discover.return_value = [
            SourceDiscoverResult(
                url="https://example.com/feed",
                title="Example",
                description="Desc",
                favicon="icon.ico",
            )
        ]

        response = client.post(
            "/sources/discover", json={"url": "https://example.com"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["url"] == "https://example.com/feed"


@patch(
    "src.routers.sources.SourceDiscoveryAdapter.extract_website_url",
    return_value=None,
)
@patch("src.routers.sources.discover_sources")
@patch("src.routers.sources.SqlAlchemySourceRepository")
def test_register_source_success(
    mock_repo_cls, mock_discover, mock_extract, client
):
    mock_discover.return_value = [
        SourceDiscoverResult(
            url="https://example.com/feed",
            title="Example",
            description="Desc",
            favicon="icon.ico",
        )
    ]

    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    repository = MagicMock()
    repository.get_source_by_url.return_value = None
    repository.create_source.return_value = Source(
        source_id=uuid.uuid4(),
        url="https://example.com/feed",
        title="Example",
        description="Desc",
        favicon="icon.ico",
        enrich_with_ai=False,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=False,
        created_at=now_dt,
        updated_at=now_dt,
    )
    mock_repo_cls.return_value = repository

    response = client.post(
        "/sources",
        json={"url": "https://example.com", "title": "My Title"},
    )
    assert response.status_code == 201
    assert response.json()["url"] == "https://example.com/feed"
    assert response.json()["title"] == "Example"
    assert "source_id" in response.json()
    mock_extract.assert_called_once_with("https://example.com/feed")


@patch("src.routers.sources.discover_sources")
def test_register_source_not_found(mock_discover, client):
    mock_discover.return_value = []

    response = client.post(
        "/sources", json={"url": "https://example.com"}
    )
    assert response.status_code == 400
    assert "No valid RSS/Atom feed found" in response.text


@patch("src.routers.sources.SqlAlchemySourceRepository")
def test_get_source_success(mock_repo_cls, client):
    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    source_id = uuid.uuid4()
    repository = MagicMock()
    repository.get_source_by_id.return_value = Source(
        source_id=source_id,
        url="https://example.com/feed",
        title="Example",
        description="Desc",
        favicon="icon.ico",
        enrich_with_ai=False,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    mock_repo_cls.return_value = repository

    response = client.get(f"/sources/{source_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == str(source_id)
    assert "consecutive_failures" in data
    assert "next_crawl_scheduled_at" in data
    assert "health_score" not in data


@patch("src.routers.sources.SqlAlchemySourceRepository")
def test_patch_source_success(mock_repo_cls, client):
    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    source_id = uuid.uuid4()
    existing = Source(
        source_id=source_id,
        url="https://example.com/feed",
        title="Example",
        description="Desc",
        favicon="icon.ico",
        enrich_with_ai=False,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    updated = Source(
        source_id=source_id,
        url=existing.url,
        title="Updated Title",
        description=existing.description,
        favicon=existing.favicon,
        enrich_with_ai=False,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    repository = MagicMock()
    repository.get_source_by_id.return_value = existing
    repository.get_source_by_url.return_value = None
    repository.update_source.return_value = updated
    mock_repo_cls.return_value = repository

    response = client.patch(
        f"/sources/{source_id}", json={"title": "Updated Title"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@patch("src.routers.sources.SqlAlchemySourceRepository")
def test_list_sources_returns_all(mock_repo_cls, client):
    source_id = uuid.uuid4()
    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    repository = MagicMock()
    repository.get_sources.return_value = [
        Source(
            source_id=source_id,
            url="https://example.com/feed",
            title="Example",
            description="Desc",
            favicon="icon.ico",
            enrich_with_ai=False,
            consecutive_failures=0,
            last_crawled_at=None,
            next_crawl_scheduled_at=now_dt,
            last_crawl_succeeded=True,
            created_at=now_dt,
            updated_at=now_dt,
        )
    ]
    mock_repo_cls.return_value = repository

    response = client.get("/sources")
    assert response.status_code == 200
    assert len(response.json()) == 1

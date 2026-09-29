import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from src.config.settings import settings
from src.models.source import Source
from src.schemas.sources import SourceDiscoverResponse


@pytest.fixture
def discover(monkeypatch):
    result = SourceDiscoverResponse(
        url="https://example.com/feed",
        title="Example",
        description="News",
        website_url="https://example.com/",
    )
    discover = Mock(return_value=[result])
    monkeypatch.setattr(
        "src.routers.sources.SourceDiscoveryAdapter.discover", discover
    )
    return discover


def test_source_lifecycle(client, discover, db_session):
    submitter = str(uuid.uuid4())
    response = client.post(
        "/sources",
        json={
            "url": "HTTPS://EXAMPLE.COM:443/feed#fragment",
            "title": "  My Source  ",
            "favicon": "https://example.com/original.png",
            "submitted_by_user_id": submitter,
        },
    )
    assert response.status_code == 201
    source = response.json()
    source_id = source["source_id"]
    assert source["title"] == "My Source"
    assert source["url"] == "https://example.com/feed"
    assert source["website_url"] is None
    assert source["verified"] is False
    assert source["favicon"] == "https://example.com/original.png"
    assert "submitted_by_user_id" not in source
    stored = db_session.get(Source, uuid.UUID(source_id))
    assert str(stored.submitted_by_user_id) == submitter
    discover.assert_not_called()
    assert client.get(f"/sources/{source_id}").json() == source

    updated = client.patch(
        f"/sources/{source_id}",
        json={
            "url": "https://example.com/news.xml",
            "description": None,
            "favicon": "https://example.com/icon.png",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["url"] == "https://example.com/news.xml"
    assert updated.json()["description"] is None
    assert updated.json()["favicon"] == "https://example.com/icon.png"
    assert updated.json()["title"] == source["title"]
    assert updated.json()["website_url"] == source["website_url"]
    renamed = client.patch(
        f"/sources/{source_id}",
        json={"title": "  Updated Source  ", "favicon": None},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Updated Source"
    assert renamed.json()["favicon"] is None
    assert renamed.json()["url"] == updated.json()["url"]
    assert client.get(f"/sources/{source_id}").json() == renamed.json()
    assert client.get("/sources").json() == [renamed.json()]

    assert client.delete(f"/sources/{source_id}").status_code == 204
    assert client.get(f"/sources/{source_id}").status_code == 404
    assert client.delete(f"/sources/{source_id}").status_code == 404
    assert client.patch(f"/sources/{source_id}", json={}).status_code == 404
    assert client.get("/sources").json() == []


def test_discovery_endpoint(client, discover):
    response = client.post(
        "/sources/discover",
        json={
            "url": "https://example.com/",
        },
    )
    assert response.status_code == 200
    assert response.json() == [
        result.model_dump() for result in discover.return_value
    ]
    discover.assert_called_once_with("https://example.com/")


def test_registration_does_not_fetch_or_require_discovery(client, discover):
    discover.return_value = []
    response = client.post(
        "/sources",
        json={"url": "https://feeds.example.com/rss", "title": "Example"},
    )
    assert response.status_code == 201
    assert response.json()["url"] == "https://feeds.example.com/rss"
    discover.assert_not_called()


def test_registration_rejects_duplicate_url(client, source_factory):
    source_factory(url="https://example.com/feed")
    response = client.post(
        "/sources",
        json={
            "url": "HTTPS://EXAMPLE.COM:443/feed#fragment",
            "title": "Example",
        },
    )
    assert response.status_code == 409
    assert len(client.get("/sources").json()) == 1


def test_registration_allows_other_feeds_on_same_domain(client, source_factory):
    source_factory(
        title="Other Publisher",
        website_url="https://other.example.com/",
    )
    response = client.post(
        "/sources",
        json={"url": "https://example.com/other.xml", "title": "Example"},
    )
    assert response.status_code == 201
    assert len(client.get("/sources").json()) == 2


@pytest.mark.parametrize(
    "method, path, payload",
    [
        ("post", "/sources", {"url": "not-a-url", "title": "Example"}),
        (
            "post",
            "/sources",
            {"url": "https://user:pass@example.com/feed", "title": "Example"},
        ),
        (
            "post",
            "/sources",
            {"url": "https://example.com/", "title": " "},
        ),
        (
            "post",
            "/sources",
            {
                "url": "https://example.com/",
                "title": "Example",
                "verified": True,
            },
        ),
    ],
    ids=[
        "invalid-url",
        "credentialed-url",
        "blank-title",
        "verification",
    ],
)
def test_api_rejects_invalid_or_server_owned_fields(
    client, source_factory, method, path, payload
):
    source = source_factory()
    response = client.request(
        method, path.format(source_id=source.source_id), json=payload
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "method, payload",
    [
        ("post", {}),
        ("post", {"title": None}),
        ("post", {"title": "x" * 256}),
        ("post", {"title": "Example", "favicon": "http-invalid"}),
        ("patch", {"title": " "}),
        ("patch", {"title": None}),
        ("patch", {"title": "x" * 256}),
        ("patch", {"url": None}),
        ("patch", {"favicon": "ftp://example.com/icon.png"}),
        ("patch", {"favicon": "https://example.com/" + "x" * 2048}),
    ],
)
def test_source_metadata_validation(
    client, discover, source_factory, method, payload
):
    source = source_factory()
    if method == "post":
        path = "/sources"
        payload = {"url": "https://example.com/"} | payload
    else:
        path = f"/sources/{source.source_id}"
    response = client.request(method, path, json=payload)
    assert response.status_code == 422
    assert (
        client.get(f"/sources/{source.source_id}").json()["title"]
        == source.title
    )
    assert len(client.get("/sources").json()) == 1
    discover.assert_not_called()


def test_source_list_filters_and_orders(client, source_factory):
    now = datetime.now(timezone.utc)
    verified = source_factory(title="Zeta", verified=True)
    unverified = source_factory(title="Alpha")
    future = source_factory(next_crawl_scheduled_at=now + timedelta(days=1))
    suspended = source_factory(consecutive_failures=settings.max_retries)

    def ids(response):
        assert response.status_code == 200
        return [row["source_id"] for row in response.json()]

    assert ids(client.get("/sources"))[0] == str(verified.source_id)
    assert ids(client.get("/sources?verified_only=true")) == [
        str(verified.source_id)
    ]
    assert set(ids(client.get("/sources?active_only=true"))) == {
        str(verified.source_id),
        str(unverified.source_id),
    }
    assert ids(client.get("/sources?active_only=true&verified_only=true")) == [
        str(verified.source_id)
    ]
    assert str(future.source_id) in ids(client.get("/sources"))
    assert str(suspended.source_id) in ids(client.get("/sources"))


def test_patch_rejects_existing_feed_url(client, source_factory):
    first, second = source_factory(), source_factory()
    response = client.patch(
        f"/sources/{second.source_id}", json={"url": first.url}
    )
    assert response.status_code == 409
    assert (
        client.get(f"/sources/{second.source_id}").json()["url"] == second.url
    )

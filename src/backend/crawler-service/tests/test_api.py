import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from src.config.settings import settings
from src.models.source import Source
from src.schemas.sources import SourceDiscoverResult


@pytest.fixture
def discover(monkeypatch):
    result = SourceDiscoverResult(
        url="https://example.com/feed",
        title="Example",
        description="News",
        website_url="https://example.com/",
        registrable_domain="example.com",
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
            "url": "https://example.com/",
            "title": "My Source",
            "submitted_by_user_id": submitter,
        },
    )
    assert response.status_code == 201
    source = response.json()
    source_id = source["source_id"]
    assert source["title"] == "My Source"
    assert source["url"] == "https://example.com/feed"
    assert source["verified"] is False
    assert "submitted_by_user_id" not in source
    assert "registrable_domain" not in source
    stored = db_session.get(Source, uuid.UUID(source_id))
    assert str(stored.submitted_by_user_id) == submitter
    assert stored.registrable_domain == "example.com"
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
    assert client.get("/sources").json() == [updated.json()]

    assert client.delete(f"/sources/{source_id}").status_code == 204
    assert client.get(f"/sources/{source_id}").status_code == 404
    assert client.delete(f"/sources/{source_id}").status_code == 404
    assert (
        client.patch(f"/sources/{source_id}", json={}).status_code
        == 404
    )
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


@pytest.mark.parametrize(
    "problem, status",
    [
        ("no-feed", 400),
        ("multiple-feeds", 422),
        ("missing-title", 422),
    ],
)
def test_registration_requires_one_named_feed(
    client, discover, problem, status
):
    if problem == "no-feed":
        discover.return_value = []
    elif problem == "multiple-feeds":
        discover.return_value *= 2
    else:
        discover.return_value[0].title = None
    response = client.post(
        "/sources", json={"url": "https://example.com/"}
    )
    assert response.status_code == status
    assert client.get("/sources").json() == []


@pytest.mark.parametrize(
    "existing",
    [
        {
            "url": "HTTPS://EXAMPLE.COM:443/feed#fragment",
            "title": "Other",
        },
        {"website_url": "https://www.example.com/", "title": "Other"},
        {"title": "  EXAMPLE  "},
    ],
    ids=["feed-url", "website-host", "publisher-title"],
)
def test_registration_rejects_duplicate_source(
    client, discover, source_factory, existing
):
    source_factory(**existing)
    response = client.post(
        "/sources", json={"url": "https://example.com/"}
    )
    assert response.status_code == 409
    assert len(client.get("/sources").json()) == 1


def test_registration_allows_distinct_publishers_on_one_domain(
    client, discover, source_factory
):
    source_factory(
        title="Other Publisher",
        website_url="https://other.example.com/",
    )
    response = client.post(
        "/sources", json={"url": "https://example.com/"}
    )
    assert response.status_code == 201
    assert len(client.get("/sources").json()) == 2


@pytest.mark.parametrize(
    "method, path, payload",
    [
        ("post", "/sources", {"url": "not-a-url"}),
        (
            "post",
            "/sources",
            {"url": "https://example.com/", "title": " "},
        ),
        (
            "post",
            "/sources",
            {"url": "https://example.com/", "verified": True},
        ),
        (
            "post",
            "/sources",
            {
                "url": "https://example.com/",
                "registrable_domain": "other.org",
            },
        ),
        ("patch", "/sources/{source_id}", {"title": "Changed"}),
    ],
    ids=[
        "invalid-url",
        "blank-title",
        "verification",
        "domain",
        "immutable-title",
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


def test_source_list_filters_and_orders(client, source_factory):
    now = datetime.now(timezone.utc)
    verified = source_factory(title="Zeta", verified=True)
    unverified = source_factory(title="Alpha")
    future = source_factory(
        next_crawl_scheduled_at=now + timedelta(days=1)
    )
    suspended = source_factory(
        consecutive_failures=settings.max_retries
    )

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
    assert ids(
        client.get("/sources?active_only=true&verified_only=true")
    ) == [str(verified.source_id)]
    assert str(future.source_id) in ids(client.get("/sources"))
    assert str(suspended.source_id) in ids(client.get("/sources"))


def test_patch_rejects_existing_feed_url(client, source_factory):
    first, second = source_factory(), source_factory()
    response = client.patch(
        f"/sources/{second.source_id}", json={"url": first.url}
    )
    assert response.status_code == 409
    assert (
        client.get(f"/sources/{second.source_id}").json()["url"]
        == second.url
    )

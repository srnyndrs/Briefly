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
        site_url="https://example.com/",
        site_name="Example News",
        language="hu-HU",
    )
    discover = Mock(return_value=[result])
    monkeypatch.setattr(
        "src.routers.sources.SourceDiscoveryAdapter.discover", discover
    )

    return discover


def test_source_lifecycle(client, discover, db_session):
    discover.side_effect = AssertionError("Registration must not discover feeds")
    submitter = str(uuid.uuid4())
    response = client.post(
        "/sources",
        json={
            "url": "HTTPS://EXAMPLE.COM:443/feed#fragment",
            "title": "  My Source  ",
            "description": "Original description",
            "favicon": "https://example.com/original.png",
            "site_url": "https://example.com/",
            "site_name": "Example News",
            "language": "hu-HU",
            "submitted_by_user_id": submitter,
        },
    )
    assert response.status_code == 201
    source = response.json()
    source_id = source["source_id"]
    assert source["title"] == "My Source"
    assert source["url"] == "https://example.com/feed"
    assert source["site_url"] == "https://example.com/"
    assert source["site_name"] == "Example News"
    assert source["language"] == "hu"
    assert source["verified"] is False
    assert source["favicon"] == "https://example.com/original.png"
    assert "submitted_by_user_id" not in source
    stored = db_session.get(Source, uuid.UUID(source_id))
    assert str(stored.submitted_by_user_id) == submitter
    discover.assert_not_called()
    read = client.get(f"/sources/{source_id}")
    assert read.status_code == 200
    assert read.json()["source_id"] == source_id
    assert read.json()["description"] == "Original description"

    updated = client.patch(
        f"/sources/{source_id}",
        json={
            "url": "https://example.com/news.xml",
            "description": None,
            "favicon": "https://example.com/icon.png",
            "site_url": "https://news.example.com/",
            "site_name": "Example Media",
            "language": "yue-Hant",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["url"] == "https://example.com/news.xml"
    assert updated.json()["description"] is None
    assert updated.json()["favicon"] == "https://example.com/icon.png"
    assert updated.json()["site_url"] == "https://news.example.com/"
    assert updated.json()["site_name"] == "Example Media"
    assert updated.json()["language"] == "yue"
    assert updated.json()["title"] == source["title"]
    renamed = client.patch(
        f"/sources/{source_id}",
        json={"title": "  Updated Source  ", "favicon": None},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Updated Source"
    assert renamed.json()["favicon"] is None
    assert renamed.json()["url"] == updated.json()["url"]
    read = client.get(f"/sources/{source_id}").json()
    assert read["title"] == "Updated Source"
    assert read["favicon"] is None
    assert read["language"] == "yue"

    verified = client.patch(f"/sources/{source_id}", json={"verified": True})
    assert verified.status_code == 200
    assert verified.json()["verified"] is True
    assert (
        client.patch(f"/sources/{source_id}", json={"verified": None}).status_code
        == 422
    )

    assert [row["source_id"] for row in client.get("/sources").json()] == [
        source_id
    ]

    assert client.delete(f"/sources/{source_id}").status_code == 204
    assert client.get(f"/sources/{source_id}").status_code == 404
    assert client.get("/sources").json() == []


def test_discovery_endpoint(client, discover):
    response = client.post(
        "/sources/discover",
        json={
            "url": "24.hu",
        },
    )
    assert response.status_code == 200
    assert response.json() == [
        result.model_dump() for result in discover.return_value
    ]
    discover.assert_called_once_with("24.hu")


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
        url="https://example.com/main.xml", site_url="https://example.com/"
    )
    response = client.post(
        "/sources",
        json={
            "url": "https://example.com/other.xml",
            "title": "Other Feed",
            "site_url": "https://example.com/",
        },
    )
    assert response.status_code == 201
    assert {row["url"] for row in client.get("/sources").json()} == {
        "https://example.com/main.xml",
        "https://example.com/other.xml",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"url": "https://user:pass@example.com/feed", "title": "Example"},
        {"url": "https://example.com/feed", "title": " "},
        {
            "url": "https://example.com/feed",
            "title": "Example",
            "verified": True,
        },
    ],
    ids=["credentialed-url", "blank-title", "verification"],
)
def test_api_rejects_invalid_or_server_owned_fields(client, db_session, payload):
    assert client.post("/sources", json=payload).status_code == 422
    assert db_session.query(Source).count() == 0


def test_source_metadata_validation(client, source_factory, db_session):
    source = source_factory(title="Original", language="hu")

    response = client.patch(
        f"/sources/{source.source_id}",
        json={"title": "Should not persist", "language": "und"},
    )

    assert response.status_code == 422
    db_session.refresh(source)

    assert source.title == "Original"
    assert source.language == "hu"


def test_source_list_filters_and_orders(client, source_factory):
    now = datetime.now(timezone.utc)
    first = source_factory(
        verified=True,
        title="alpha",
        source_id=uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"),
    )
    second = source_factory(
        verified=True,
        title="Alpha",
        source_id=uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2"),
    )
    last = source_factory(title="Zeta", verified=True)
    unverified = source_factory(title="Alpha")
    future = source_factory(
        title="Future", next_crawl_scheduled_at=now + timedelta(days=1)
    )
    suspended = source_factory(
        title="Suspended", consecutive_failures=settings.max_retries
    )

    def ids(response):
        assert response.status_code == 200
        return [row["source_id"] for row in response.json()]

    verified_ids = [str(source.source_id) for source in (first, second, last)]

    assert ids(client.get("/sources")) == verified_ids + [
        str(source.source_id) for source in (unverified, future, suspended)
    ]
    assert ids(client.get("/sources?verified_only=true")) == verified_ids
    assert set(ids(client.get("/sources?active_only=true"))) == {
        *verified_ids,
        str(unverified.source_id),
    }
    assert set(
        ids(client.get("/sources?active_only=true&verified_only=true"))
    ) == set(verified_ids)


def test_patch_rejects_existing_feed_url(client, source_factory):
    first, second = source_factory(), source_factory()

    response = client.patch(f"/sources/{second.source_id}", json={"url": first.url})

    assert response.status_code == 409
    assert client.get(f"/sources/{second.source_id}").json()["url"] == second.url

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.models.source import Source
from src.schemas.sources import SourceDiscoverResult


def _http_response(url: str, body: bytes, *, headers=None, status=200):
    response = MagicMock()
    response.url = url
    response.status_code = status
    response.headers = headers or {}
    response.content = body
    response.iter_content.return_value = [body]
    return response


def test_discover_sources_success(client):
    with patch("src.routers.sources.discover_sources") as mock_discover:
        mock_discover.return_value = [
            SourceDiscoverResult(
                url="https://example.com/feed",
                title="Example",
                description="Desc",
                favicon="icon.ico",
                website_url="https://example.com/",
                registrable_domain="example.com",
            )
        ]

        response = client.post(
            "/sources/discover", json={"url": "https://example.com"}
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["url"] == "https://example.com/feed"
        assert response.json()[0]["title"] == "Example"
        assert response.json()[0]["description"] == "Desc"
        assert response.json()[0]["favicon"] == "icon.ico"
        assert (
            response.json()[0]["website_url"] == "https://example.com/"
        )
        assert response.json()[0]["registrable_domain"] == "example.com"


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_accepts_direct_feed_url(_mock_public):
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    body = (
        b"<?xml version='1.0'?><rss version='2.0'><channel>"
        b"<title>Example</title><description>News</description>"
        b"<link>https://www.example.com/</link>"
        b"</channel></rss>"
    )
    response = _http_response(
        "https://example.com/feed.xml",
        body,
        headers={"Content-Type": "application/rss+xml; charset=utf-8"},
    )

    with patch(
        "src.adapters.source_discovery.requests.get",
        return_value=response,
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/feed.xml"
        )

    assert len(result) == 1
    assert result[0].url == "https://example.com/feed.xml"
    assert result[0].content_type == "application/rss+xml"
    assert result[0].title == "Example"
    assert result[0].website_url == "https://www.example.com/"
    assert result[0].registrable_domain == "example.com"


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_does_not_guess_unverified_feed_paths(
    _mock_public,
):
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    body = b"<html><head><title>Example</title></head></html>"
    response = _http_response("https://example.com/", body)

    with (
        patch(
            "src.adapters.source_discovery.requests.get",
            return_value=response,
        ),
        patch(
            "src.adapters.source_discovery.requests.head"
        ) as mock_head,
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/"
        )

    assert result == []
    mock_head.assert_not_called()


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_validates_advertised_feed_and_prefers_feed_title(
    _mock_public,
):
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    page = _http_response(
        "https://example.com/",
        b"<html><head>"
        b"<meta property='og:site_name' content='Example News'>"
        b"<link rel='alternate' type='application/rss+xml' "
        b"title='Latest stories' href='/feed.xml'>"
        b"</head></html>",
    )
    feed = _http_response(
        "https://example.com/feed.xml",
        b"<rss version='2.0'><channel><title>Channel Title</title>"
        b"<description>Feed description</description></channel></rss>",
        headers={"Content-Type": "text/html"},
    )

    with patch(
        "src.adapters.source_discovery.requests.get",
        side_effect=[page, feed],
    ) as mock_get:
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/"
        )

    assert len(result) == 1
    assert result[0].url == "https://example.com/feed.xml"
    assert result[0].title == "Channel Title"
    assert result[0].description == "Feed description"
    assert result[0].website_url == "https://example.com/"
    assert mock_get.call_count == 2


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_omits_advertised_non_feed(_mock_public):
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    page = _http_response(
        "https://example.com/",
        b"<link rel='alternate' type='application/atom+xml' href='/fake'>",
    )
    fake_feed = _http_response(
        "https://example.com/fake", b"<html>no</html>"
    )
    with patch(
        "src.adapters.source_discovery.requests.get",
        side_effect=[page, fake_feed],
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/"
        )
    assert result == []


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_accepts_empty_atom_feed(_mock_public):
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    response = _http_response(
        "https://example.com/atom.xml",
        b"<feed xmlns='http://www.w3.org/2005/Atom'>"
        b"<title>Empty atom</title><link href='https://example.com/'/>"
        b"</feed>",
    )
    with patch(
        "src.adapters.source_discovery.requests.get",
        return_value=response,
    ):
        result = SourceDiscoveryAdapter().discover(response.url)
    assert len(result) == 1
    assert result[0].title == "Empty atom"


def test_discover_sources_rejects_non_public_url_before_request():
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    with patch(
        "src.adapters.source_discovery.requests.get"
    ) as mock_get:
        result = SourceDiscoveryAdapter().discover(
            "http://127.0.0.1/feed"
        )
    assert result == []
    mock_get.assert_not_called()


def test_public_destination_rejects_private_dns_results():
    import socket

    from src.adapters.source_discovery import _assert_public_destination

    private_result = (
        socket.AddressFamily.AF_INET,
        socket.SocketKind.SOCK_STREAM,
        6,
        "",
        ("10.0.0.8", 443),
    )
    with patch(
        "src.adapters.source_discovery.socket.getaddrinfo",
        return_value=[private_result],
    ):
        try:
            _assert_public_destination("https://example.com/feed")
        except ValueError as exc:
            assert "Non-public" in str(exc)
        else:
            raise AssertionError("Private DNS result was accepted")


def test_normalize_feed_url_keeps_path_query_and_removes_defaults():
    from src.adapters.source_discovery import normalize_feed_url

    assert (
        normalize_feed_url("HTTPS://Example.COM:443/feed/?a=1#top")
        == "https://example.com/feed/?a=1"
    )


def test_registrable_domain_uses_packaged_public_suffix_list():
    from src.adapters.source_discovery import registrable_domain

    assert registrable_domain("https://www.origo.hu/feed") == "origo.hu"
    assert (
        registrable_domain("https://borsonline.origo.hu/feed")
        == "origo.hu"
    )


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_follows_redirect_and_uses_final_url(
    _mock_public,
):
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    redirect = _http_response(
        "https://example.com/old",
        b"",
        headers={"Location": "/feed"},
        status=302,
    )
    feed = _http_response(
        "https://example.com/feed",
        b"<rss version='2.0'><channel><title>Final</title></channel></rss>",
    )
    with patch(
        "src.adapters.source_discovery.requests.get",
        side_effect=[redirect, feed],
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/old"
        )
    assert result[0].url == "https://example.com/feed"


def test_discover_sources_checks_redirect_destination_before_request():
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    redirect = _http_response(
        "https://example.com/old",
        b"",
        headers={"Location": "http://127.0.0.1/private"},
        status=302,
    )
    with (
        patch(
            "src.adapters.source_discovery._assert_public_destination",
            side_effect=[None, ValueError("Non-public destination")],
        ) as check_public,
        patch(
            "src.adapters.source_discovery.requests.get",
            return_value=redirect,
        ) as mock_get,
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/old"
        )
    assert result == []
    assert check_public.call_count == 2
    mock_get.assert_called_once()


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_rejects_response_larger_than_limit(
    _mock_public,
):
    from src.adapters.source_discovery import SourceDiscoveryAdapter

    response = _http_response("https://example.com/feed", b"123456")
    with (
        patch(
            "src.adapters.source_discovery.requests.get",
            return_value=response,
        ),
        patch(
            "src.adapters.source_discovery.settings.source_validation_max_bytes",
            5,
        ),
    ):
        result = SourceDiscoveryAdapter().discover(response.url)
    assert result == []


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_handles_timeout(_mock_public):
    import requests

    from src.adapters.source_discovery import SourceDiscoveryAdapter

    with patch(
        "src.adapters.source_discovery.requests.get",
        side_effect=requests.Timeout,
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/feed"
        )
    assert result == []


@patch("src.routers.sources.discover_sources")
@patch("src.routers.sources.SourceRepository")
def test_register_source_success(mock_repo_cls, mock_discover, client):
    mock_discover.return_value = [
        SourceDiscoverResult(
            url="https://example.com/feed",
            title="Example",
            description="Desc",
            favicon="icon.ico",
            website_url="https://www.example.com/",
            registrable_domain="example.com",
        )
    ]

    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    repository = MagicMock()
    repository.get_source_by_url.return_value = None
    repository.create_source.return_value = Source(
        source_id=uuid.uuid4(),
        url="https://example.com/feed",
        title="My Title",
        description="Desc",
        favicon="icon.ico",
        verified=False,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=False,
        created_at=now_dt,
        updated_at=now_dt,
    )
    mock_repo_cls.return_value = repository

    submitted_by_user_id = uuid.uuid4()
    response = client.post(
        "/sources",
        json={
            "url": "https://example.com",
            "title": "My Title",
            "submitted_by_user_id": str(submitted_by_user_id),
        },
    )
    assert response.status_code == 201
    assert response.json()["url"] == "https://example.com/feed"
    assert response.json()["title"] == "My Title"
    assert "source_id" in response.json()
    mock_discover.assert_called_once_with("https://example.com/")
    repository.create_source.assert_called_once_with(
        url="https://example.com/feed",
        title="My Title",
        description="Desc",
        favicon="icon.ico",
        website_url="https://www.example.com/",
        registrable_domain="example.com",
        verified=False,
        submitted_by_user_id=submitted_by_user_id,
    )


@patch("src.routers.sources.discover_sources")
def test_register_source_rejects_multiple_valid_feeds(
    mock_discover, client
):
    mock_discover.return_value = [
        SourceDiscoverResult(
            url="https://example.com/one.xml",
            title="Example One",
            registrable_domain="example.com",
        ),
        SourceDiscoverResult(
            url="https://example.com/two.xml",
            title="Example Two",
            registrable_domain="example.com",
        ),
    ]
    response = client.post(
        "/sources", json={"url": "https://example.com"}
    )
    assert response.status_code == 422
    assert "direct feed URL" in response.json()["detail"]


@patch("src.routers.sources.discover_sources")
@patch("src.routers.sources.SourceRepository")
def test_register_source_rejects_same_publisher_title(
    mock_repo_cls, mock_discover, client
):
    mock_discover.return_value = [
        SourceDiscoverResult(
            url="https://api.origo.hu/rss",
            title="ORIGO",
            website_url="https://api.origo.hu/",
            registrable_domain="origo.hu",
        )
    ]
    repository = MagicMock()
    repository.get_source_by_url.return_value = None
    repository.get_sources_by_registrable_domain.return_value = [
        Source(
            source_id=uuid.uuid4(),
            url="https://www.origo.hu/rss",
            title="Origo",
            website_url="https://www.origo.hu/",
            registrable_domain="origo.hu",
        )
    ]
    mock_repo_cls.return_value = repository
    response = client.post(
        "/sources", json={"url": "https://api.origo.hu/rss"}
    )
    assert response.status_code == 409
    repository.create_source.assert_not_called()


@patch("src.routers.sources.discover_sources")
@patch("src.routers.sources.SourceRepository")
def test_register_source_rejects_normalized_exact_url_duplicate(
    mock_repo_cls, mock_discover, client
):
    mock_discover.return_value = [
        SourceDiscoverResult(
            url="HTTPS://EXAMPLE.COM:443/feed#fragment",
            title="Example",
            registrable_domain="example.com",
        )
    ]
    repository = MagicMock()
    repository.get_source_by_url.return_value = None
    repository.get_sources_by_registrable_domain.return_value = [
        Source(
            source_id=uuid.uuid4(),
            url="https://example.com/feed",
            title="Existing Example",
            registrable_domain="example.com",
        )
    ]
    mock_repo_cls.return_value = repository
    response = client.post(
        "/sources", json={"url": "https://example.com/feed"}
    )
    assert response.status_code == 409
    repository.create_source.assert_not_called()


@patch("src.routers.sources.discover_sources")
@patch("src.routers.sources.SourceRepository")
def test_register_source_allows_distinct_publisher_same_domain(
    mock_repo_cls, mock_discover, client
):
    mock_discover.return_value = [
        SourceDiscoverResult(
            url="https://borsonline.origo.hu/rss",
            title="Bors",
            website_url="https://borsonline.origo.hu/",
            registrable_domain="origo.hu",
        )
    ]
    repository = MagicMock()
    repository.get_source_by_url.return_value = None
    repository.get_sources_by_registrable_domain.return_value = [
        Source(
            source_id=uuid.uuid4(),
            url="https://www.origo.hu/rss",
            title="ORIGO",
            website_url="https://www.origo.hu/",
            registrable_domain="origo.hu",
        )
    ]
    repository.create_source.return_value = Source(
        source_id=uuid.uuid4(),
        url="https://borsonline.origo.hu/rss",
        title="Bors",
        website_url="https://borsonline.origo.hu/",
        registrable_domain="origo.hu",
        verified=False,
        last_crawl_succeeded=False,
        consecutive_failures=0,
        next_crawl_scheduled_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_repo_cls.return_value = repository
    response = client.post(
        "/sources", json={"url": "https://borsonline.origo.hu/rss"}
    )
    assert response.status_code == 201
    assert (
        repository.create_source.call_args.kwargs["registrable_domain"]
        == "origo.hu"
    )


def test_source_create_rejects_client_policy_fields(client):
    response = client.post(
        "/sources",
        json={"url": "https://example.com/feed", "verified": True},
    )
    assert response.status_code == 422


@patch("src.routers.sources.discover_sources")
def test_register_source_not_found(mock_discover, client):
    mock_discover.return_value = []

    response = client.post(
        "/sources", json={"url": "https://example.com"}
    )
    assert response.status_code == 400
    assert "No valid RSS/Atom feed found" in response.text


@patch("src.routers.sources.discover_sources")
def test_register_source_rejects_missing_title(mock_discover, client):
    mock_discover.return_value = [
        SourceDiscoverResult(
            url="https://example.com/feed",
            title="  ",
        )
    ]

    response = client.post(
        "/sources", json={"url": "https://example.com"}
    )

    assert response.status_code == 422


@patch("src.routers.sources.SourceRepository")
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
        verified=False,
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


@patch("src.routers.sources.SourceRepository")
def test_patch_source_rejects_title_change(mock_repo_cls, client):
    now_dt = datetime(2026, 3, 11, tzinfo=timezone.utc)
    source_id = uuid.uuid4()
    existing = Source(
        source_id=source_id,
        url="https://example.com/feed",
        title="Example",
        description="Desc",
        favicon="icon.ico",
        verified=False,
        consecutive_failures=0,
        last_crawled_at=None,
        next_crawl_scheduled_at=now_dt,
        last_crawl_succeeded=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    repository = MagicMock()
    repository.get_source_by_id.return_value = existing
    mock_repo_cls.return_value = repository

    response = client.patch(
        f"/sources/{source_id}", json={"title": "Updated Title"}
    )
    assert response.status_code == 422
    repository.update_source.assert_not_called()


@patch("src.routers.sources.SourceRepository")
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
            verified=False,
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


@patch("src.routers.sources.SourceRepository")
def test_list_sources_supports_verified_only(mock_repo_cls, client):
    repository = MagicMock()
    repository.get_sources.return_value = []
    mock_repo_cls.return_value = repository

    response = client.get("/sources?verified_only=true")

    assert response.status_code == 200
    repository.get_sources.assert_called_once_with(verified_only=True)

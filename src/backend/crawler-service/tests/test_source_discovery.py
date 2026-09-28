import socket
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.adapters.source_discovery import (
    SourceDiscoveryAdapter,
    _assert_public_destination,
    _bounded_get,
    _PinnedAddressAdapter,
    normalize_feed_url,
    registrable_domain,
)


def _http_response(url: str, body: bytes, *, headers=None, status=200):
    response = MagicMock()
    response.url = url
    response.status_code = status
    response.headers = headers or {}
    response.content = body
    response.raw.read1.side_effect = [body, b""]
    return response


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_accepts_direct_feed_url(_mock_public):
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
        "src.adapters.source_discovery.requests.Session.get",
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
    body = b"<html><head><title>Example</title></head></html>"
    response = _http_response("https://example.com/", body)

    with (
        patch(
            "src.adapters.source_discovery.requests.Session.get",
            return_value=response,
        ),
        patch("requests.head") as mock_head,
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
        "src.adapters.source_discovery.requests.Session.get",
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
    page = _http_response(
        "https://example.com/",
        b"<link rel='alternate' type='application/atom+xml' href='/fake'>",
    )
    fake_feed = _http_response(
        "https://example.com/fake", b"<html>no</html>"
    )
    with patch(
        "src.adapters.source_discovery.requests.Session.get",
        side_effect=[page, fake_feed],
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/"
        )
    assert result == []


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_accepts_empty_atom_feed(_mock_public):
    response = _http_response(
        "https://example.com/atom.xml",
        b"<feed xmlns='http://www.w3.org/2005/Atom'>"
        b"<title>Empty atom</title><link href='https://example.com/'/>"
        b"</feed>",
    )
    with patch(
        "src.adapters.source_discovery.requests.Session.get",
        return_value=response,
    ):
        result = SourceDiscoveryAdapter().discover(response.url)
    assert len(result) == 1
    assert result[0].title == "Empty atom"


def test_discover_sources_rejects_non_public_url_before_request():
    with patch(
        "src.adapters.source_discovery.requests.Session.get"
    ) as mock_get:
        result = SourceDiscoveryAdapter().discover(
            "http://127.0.0.1/feed"
        )
    assert result == []
    mock_get.assert_not_called()


def test_public_destination_rejects_private_dns_results():
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
        with pytest.raises(ValueError, match="Non-public"):
            _assert_public_destination("https://example.com/feed")


def test_source_validation_uses_the_vetted_address():
    public_result = (
        socket.AF_INET,
        socket.SOCK_STREAM,
        6,
        "",
        ("93.184.215.14", 443),
    )
    response = _http_response(
        "https://example.com/feed",
        b"<rss version='2.0'><channel/></rss>",
    )
    seen_addresses = []

    def fake_get(session, url, **kwargs):
        seen_addresses.append(session.adapters["https://"]._address)
        assert not session.trust_env
        assert kwargs["headers"]["Host"] == "example.com"
        return response

    with (
        patch(
            "src.adapters.source_discovery.socket.getaddrinfo",
            return_value=[public_result],
        ) as resolve,
        patch(
            "src.adapters.source_discovery.requests.Session.get",
            autospec=True,
            side_effect=fake_get,
        ),
    ):
        _bounded_get(response.url)

    assert seen_addresses == ["93.184.215.14"]
    resolve.assert_called_once()


def test_pinned_adapter_preserves_https_hostname():
    adapter = _PinnedAddressAdapter("93.184.215.14", "example.com")
    request = requests.Request(
        "GET", "https://example.com/feed"
    ).prepare()
    with patch.object(
        adapter.poolmanager, "connection_from_host"
    ) as connection:
        adapter.get_connection_with_tls_context(request, True)

    kwargs = connection.call_args.kwargs
    assert kwargs["host"] == "93.184.215.14"
    assert kwargs["pool_kwargs"]["assert_hostname"] == "example.com"
    assert kwargs["pool_kwargs"]["server_hostname"] == "example.com"


def test_source_validation_deadline_stops_a_trickling_response():
    response = _http_response("https://example.com/feed", b"")
    response.raw.read1.side_effect = [b"first", b"second"]
    with (
        patch(
            "src.adapters.source_discovery._assert_public_destination",
            return_value="93.184.215.14",
        ),
        patch(
            "src.adapters.source_discovery.requests.Session.get",
            return_value=response,
        ),
        patch(
            "src.adapters.source_discovery.settings.source_validation_timeout_seconds",
            1,
        ),
        patch(
            "src.adapters.source_discovery.time.monotonic",
            side_effect=[0, 0, 0.4, 1.1],
        ),
    ):
        with pytest.raises(requests.Timeout):
            _bounded_get(response.url)
    response.close.assert_called_once()


def test_normalize_feed_url_keeps_path_query_and_removes_defaults():
    assert (
        normalize_feed_url("HTTPS://Example.COM:443/feed/?a=1#top")
        == "https://example.com/feed/?a=1"
    )


def test_registrable_domain_uses_packaged_public_suffix_list():
    assert (
        registrable_domain("https://www.example.co.uk/feed")
        == "example.co.uk"
    )
    assert (
        registrable_domain("https://news.example.co.uk/feed")
        == "example.co.uk"
    )


@patch("src.adapters.source_discovery._assert_public_destination")
def test_discover_sources_follows_redirect_and_uses_final_url(
    _mock_public,
):
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
        "src.adapters.source_discovery.requests.Session.get",
        side_effect=[redirect, feed],
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/old"
        )
    assert result[0].url == "https://example.com/feed"


def test_discover_sources_checks_redirect_destination_before_request():
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
            "src.adapters.source_discovery.requests.Session.get",
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
    response = _http_response("https://example.com/feed", b"123456")
    with (
        patch(
            "src.adapters.source_discovery.requests.Session.get",
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
    with patch(
        "src.adapters.source_discovery.requests.Session.get",
        side_effect=requests.Timeout,
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://example.com/feed"
        )
    assert result == []

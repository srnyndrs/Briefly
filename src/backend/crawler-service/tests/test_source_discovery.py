from unittest.mock import MagicMock, patch

import requests

from src.adapters.source_discovery import (
    SourceDiscoveryAdapter,
    normalize_feed_url,
)


def _http_response(url: str, body: bytes, *, headers=None, status=200):
    response = MagicMock()
    response.url = url
    response.status_code = status
    response.headers = headers or {}
    response.content = body
    response.iter_content.return_value = iter([body])
    return response


def test_discover_sources_accepts_direct_feed_url():
    body = (
        b"<?xml version='1.0'?><rss version='2.0'><channel>"
        b"<title>Example</title><description>News</description>"
        b"<link>https://www.example.com/</link>"
        b"</channel></rss>"
    )
    response = _http_response(
        "https://feeds.example.net/feed.xml",
        body,
        headers={"Content-Type": "application/rss+xml; charset=utf-8"},
    )

    with patch(
        "src.adapters.source_discovery.requests.Session.get",
        return_value=response,
    ):
        result = SourceDiscoveryAdapter().discover(
            "https://feeds.example.net/feed.xml"
        )

    assert len(result) == 1
    assert result[0].url == "https://feeds.example.net/feed.xml"
    assert result[0].content_type == "application/rss+xml"
    assert result[0].title == "Example"
    assert result[0].website_url == "https://www.example.com/"


def test_discover_sources_does_not_guess_unverified_feed_paths():
    body = b"<html><head><title>Example</title></head></html>"
    response = _http_response("https://example.com/", body)

    with (
        patch(
            "src.adapters.source_discovery.requests.Session.get",
            return_value=response,
        ),
        patch("requests.head") as mock_head,
    ):
        result = SourceDiscoveryAdapter().discover("https://example.com/")

    assert result == []
    mock_head.assert_not_called()


def test_discover_sources_validates_advertised_feed_and_prefers_feed_title():
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
        result = SourceDiscoveryAdapter().discover("https://example.com/")

    assert len(result) == 1
    assert result[0].url == "https://example.com/feed.xml"
    assert result[0].title == "Channel Title"
    assert result[0].description == "Feed description"
    assert result[0].website_url == "https://example.com/"
    assert mock_get.call_count == 2


def test_discover_sources_omits_advertised_non_feed():
    page = _http_response(
        "https://example.com/",
        b"<link rel='alternate' type='application/atom+xml' href='/fake'>",
    )
    fake_feed = _http_response("https://example.com/fake", b"<html>no</html>")
    with patch(
        "src.adapters.source_discovery.requests.Session.get",
        side_effect=[page, fake_feed],
    ):
        result = SourceDiscoveryAdapter().discover("https://example.com/")
    assert result == []


def test_discover_sources_accepts_empty_atom_feed():
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


def test_normalize_feed_url_keeps_path_query_and_removes_defaults():
    assert (
        normalize_feed_url("HTTPS://Example.COM:443/feed/?a=1#top")
        == "https://example.com/feed/?a=1"
    )


def test_discover_sources_uses_final_url_after_redirect():
    feed = _http_response(
        "https://example.com/feed",
        b"<rss version='2.0'><channel><title>Final</title></channel></rss>",
    )
    with patch(
        "src.adapters.source_discovery.requests.Session.get",
        return_value=feed,
    ):
        result = SourceDiscoveryAdapter().discover("https://example.com/old")
    assert result[0].url == "https://example.com/feed"


def test_discover_sources_rejects_response_larger_than_limit():
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


def test_discover_sources_handles_timeout():
    with patch(
        "src.adapters.source_discovery.requests.Session.get",
        side_effect=requests.Timeout,
    ):
        result = SourceDiscoveryAdapter().discover("https://example.com/feed")
    assert result == []

from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.adapters.source_discovery import (
    SourceDiscoveryAdapter,
)
from src.config.settings import settings


def _result(*feeds, root_error=None):
    return SimpleNamespace(
        feeds=[Mock(serialize=Mock(return_value=feed)) for feed in feeds],
        root_error=root_error,
    )


def test_discovery_maps_metadata_and_prefers_primary_links():
    fallback = {
        "url": "HTTPS://FEEDS.EXAMPLE.NET:443/feed.xml?a=1#fragment",
        "title": "Feed title",
        "description": "News",
        "content_type": "application/rss+xml; charset=utf-8",
        "image": "https://example.com/artwork.png",
        "link": "https://example.com/",
        "site_name": "Example News",
        "language": "hu-HU",
    }
    primary = {
        "url": "https://example.com/other.xml",
        "favicon": "https://example.com/favicon.ico",
        "image": "https://example.com/ignored-image.png",
        "site_url": "https://news.example.com/",
        "link": "https://example.com/ignored-link",
        "language": "invalid-language",
    }
    with patch(
        "src.adapters.source_discovery.search_with_info",
        return_value=_result(fallback, primary),
    ) as search:
        result = SourceDiscoveryAdapter().discover(
            "HTTPS://FEEDS.EXAMPLE.NET:443/feed.xml?a=1#top"
        )

    assert len(result) == 2
    assert result[0].url == "https://feeds.example.net/feed.xml?a=1"
    assert result[0].title == "Feed title"
    assert result[0].description == "News"
    assert result[0].content_type == "application/rss+xml"
    assert result[0].favicon == fallback["image"]
    assert result[0].site_url == fallback["link"]
    assert result[0].site_name == "Example News"
    assert result[0].language == "hu"
    assert result[1].favicon == primary["favicon"]
    assert result[1].site_url == primary["site_url"]
    assert result[1].language is None
    search.assert_called_once()
    assert search.call_args.args == ("https://feeds.example.net/feed.xml?a=1",)
    assert (
        search.call_args.kwargs["total_timeout"]
        == settings.source_validation_timeout_seconds
    )
    assert (
        search.call_args.kwargs["max_content_length"]
        == settings.source_validation_max_bytes
    )


def test_discovery_accepts_bare_domain():
    with patch(
        "src.adapters.source_discovery.search_with_info",
        return_value=_result({"url": "https://24.hu/feed/"}),
    ) as search:
        result = SourceDiscoveryAdapter().discover(" 24.hu ")

    assert [item.url for item in result] == ["https://24.hu/feed/"]
    assert search.call_args.args == ("24.hu",)


def test_discovery_skips_invalid_and_duplicate_feed_urls():
    with patch(
        "src.adapters.source_discovery.search_with_info",
        return_value=_result(
            {"url": "ftp://example.com/feed"},
            {"url": "https://example.com/feed"},
            {"url": "https://example.com/feed#duplicate"},
        ),
    ):
        result = SourceDiscoveryAdapter().discover("https://example.com/")

    assert [item.url for item in result] == ["https://example.com/feed"]


def test_discovery_handles_empty_and_failed_search():
    with patch("src.adapters.source_discovery.search_with_info") as search:
        assert SourceDiscoveryAdapter().discover("not-a-url") == []
        search.assert_not_called()

        search.return_value = _result(root_error="timeout")
        assert SourceDiscoveryAdapter().discover("https://example.com/") == []

        search.side_effect = OSError("search failed")
        assert SourceDiscoveryAdapter().discover("https://example.com/") == []

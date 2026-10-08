from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.adapters.source_discovery import (
    SourceDiscoveryAdapter,
    normalize_feed_url,
)
from src.config.settings import settings


def _result(*feeds, root_error=None):
    return SimpleNamespace(
        feeds=[Mock(serialize=Mock(return_value=feed)) for feed in feeds],
        root_error=root_error,
    )


def test_discovery_maps_feed_and_site_metadata():
    feed = {
        "url": "https://feeds.example.net/feed.xml#fragment",
        "title": "Feed title",
        "description": "News",
        "content_type": "application/rss+xml; charset=utf-8",
        "favicon": None,
        "image": "https://example.com/apple-touch-icon.png",
        "site_url": "https://www.example.com/",
        "site_name": "Example News",
        "language": "hu-HU",
    }
    with patch(
        "src.adapters.source_discovery.search_with_info",
        return_value=_result(feed),
    ) as search:
        result = SourceDiscoveryAdapter().discover(
            "HTTPS://FEEDS.EXAMPLE.NET:443/feed.xml#top"
        )

    assert len(result) == 1
    assert result[0].url == "https://feeds.example.net/feed.xml"
    assert result[0].content_type == "application/rss+xml"
    assert result[0].favicon == feed["image"]
    assert result[0].site_url == feed["site_url"]
    assert result[0].site_name == "Example News"
    assert result[0].language == "hu"
    search.assert_called_once_with(
        "https://feeds.example.net/feed.xml",
        try_urls=False,
        crawl_hosts=True,
        total_timeout=settings.source_validation_timeout_seconds,
        max_content_length=settings.source_validation_max_bytes,
        favicon_data_uri=False,
    )


def test_discovery_prefers_favicon_and_feed_site_link():
    with patch(
        "src.adapters.source_discovery.search_with_info",
        return_value=_result(
            {
                "url": "https://example.com/feed",
                "favicon": "https://example.com/favicon.ico",
                "image": "https://example.com/artwork.png",
                "link": "https://example.com/",
            }
        ),
    ):
        result = SourceDiscoveryAdapter().discover("https://example.com/feed")

    assert result[0].favicon == "https://example.com/favicon.ico"
    assert result[0].site_url == "https://example.com/"


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


def test_normalize_feed_url_keeps_path_query_and_removes_defaults():
    assert (
        normalize_feed_url("HTTPS://Example.COM:443/feed/?a=1#top")
        == "https://example.com/feed/?a=1"
    )

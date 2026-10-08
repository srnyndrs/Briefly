import logging
import warnings

from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


from urllib.parse import urljoin, urlsplit, urlunsplit
from feedsearch_crawler import search_with_info

import feedparser
import requests
from bs4 import BeautifulSoup
from requests import Response

from src.config.settings import settings
from src.schemas.sources import SourceDiscoverResponse

logger = logging.getLogger(__name__)

FEED_TYPES = {
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
}


def normalize_feed_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").encode("idna").decode("ascii").lower()

    if scheme not in {"http", "https"} or not host:
        raise ValueError("A valid HTTP(S) URL is required")

    if parts.username is not None or parts.password is not None:
        raise ValueError("URL credentials are not allowed")

    port = parts.port
    netloc = f"[{host}]" if ":" in host else host

    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc = f"{netloc}:{port}"

    return urlunsplit((scheme, netloc, parts.path, parts.query, ""))


class SourceDiscoveryAdapter:
    def discover(self, url: str) -> list[SourceDiscoverResponse]:
        if not url:
            logger.warning("URL is empty or None")
            return []

        try:
            result = search_with_info(url,
                try_urls=False,
                crawl_hosts=True,
                total_timeout=30.0,
                request_timeout=3.0,
                max_content_length=10 * 1024 * 1024,
                max_depth=10,
                favicon_data_uri=False,
            )
            discovered_feeds: list[SourceDiscoverResponse] = []
            for feed_data in (feed.serialize() for feed in result.feeds):
                try:
                    feed_url = normalize_feed_url(str(feed_data.get("url") or ""))
                except (ValueError, UnicodeError):
                    continue

                discovered_feeds.append(
                    SourceDiscoverResponse(
                        url=feed_url,
                        title=feed_data.get("title"),
                        description=feed_data.get("description"),
                        content_type=feed_data.get("content_type"),
                        favicon=_valid_website_url(feed_data.get("favicon")),
                        website_url=_valid_website_url(
                            feed_data.get("site_url") or feed_data.get("feed.link")
                        ),
                        site_name=feed_data.get("site_name"),
                        language=feed_data.get("language"),
                    )
                )
            if discovered_feeds:
                return discovered_feeds

        except (requests.RequestException, ValueError, OSError) as exc:
            logger.info("Source discovery failed for %s: %s", url, exc)
            return []

    @staticmethod
    def _direct_feed_result(
        response: Response,
    ) -> SourceDiscoverResponse | None:
        parsed = feedparser.parse(response.content)
        version = getattr(parsed, "version", "") or ""
        if not (
            version.startswith("rss")
            or version.startswith("atom")
        ):
            return None

        feed = parsed.feed
        content_type = response.headers.get("Content-Type", "")
        content_type = content_type.split(";", 1)[0].strip() or None
        website_url = _valid_website_url(getattr(feed, "link", None))
        final_url = normalize_feed_url(response.url)
        image = getattr(feed, "image", None)

        return SourceDiscoverResponse(
            url=final_url,
            title=getattr(feed, "title", None),
            content_type=content_type,
            favicon=getattr(image, "href", None) or getattr(image, "url", None),
            description=getattr(feed, "subtitle", None),
            website_url=website_url,
        )

    @staticmethod
    def _extract_publisher_name(soup: BeautifulSoup) -> str | None:
        for attributes in (
            {"property": "og:site_name"},
            {"name": "application-name"},
        ):
            tag = soup.find("meta", attributes)
            if tag:
                value = tag.get("content")
                if value and value.strip():
                    return " ".join(value.split())

        return None

    @staticmethod
    def _extract_site_title(soup: BeautifulSoup) -> str | None:
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(" ", strip=True)
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text(" ", strip=True)

        return None

    @staticmethod
    def _extract_favicon(soup: BeautifulSoup, base_url: str) -> str | None:
        favicon_link = soup.find(
            "link",
            {"rel": lambda value: value and "icon" in str(value).lower()},
        )
        if favicon_link:
            href = favicon_link.get("href")
            if href:
                return urljoin(base_url, href)

        return None

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> str | None:
        for attributes in (
            {"name": "description"},
            {"property": "og:description"},
        ):
            meta = soup.find("meta", attributes)
            if meta and meta.get("content"):
                return " ".join(meta["content"].split())

        return None


def _valid_website_url(value: object) -> str | None:
    if not value:
        return None
    try:
        normalized = normalize_feed_url(str(value))
    except (ValueError, UnicodeError):
        return None

    return normalized

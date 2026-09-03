import logging
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from src.schemas.schemas import SourceDiscoverResult

logger = logging.getLogger(__name__)

FEED_TYPES = {
    "application/rss+xml": "RSS",
    "application/atom+xml": "Atom",
    "application/feed+json": "JSON Feed",
    "application/json": "JSON Feed",
    "text/xml": "XML",
}


class SourceDiscoveryAdapter:
    def extract_website_url(self, source_url: str) -> str | None:
        try:
            response = requests.get(source_url, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            return getattr(feed.feed, "link", None) or None
        except Exception:  # noqa: BLE001
            return None

    def discover(self, url: str) -> list[SourceDiscoverResult]:
        if not url:
            logger.warning("URL is empty or None")
            return []

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            base_url = response.url

            direct_feed = self._direct_feed_result(response)
            if direct_feed is not None:
                return [direct_feed]

            soup = BeautifulSoup(response.text, "html.parser")

            sources: list[SourceDiscoverResult] = []
            feed_links = soup.find_all(
                "link",
                {
                    "type": lambda t: (
                        t and any(ft in t for ft in FEED_TYPES.keys())
                    )
                },
            )

            for link in feed_links:
                href = link.get("href")
                if href:
                    feed_url = urljoin(base_url, href)
                    sources.append(
                        SourceDiscoverResult(
                            url=feed_url,
                            title=link.get("title")
                            or self._extract_site_title(soup),
                            content_type=link.get("type"),
                            favicon=self._extract_favicon(
                                soup, base_url
                            ),
                            description=self._extract_description(soup),
                        )
                    )

            return sources
        except requests.exceptions.Timeout:
            logger.error("Request timeout for URL: %s", url)
            return []

        except requests.exceptions.RequestException as exc:
            logger.error("Failed to fetch URL %s: %s", url, str(exc))
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Unexpected error discovering feeds for %s: %s",
                url,
                str(exc),
            )
            return []

    def _direct_feed_result(
        self, response: requests.Response
    ) -> SourceDiscoverResult | None:
        parsed = feedparser.parse(response.content)
        if not parsed.version:
            return None

        feed = parsed.feed
        content_type = response.headers.get("Content-Type", "")
        content_type = content_type.split(";", 1)[0].strip() or None
        return SourceDiscoverResult(
            url=response.url,
            title=getattr(feed, "title", None),
            content_type=content_type,
            favicon=getattr(getattr(feed, "image", None), "href", None),
            description=getattr(feed, "subtitle", None),
        )

    def _extract_site_title(self, soup: BeautifulSoup) -> str | None:
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text(strip=True)
        return None

    def _extract_favicon(
        self, soup: BeautifulSoup, base_url: str
    ) -> str | None:
        favicon_link = soup.find(
            "link", {"rel": lambda r: r and "icon" in r.lower()}
        )
        if favicon_link:
            href = favicon_link.get("href")
            if href:
                return urljoin(base_url, href)
        return None

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc:
            return meta_desc.get("content")
        meta_og_desc = soup.find("meta", {"property": "og:description"})
        if meta_og_desc:
            return meta_og_desc.get("content")
        return None

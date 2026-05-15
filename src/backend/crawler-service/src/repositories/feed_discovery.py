"""Feed discovery adapter."""

import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.schemas.schemas import ExploreResult

logger = logging.getLogger(__name__)

FEED_TYPES = {
    "application/rss+xml": "RSS",
    "application/atom+xml": "Atom",
    "application/feed+json": "JSON Feed",
    "application/json": "JSON Feed",
    "text/xml": "XML",
}


class FeedDiscoveryAdapter:
    """Discover RSS/Atom feeds for a given URL."""

    def discover(self, url: str) -> list[ExploreResult]:
        if not url:
            logger.warning("URL is empty or None")
            return []

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            base_url = response.url

            feeds: list[ExploreResult] = []
            feed_links = soup.find_all(
                "link",
                {
                    "type": lambda t: (
                        t
                        and any(ft in t for ft in FEED_TYPES.keys())
                    )
                },
            )

            for link in feed_links:
                href = link.get("href")
                if href:
                    feed_url = urljoin(base_url, href)
                    feeds.append(
                        ExploreResult(
                            url=feed_url,
                            title=link.get("title")
                            or self._extract_site_title(soup),
                            content_type=link.get("type"),
                            favicon=self._extract_favicon(
                                soup, base_url
                            ),
                            description=self._extract_description(
                                soup
                            ),
                        )
                    )

            if not feeds:
                feeds.extend(
                    self._try_common_feed_paths(base_url, soup)
                )

            return feeds
        except requests.exceptions.Timeout:
            logger.error("Request timeout for URL: %s", url)
            return []
        except requests.exceptions.RequestException as exc:
            logger.error(
                "Failed to fetch URL %s: %s", url, str(exc)
            )
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Unexpected error discovering feeds for %s: %s",
                url,
                str(exc),
            )
            return []

    def _extract_site_title(
        self, soup: BeautifulSoup
    ) -> str | None:
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

    def _extract_description(
        self, soup: BeautifulSoup
    ) -> str | None:
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc:
            return meta_desc.get("content")
        meta_og_desc = soup.find(
            "meta", {"property": "og:description"}
        )
        if meta_og_desc:
            return meta_og_desc.get("content")
        return None

    def _try_common_feed_paths(
        self,
        base_url: str,
        soup: BeautifulSoup,
    ) -> list[ExploreResult]:
        common_paths = [
            "/feed",
            "/rss",
            "/feed.xml",
            "/rss.xml",
            "/atom.xml",
            "/feeds/all.atom.xml",
        ]

        feeds: list[ExploreResult] = []
        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        for path in common_paths:
            feed_url = domain + path
            try:
                response = requests.head(
                    feed_url, timeout=10, allow_redirects=True
                )
                if response.status_code == 200:
                    feeds.append(
                        ExploreResult(
                            url=feed_url,
                            title=self._extract_site_title(soup),
                            content_type="application/rss+xml",
                            favicon=self._extract_favicon(
                                soup, base_url
                            ),
                            description=self._extract_description(
                                soup
                            ),
                        )
                    )
            except requests.exceptions.RequestException:
                continue

        return feeds

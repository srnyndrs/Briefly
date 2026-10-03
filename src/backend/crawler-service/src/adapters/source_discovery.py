import logging
from urllib.parse import urljoin, urlsplit, urlunsplit

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


def _bounded_get(url: str) -> Response:
    with requests.Session() as session:
        session.max_redirects = settings.source_validation_max_redirects
        response = session.get(
            normalize_feed_url(url),
            timeout=settings.source_validation_timeout_seconds,
            stream=True,
            headers={"User-Agent": "briefly-source-discovery/1.0"},
        )
        try:
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                body.extend(chunk)
                if len(body) > settings.source_validation_max_bytes:
                    raise ValueError(
                        "Response exceeds the configured size limit"
                    )
            response._content = bytes(body)
            return response
        finally:
            response.close()


class SourceDiscoveryAdapter:
    def discover(self, url: str) -> list[SourceDiscoverResponse]:
        if not url:
            logger.warning("URL is empty or None")
            return []

        try:
            response = _bounded_get(url)
            direct_result = self._direct_feed_result(response)
            if direct_result is not None:
                return [direct_result]

            page_url = response.url
            soup = BeautifulSoup(response.content, "html.parser")
            publisher_name = self._extract_publisher_name(soup)
            page_title = self._extract_site_title(soup)
            page_favicon = self._extract_favicon(soup, page_url)
            page_description = self._extract_description(soup)
            results: list[SourceDiscoverResponse] = []
            seen_candidate_urls: set[str] = set()
            seen_final_urls: set[str] = set()

            for link in soup.find_all("link"):
                rel = link.get("rel") or []
                if isinstance(rel, str):
                    rel = rel.split()
                content_type = (link.get("type") or "").split(";", 1)[0]
                if "alternate" not in {value.lower() for value in rel}:
                    continue
                if content_type.strip().lower() not in FEED_TYPES:
                    continue
                href = link.get("href")
                if not href:
                    continue
                try:
                    candidate_url = normalize_feed_url(urljoin(page_url, href))
                    if candidate_url in seen_candidate_urls:
                        continue
                    seen_candidate_urls.add(candidate_url)
                    candidate = _bounded_get(candidate_url)
                    result = self._direct_feed_result(candidate)
                    if result is None or result.url in seen_final_urls:
                        continue
                    seen_final_urls.add(result.url)
                    result.website_url = (
                        _valid_website_url(result.website_url) or page_url
                    )
                    result.title = (
                        result.title
                        or publisher_name
                        or link.get("title")
                        or page_title
                    )
                    result.favicon = result.favicon or page_favicon
                    result.description = result.description or page_description
                    results.append(result)
                except (
                    requests.RequestException,
                    ValueError,
                    OSError,
                ) as exc:
                    logger.info("Skipping invalid advertised feed: %s", exc)
            return results
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


def _valid_website_url(value: str | None) -> str | None:
    if not value:
        return None
    try:
        normalized = normalize_feed_url(value)
    except ValueError:
        return None

    return normalized

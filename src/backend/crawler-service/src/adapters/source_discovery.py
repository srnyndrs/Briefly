import ipaddress
import logging
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit

import feedparser
import requests
import tldextract
from bs4 import BeautifulSoup
from requests import Response

from src.config.settings import settings
from src.schemas.sources import SourceDiscoverResult

logger = logging.getLogger(__name__)

FEED_TYPES = {
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
_TLD_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())


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
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        netloc = f"{netloc}:{port}"
    return urlunsplit((scheme, netloc, parts.path, parts.query, ""))


def normalize_host(url: str) -> str | None:
    try:
        host = urlsplit(url).hostname
        if not host:
            return None
        normalized = host.encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError):
        return None
    return (
        normalized[4:] if normalized.startswith("www.") else normalized
    )


def registrable_domain(url: str) -> str:
    host = normalize_host(url)
    if not host:
        raise ValueError("A valid website or feed URL is required")
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        pass
    result = _TLD_EXTRACT(host)
    domain = ".".join(
        part for part in (result.domain, result.suffix) if part
    )
    if not domain:
        raise ValueError("URL does not have a registrable domain")
    return domain


def normalize_source_title(title: str | None) -> str | None:
    if title is None:
        return None
    normalized = " ".join(title.split())
    return normalized.casefold() or None


def _assert_public_destination(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are accepted")
    if parts.username is not None or parts.password is not None:
        raise ValueError("URL credentials are not allowed")
    host = parts.hostname
    if not host:
        raise ValueError("URL host is required")
    normalized_host = host.encode("idna").decode("ascii").lower()
    if normalized_host == "localhost" or normalized_host.endswith(
        ".localhost"
    ):
        raise ValueError("Non-public destinations are not allowed")

    try:
        literal_address = ipaddress.ip_address(normalized_host)
    except ValueError:
        addresses = {
            ipaddress.ip_address(result[4][0])
            for result in socket.getaddrinfo(
                normalized_host, parts.port, type=socket.SOCK_STREAM
            )
        }
    else:
        addresses = {literal_address}

    if not addresses or any(
        not address.is_global for address in addresses
    ):
        raise ValueError("Non-public destinations are not allowed")


def _bounded_get(url: str) -> Response:
    current_url = normalize_feed_url(url)
    for redirect_count in range(
        settings.source_validation_max_redirects + 1
    ):
        _assert_public_destination(current_url)
        response = requests.get(
            current_url,
            timeout=settings.source_validation_timeout_seconds,
            allow_redirects=False,
            stream=True,
            headers={"User-Agent": "briefly-source-validator/1.0"},
        )
        if response.status_code in REDIRECT_STATUSES:
            location = response.headers.get("Location")
            response.close()
            if (
                not location
                or redirect_count
                >= settings.source_validation_max_redirects
            ):
                raise ValueError("Too many or invalid redirects")
            current_url = normalize_feed_url(
                urljoin(current_url, location)
            )
            continue

        try:
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                body.extend(chunk)
                if len(body) > settings.source_validation_max_bytes:
                    raise ValueError(
                        "Response exceeds the configured size limit"
                    )
            response._content = bytes(body)
            response.url = current_url
            return response
        finally:
            response.close()
    raise ValueError("Too many redirects")


class SourceDiscoveryAdapter:
    def discover(self, url: str) -> list[SourceDiscoverResult]:
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
            results: list[SourceDiscoverResult] = []
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
                    candidate_url = normalize_feed_url(
                        urljoin(page_url, href)
                    )
                    if candidate_url in seen_candidate_urls:
                        continue
                    seen_candidate_urls.add(candidate_url)
                    candidate = _bounded_get(candidate_url)
                    result = self._direct_feed_result(candidate)
                    if result is None or result.url in seen_final_urls:
                        continue
                    seen_final_urls.add(result.url)
                    result.website_url = (
                        _valid_website_url(result.website_url)
                        or page_url
                    )
                    result.title = (
                        result.title
                        or publisher_name
                        or link.get("title")
                        or page_title
                    )
                    result.favicon = result.favicon or page_favicon
                    result.description = (
                        result.description or page_description
                    )
                    result.registrable_domain = registrable_domain(
                        result.website_url or result.url
                    )
                    results.append(result)
                except (
                    requests.RequestException,
                    ValueError,
                    OSError,
                ) as exc:
                    logger.info(
                        "Skipping invalid advertised feed: %s", exc
                    )
            return results
        except (requests.RequestException, ValueError, OSError) as exc:
            logger.info("Source discovery failed for %s: %s", url, exc)
            return []

    def _direct_feed_result(
        self, response: Response
    ) -> SourceDiscoverResult | None:
        parsed = feedparser.parse(response.content)
        if not (
            parsed.version.startswith("rss")
            or parsed.version.startswith("atom")
        ):
            return None

        feed = parsed.feed
        content_type = response.headers.get("Content-Type", "")
        content_type = content_type.split(";", 1)[0].strip() or None
        website_url = _valid_website_url(getattr(feed, "link", None))
        final_url = normalize_feed_url(response.url)
        domain_url = website_url or final_url
        image = getattr(feed, "image", None)
        return SourceDiscoverResult(
            url=final_url,
            title=getattr(feed, "title", None),
            content_type=content_type,
            favicon=getattr(image, "href", None)
            or getattr(image, "url", None),
            description=getattr(feed, "subtitle", None),
            website_url=website_url,
            registrable_domain=registrable_domain(domain_url),
        )

    def _extract_publisher_name(
        self, soup: BeautifulSoup
    ) -> str | None:
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

    def _extract_site_title(self, soup: BeautifulSoup) -> str | None:
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(" ", strip=True)
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text(" ", strip=True)
        return None

    def _extract_favicon(
        self, soup: BeautifulSoup, base_url: str
    ) -> str | None:
        favicon_link = soup.find(
            "link",
            {
                "rel": lambda value: (
                    value and "icon" in str(value).lower()
                )
            },
        )
        if favicon_link:
            href = favicon_link.get("href")
            if href:
                return urljoin(base_url, href)
        return None

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
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

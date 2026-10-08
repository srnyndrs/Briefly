import logging
import warnings
from urllib.parse import urlsplit, urlunsplit

from bs4 import XMLParsedAsHTMLWarning
from feedsearch_crawler import search_with_info

from src.config.settings import settings
from src.schemas.sources import SourceDiscoverResponse

logger = logging.getLogger(__name__)


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


def _valid_url(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return normalize_feed_url(value)
    except ValueError:
        return None


class SourceDiscoveryAdapter:
    @staticmethod
    def discover(url: str) -> list[SourceDiscoverResponse]:
        try:
            normalized_url = normalize_feed_url(url)
        except (ValueError, UnicodeError):
            return []

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
                result = search_with_info(
                    normalized_url,
                    try_urls=False,
                    crawl_hosts=True,
                    total_timeout=settings.source_validation_timeout_seconds,
                    max_content_length=settings.source_validation_max_bytes,
                    favicon_data_uri=False,
                )
        except (ValueError, OSError) as exc:
            logger.info(
                "Source discovery failed for %s: %s", normalized_url, exc
            )
            return []

        if result.root_error:
            logger.info(
                "Source discovery failed for %s: %s",
                normalized_url,
                result.root_error,
            )

        discovered: list[SourceDiscoverResponse] = []
        seen_urls: set[str] = set()
        for feed in result.feeds:
            data = feed.serialize()
            feed_url = _valid_url(data.get("url"))
            if feed_url is None or feed_url in seen_urls:
                continue
            seen_urls.add(feed_url)
            content_type = (data.get("content_type") or "").split(";", 1)[0]
            discovered.append(
                SourceDiscoverResponse(
                    url=feed_url,
                    title=data.get("title"),
                    description=data.get("description"),
                    content_type=content_type or None,
                    favicon=_valid_url(data.get("favicon"))
                    or _valid_url(data.get("image")),
                    site_url=_valid_url(data.get("site_url"))
                    or _valid_url(data.get("link")),
                    site_name=data.get("site_name"),
                    language=data.get("language"),
                )
            )

        return discovered

import logging
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests

from src.config.settings import settings

logger = logging.getLogger(__name__)
_VALIDATOR_LOG_LIMIT = 200


def _safe_validator(value: str | None) -> str:
    if value is None:
        return "<absent>"
    escaped = repr(value)
    if len(escaped) > _VALIDATOR_LOG_LIMIT:
        return escaped[: _VALIDATOR_LOG_LIMIT - 3] + "..."
    return escaped


@dataclass
class FetchHeaders:
    etag: str | None = None
    last_modified: str | None = None


@dataclass
class HttpFetchResult:
    body: str
    status_code: int
    etag: str | None
    last_modified: str | None


class RequestsHttpClient:
    @staticmethod
    def fetch(url: str, headers: FetchHeaders) -> HttpFetchResult:
        request_headers: dict[str, str] = {
            "User-Agent": "briefly-crawler",
        }
        if headers.etag:
            request_headers["If-None-Match"] = headers.etag
        if headers.last_modified:
            request_headers["If-Modified-Since"] = headers.last_modified

        response = requests.get(
            url,
            headers=request_headers,
            timeout=settings.fetch_timeout_seconds,
        )
        response_etag = response.headers.get("ETag")
        response_last_modified = response.headers.get("Last-Modified")
        logger.info(
            "Feed HTTP response (host=%s, status=%d, "
            "if_none_match=%s, if_modified_since=%s, etag=%s, "
            "last_modified=%s)",
            urlsplit(url).hostname or "unknown",
            response.status_code,
            _safe_validator(request_headers.get("If-None-Match")),
            _safe_validator(request_headers.get("If-Modified-Since")),
            _safe_validator(response_etag),
            _safe_validator(response_last_modified),
        )

        if response.status_code == 304:
            return HttpFetchResult(
                body="",
                status_code=304,
                etag=headers.etag,
                last_modified=headers.last_modified,
            )

        response.raise_for_status()
        return HttpFetchResult(
            body=response.text,
            status_code=response.status_code,
            etag=response_etag,
            last_modified=response_last_modified,
        )

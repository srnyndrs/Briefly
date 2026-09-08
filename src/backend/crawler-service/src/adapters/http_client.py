import requests

from src.config.settings import settings
from dataclasses import dataclass


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
    def fetch(self, url: str, headers: FetchHeaders) -> HttpFetchResult:
        request_headers: dict[str, str] = {
            "User-Agent": "briefly-crawler/1.0"
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
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
        )

import logging
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from requests.exceptions import ReadTimeout

from src.adapters.content_extractor import (
    extract_article,
    normalize_article_url,
)
from src.config.settings import Settings, settings


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_article_timeout_must_be_positive(timeout: float) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None, article_request_timeout_seconds=timeout
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/article?first=1&second=2",
        "http://example.com/article,",
        "https://example.com/article:",
    ],
)
def test_article_url_trims_whitespace_and_preserves_punctuation(
    url: str,
) -> None:
    assert normalize_article_url(f"  {url} \n") == url


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https:///missing-host",
        "https://[broken",
        "https://example.com:not-a-port/",
        "https://example.com/a\nb",
        "https://user:password@example.com/article",
    ],
)
def test_invalid_article_url_never_starts_download(url: str) -> None:
    with patch(
        "src.adapters.content_extractor._MetadataArticle"
    ) as article:
        result = extract_article(url)

    article.assert_not_called()
    assert result["outcome"] == "invalid_url"


def test_invalid_link_log_escapes_controls_and_omits_query_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    normalize_article_url("https://example.com/a\nb?secret=value")
    normalize_article_url(
        "https://user:password@example.com/?secret=value"
    )

    assert "a\\nb" in caplog.text
    assert "secret" not in caplog.text
    assert "password" not in caplog.text


@pytest.mark.parametrize("metadata_image", [True, False])
def test_real_parser_keeps_metadata_image_without_image_downloads(
    metadata_image: bool,
) -> None:
    image_tag = (
        '<meta property="og:image" content="/image.jpg">'
        if metadata_image
        else ""
    )
    html = (
        f"<html><head><title>Article title</title>{image_tag}</head>"
        "<body><article><h1>Article title</h1><p>"
        + "This article contains enough words to identify the main text. "
        * 30
        + '</p><img src="https://example.com/fallback.jpg">'
        "</article></body></html>"
    )
    with (
        patch(
            "newspaper.article.network.get_html_status",
            return_value=(html, 200, []),
        ) as download,
        patch(
            "newspaper.extractors.image_extractor.ImageExtractor._fetch_image",
            side_effect=AssertionError("Images must not be downloaded"),
        ) as image_download,
        patch.object(settings, "article_request_timeout_seconds", 2.5),
    ):
        result = extract_article("https://example.com/article")

    assert result["outcome"] == "success"
    assert "main text" in result["content"]
    assert result["image"] == (
        "https://example.com/image.jpg" if metadata_image else None
    )
    image_download.assert_not_called()
    config = download.call_args.args[1]
    assert config.request_timeout == 2.5
    assert config.fetch_images is False


@pytest.mark.parametrize("failure", ["timeout", "502", "cloudflare"])
def test_download_failure_logs_compact_outcome_without_response_or_url(
    failure: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    with patch("newspaper.article.network.get_html_status") as download:
        if failure == "timeout":
            download.side_effect = ReadTimeout("Timeout ?secret=value")
        else:
            html = (
                "<html>cloudflare secret-response-body</html>"
                if failure == "cloudflare"
                else "<html>secret-response-body</html>"
            )
            download.return_value = (html, 502, [])
        result = extract_article(
            "https://example.com/article?secret=value"
        )

    assert result["outcome"] == "failed"
    assert result["error"] == "ArticleException"
    assert "host=example.com" in caplog.text
    assert "outcome=failed" in caplog.text
    assert "duration_seconds=" in caplog.text
    assert "secret" not in caplog.text


def test_successful_download_with_no_text_has_empty_outcome(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch(
        "newspaper.article.network.get_html_status",
        return_value=(
            "<html><head><title>Title</title></head></html>",
            200,
            [],
        ),
    ):
        result = extract_article("https://example.com/empty")

    assert result["outcome"] == "empty"
    assert not result["content"]
    assert "error" not in result
    assert "outcome=empty" in caplog.text

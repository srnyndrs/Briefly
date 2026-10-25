import logging
from unittest.mock import patch

import pytest
from requests.exceptions import ReadTimeout

from src.adapters.content_extractor import (
    extract_article,
    normalize_article_url,
)
from src.config.settings import settings


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https://user:password@example.com/article",
    ],
)
def test_invalid_article_url_never_starts_download(url: str) -> None:
    with patch("src.adapters.content_extractor._MetadataArticle") as article:
        result = extract_article(url)

    article.assert_not_called()
    assert result["outcome"] == "invalid_url"


def test_invalid_link_log_escapes_controls_and_omits_query_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    normalize_article_url("https://example.com/a\nb?secret=value")
    normalize_article_url("https://user:password@example.com/?secret=value")

    assert "secret" not in caplog.text
    assert "password" not in caplog.text


@pytest.mark.parametrize("metadata_image", [True, False])
def test_real_parser_keeps_metadata_image_without_image_downloads(
    metadata_image: bool,
) -> None:
    image_tag = (
        '<meta property="og:image" content="/image.jpg">' if metadata_image else ""
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
        result = extract_article("  https://example.com/article  ")

    assert result["outcome"] == "success"
    assert "main text" in result["content"]
    assert result["image"] == (
        "https://example.com/image.jpg" if metadata_image else None
    )
    image_download.assert_not_called()
    config = download.call_args.args[1]
    assert config.request_timeout == 2.5
    assert config.fetch_images is False


def test_download_timeout_returns_failed_outcome_without_sensitive_content(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    with patch(
        "newspaper.article.network.get_html_status",
        side_effect=ReadTimeout("Timeout ?secret=value"),
    ):
        result = extract_article("https://example.com/article?secret=value")
    assert result["outcome"] == "failed"
    assert "secret" not in str(result)
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

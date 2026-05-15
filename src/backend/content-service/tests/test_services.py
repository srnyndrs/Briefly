"""
Tests for FeedProcessorService (replaces old use-case tests).
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.services.feed_processor import FeedProcessorService


def _make_event(
    feed_id: str = "f1", raw_xml: str = "<xml/>"
) -> dict:
    return {
        "payload": {
            "feed_id": feed_id,
            "raw_xml": raw_xml,
        },
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }


def test_process_feed_persists_and_publishes() -> None:
    db = MagicMock()
    channel = MagicMock()

    entry = {
        "id": "g1",
        "link": "https://example.com/1",
        "title": "Title",
    }
    feed_mock = MagicMock()
    feed_mock.entries = [entry]

    with (
        patch(
            "src.services.feed_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.services.feed_processor.content_extractor"
            ".extract_article",
            return_value={
                "title": "Title",
                "content": "Body",
                "image": None,
            },
        ),
        patch(
            "src.repositories.article_repository"
            ".ArticleRepository.save",
            return_value="a1",
        ),
        patch(
            "src.services.feed_processor"
            ".event_publisher.publish_parsed_success"
        ) as mock_publish,
    ):
        FeedProcessorService(db).process(channel, _make_event())
        assert mock_publish.called
        call_kwargs = mock_publish.call_args.kwargs
        assert call_kwargs["article_id"] == "a1"
        assert call_kwargs["feed_id"] == "f1"


def test_process_feed_publishes_failure_on_extraction_error() -> (
    None
):
    db = MagicMock()
    channel = MagicMock()

    entry = {
        "id": "g1",
        "link": "https://bad.url",
        "title": "Bad",
    }
    feed_mock = MagicMock()
    feed_mock.entries = [entry]

    with (
        patch(
            "src.services.feed_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.services.feed_processor.content_extractor"
            ".extract_article",
            side_effect=RuntimeError("network error"),
        ),
        patch(
            "src.services.feed_processor"
            ".event_publisher.publish_parsed_failed"
        ) as mock_fail,
    ):
        FeedProcessorService(db).process(channel, _make_event())
        assert mock_fail.called

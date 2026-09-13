from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

from feedparser import FeedParserDict
import pytest
from sqlalchemy.orm import Session

from src.models.post import Post
from src.services.source_processor import SourceProcessorService


def _make_event(
    source_id: str = "s1",
    source_title: str = "Crawler Source",
    raw_xml: str = "<xml/>",
    correlation_id: str = "test-corr-id",
) -> dict:
    return {
        "correlation_id": correlation_id,
        "payload": {
            "source_id": source_id,
            "source_title": source_title,
            "raw_xml": raw_xml,
        },
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }


def _capture_saved_payload(
    entry: Any,
    extracted: dict[str, Any],
    feed_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    db = MagicMock()
    channel = MagicMock()
    feed_mock = MagicMock()
    feed_mock.entries = [entry]
    feed_mock.feed = feed_data or {}
    saved_payloads: list[dict[str, Any]] = []

    with (
        patch(
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value=extracted,
        ),
        patch(
            "src.repositories.post_repository.PostRepository.save",
            side_effect=lambda data: (
                saved_payloads.append(dict(data)) or "p1"
            ),
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ),
    ):
        SourceProcessorService(db).process(channel, _make_event())

    return saved_payloads[0]


def test_process_source_persists_and_publishes() -> None:
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
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "title": "Title",
                "content": "Body",
                "image": None,
            },
        ),
        patch(
            "src.repositories.post_repository.PostRepository.save",
            return_value="p1",
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        SourceProcessorService(db).process(channel, _make_event())
        assert mock_publish.called
        call_kwargs = mock_publish.call_args.kwargs
        assert call_kwargs["post_id"] == "p1"
        assert call_kwargs["source_id"] == "s1"
        assert call_kwargs["correlation_id"] == "test-corr-id"


def test_process_source_uses_feed_metadata_as_baseline() -> None:
    entry = FeedParserDict(
        {
            "id": "g-merge-policy",
            "link": "https://example.com/merge-policy",
            "title": " Feed title ",
            "description": " Feed description ",
            "author": " Feed author ",
            "tags": [{"term": "Feed category"}],
            "published_parsed": (
                2026,
                9,
                12,
                17,
                30,
                35,
                0,
                0,
            ),
            "links": [
                {
                    "rel": "enclosure",
                    "href": "https://example.com/feed-image.jpg",
                }
            ],
        }
    )
    saved = _capture_saved_payload(
        entry,
        {
            "title": "null: undefined",
            "description": "Extracted description",
            "content": "Extracted body",
            "image": "https://example.com/extracted-image.jpg",
            "authors": ["Extracted author"],
            "language": "en",
            "keywords": ["extracted"],
            "publish_date": datetime(
                2026, 9, 12, 0, 0, tzinfo=timezone.utc
            ),
        },
        {"title": "Publisher", "language": "hu"},
    )
    assert saved["title"] == "Feed title"
    assert saved["description"] == "Feed description"
    assert saved["author"] == "Feed author"
    assert saved["category"] == "Feed category"
    assert saved["published_at"] == datetime(
        2026, 9, 12, 17, 30, 35, tzinfo=timezone.utc
    )
    assert saved["image_url"] == "https://example.com/feed-image.jpg"
    assert saved["language"] == "hu"
    assert saved["content"] == "Extracted body"
    assert saved["keywords"] == ["extracted"]


def test_process_source_uses_valid_extracted_fallbacks() -> None:
    entry = FeedParserDict(
        {
            "id": "g-extracted-fallback",
            "link": "https://example.com/extracted-fallback",
            "title": " ",
        }
    )
    saved = _capture_saved_payload(
        entry,
        {
            "title": " Extracted title ",
            "description": " Extracted description ",
            "content": "Body",
            "image": " https://example.com/image.jpg ",
            "authors": [" Extracted author "],
            "language": " en ",
            "keywords": ["keyword"],
        },
    )
    assert saved["title"] == "Extracted title"
    assert saved["description"] == "Extracted description"
    assert saved["author"] == "Extracted author"
    assert saved["image_url"] == "https://example.com/image.jpg"
    assert saved["language"] == "en"


def test_process_source_rejects_malformed_extracted_title() -> None:
    entry = FeedParserDict(
        {
            "id": "g-malformed-title",
            "link": "https://example.com/malformed-title",
            "title": "",
        }
    )
    saved = _capture_saved_payload(
        entry,
        {"title": "null: undefined", "content": "Body"},
    )

    assert saved["title"] == "Untitled"


def test_process_source_stores_source_title() -> None:
    db = MagicMock()
    channel = MagicMock()

    entry = {
        "id": "g1",
        "link": "https://example.com/1",
        "title": "Title",
    }
    feed_mock = MagicMock()
    feed_mock.entries = [entry]
    feed_mock.feed = {
        "title": "Feed Publisher Title",
        "language": "hu",
    }

    saved_payloads: list[dict] = []

    def mock_save_impl(data: dict) -> str:
        saved_payloads.append(dict(data))
        return "p1"

    with (
        patch(
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "title": "Title",
                "content": "Body",
                "image": None,
            },
        ),
        patch(
            "src.repositories.post_repository.PostRepository.save",
            side_effect=mock_save_impl,
        ) as mock_save,
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        SourceProcessorService(db).process(
            channel,
            _make_event(source_id="s1", correlation_id="test-corr"),
        )
        assert mock_save.called
        assert len(saved_payloads) == 1
        assert saved_payloads[0].get("source_title") == "Crawler Source"
        assert (
            mock_publish.call_args.kwargs.get("source_title")
            == "Crawler Source"
        )


def test_process_source_persists_source_title(
    db_session: Session,
) -> None:
    channel = MagicMock()
    entry = {
        "id": "guid-persisted-title",
        "link": "https://example.com/persisted-title",
        "title": "Title",
    }
    feed_mock = MagicMock()
    feed_mock.entries = [entry]
    feed_mock.feed = {"title": "Persisted Publisher Title"}

    with (
        patch(
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"title": "Title", "content": "Body"},
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as mock_publish,
    ):
        SourceProcessorService(db_session).process(
            channel,
            _make_event(
                source_id="source-1",
                source_title="  Registered Source  ",
            ),
        )

    db_session.expire_all()
    post = (
        db_session.query(Post)
        .filter(Post.item_guid == "guid-persisted-title")
        .one()
    )
    assert post.source_title == "Registered Source"
    assert (
        mock_publish.call_args.kwargs["source_title"]
        == "Registered Source"
    )


def test_process_source_skips_entry_on_extraction_error() -> None:
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
            "src.services.source_processor.feedparser.parse",
            return_value=feed_mock,
        ),
        patch(
            "src.adapters.content_extractor.extract_article",
            side_effect=RuntimeError("network error"),
        ),
        patch(
            "src.repositories.post_repository.PostRepository.save"
        ) as mock_save,
    ):
        SourceProcessorService(db).process(channel, _make_event())
        assert not mock_save.called


@pytest.mark.parametrize("field", ["source_id", "source_title"])
def test_process_source_rejects_missing_source_identity(
    field: str,
) -> None:
    event = _make_event()
    event["payload"].pop(field)

    with pytest.raises(ValueError, match=field):
        SourceProcessorService(MagicMock()).process(MagicMock(), event)

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from src.models.post import Post
from src.services.source_processor import SourceProcessorService


def _make_event(
    source_id: str = "s1",
    raw_xml: str = "<xml/>",
    correlation_id: str = "test-corr-id",
) -> dict:
    return {
        "correlation_id": correlation_id,
        "payload": {
            "source_id": source_id,
            "raw_xml": raw_xml,
        },
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }


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
    feed_mock.feed = {"title": "Feed Publisher Title"}

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
            _make_event(
                source_id="s1",
                correlation_id="test-corr",
            ),
        )
        assert mock_save.called
        assert len(saved_payloads) == 1
        assert (
            saved_payloads[0].get("source_title")
            == "Feed Publisher Title"
        )
        assert (
            mock_publish.call_args.kwargs.get("source_title")
            == "Feed Publisher Title"
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
            _make_event(source_id="source-1"),
        )

    db_session.expire_all()
    post = (
        db_session.query(Post)
        .filter(Post.item_guid == "guid-persisted-title")
        .one()
    )
    assert post.source_title == "Persisted Publisher Title"
    assert (
        mock_publish.call_args.kwargs["source_title"]
        == "Persisted Publisher Title"
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

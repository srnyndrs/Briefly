from unittest.mock import MagicMock, patch
from uuid import uuid4

import pika
import pytest
from sqlalchemy.orm import Session

from src.models.post import Post
from src.repositories.post_repository import PostRepository
from src.scripts.replay_failed_feed import replay_failed_feed
from src.services.feed_processor import FeedProcessor


@pytest.fixture
def stored_post(db_session: Session) -> Post:
    snapshot = PostRepository(db_session).upsert_post(
        {
            "source_id": uuid4(),
            "item_guid": "recovery-item",
            "url": "https://example.com/article",
            "source_title": "Source",
            "title": "RSS title",
            "content": "Original body",
            "description": "RSS description",
            "keywords": ["rss"],
        }
    )
    assert snapshot is not None
    return PostRepository(db_session).get_post_by_id(snapshot["post_id"])


def test_reextract_refreshes_body_preserving_identity_and_metadata(
    db_session: Session, stored_post: Post
) -> None:
    post_id = stored_post.post_id
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={
                "content": " New body ",
                "title": "Website title",
            },
        ) as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        assert FeedProcessor(PostRepository(db_session)).reextract_post(
            MagicMock(), post_id
        )
    extract.assert_called_once_with("https://example.com/article")
    db_session.expire_all()
    post = PostRepository(db_session).get_post_by_id(post_id)
    assert post.content == "New body"
    assert post.title == "RSS title"
    assert post.description == "RSS description"
    assert post.keywords == ["rss"]
    assert post.post_revision == 2
    assert publish.call_args.kwargs["post_id"] == str(post_id)
    assert publish.call_args.kwargs["post_revision"] == 2
    assert publish.call_args.kwargs["content"] == "New body"


def test_identical_reextract_republishes_stored_revision_and_timestamps(
    db_session: Session, stored_post: Post
) -> None:
    post_id = stored_post.post_id
    original_times = (stored_post.crawled_at, stored_post.parsed_at)
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"content": " Original body "},
        ) as extract,
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        assert FeedProcessor(PostRepository(db_session)).reextract_post(
            MagicMock(), post_id
        )

    extract.assert_called_once_with("https://example.com/article")
    db_session.expire_all()
    saved = PostRepository(db_session).get_post_by_id(post_id)
    assert saved.content == "Original body"
    assert saved.post_revision == 1
    assert (saved.crawled_at, saved.parsed_at) == original_times
    assert publish.call_args.kwargs["post_revision"] == 1
    assert publish.call_args.kwargs["content"] == "Original body"


def test_failed_reextract_preserves_post_and_does_not_publish(
    db_session: Session, stored_post: Post
) -> None:
    parsed_at = stored_post.parsed_at
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"error": "Blocked"},
        ),
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        assert not FeedProcessor(PostRepository(db_session)).reextract_post(
            MagicMock(), stored_post.post_id
        )
    db_session.expire_all()
    assert stored_post.content == "Original body"
    assert stored_post.parsed_at == parsed_at
    assert stored_post.post_revision == 1
    publish.assert_not_called()


def test_reextract_publish_failure_propagates(
    db_session: Session, stored_post: Post
) -> None:
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"content": "New body"},
        ),
        patch(
            "src.services.feed_processor.post_publisher.publish_post_parsed_success",
            side_effect=pika.exceptions.UnroutableError([]),
        ),
        pytest.raises(pika.exceptions.UnroutableError),
    ):
        FeedProcessor(PostRepository(db_session)).reextract_post(
            MagicMock(), stored_post.post_id
        )

    db_session.expire_all()
    saved = PostRepository(db_session).get_post_by_id(stored_post.post_id)
    assert saved.content == "New body"
    assert saved.post_revision == 2


def _dlq_channel(body: bytes) -> MagicMock:
    channel = MagicMock(is_open=True)
    channel.basic_get.return_value = (
        MagicMock(delivery_tag=9),
        MagicMock(),
        body,
    )
    return channel


def test_feed_replay_publishes_original_before_acknowledgement() -> None:
    body = b'{"event_id":"failed","event_type":"feed.raw_fetched.v1","correlation_id":"original"}'
    channel = _dlq_channel(body)
    assert replay_failed_feed(channel, "failed")
    assert channel.basic_publish.call_args.kwargs["body"] == body
    assert (
        channel.basic_publish.call_args.kwargs["properties"]
        is channel.basic_get.return_value[1]
    )
    assert channel.basic_publish.call_args.kwargs["mandatory"]
    calls = [call[0] for call in channel.method_calls]
    assert calls.index("basic_publish") < calls.index("basic_ack")
    channel.basic_nack.assert_not_called()


def test_feed_replay_requeues_unexpected_message() -> None:
    body = b'{"event_id":"other"}'
    channel = _dlq_channel(body)
    with pytest.raises(ValueError):
        replay_failed_feed(channel, "failed")
    channel.basic_publish.assert_not_called()
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=9, requeue=True)


def test_feed_replay_preserves_message_when_publication_fails() -> None:
    channel = _dlq_channel(
        b'{"event_id":"failed","event_type":"feed.raw_fetched.v1"}'
    )
    channel.basic_publish.side_effect = pika.exceptions.UnroutableError([])
    with pytest.raises(pika.exceptions.UnroutableError):
        replay_failed_feed(channel, "failed")
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(delivery_tag=9, requeue=True)

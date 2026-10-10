from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pika
import pytest
from sqlalchemy.orm import Session

from src.models.post import Post
from src.repositories.post_repository import PostRepository
from src.scripts.replay_failed_feed import replay_failed_feed
from src.scripts import reextract_post as reextract_command
from src.scripts import replay_failed_feed as replay_command
from src.services.source_processor import SourceProcessorService


@pytest.fixture
def stored_post(db_session: Session) -> Post:
    snapshot = PostRepository(db_session).create_post(
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
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        assert SourceProcessorService(db_session).reextract_post(
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
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        assert SourceProcessorService(db_session).reextract_post(
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
            "src.services.source_processor.post_publisher.publish_post_parsed_success"
        ) as publish,
    ):
        assert not SourceProcessorService(db_session).reextract_post(
            MagicMock(), stored_post.post_id
        )
    db_session.expire_all()
    assert stored_post.content == "Original body"
    assert stored_post.parsed_at == parsed_at
    assert stored_post.post_revision == 1
    publish.assert_not_called()


def test_unknown_post_is_not_extracted(db_session: Session) -> None:
    with (
        patch("src.adapters.content_extractor.extract_article") as extract,
        pytest.raises(ValueError, match="Post not found"),
    ):
        SourceProcessorService(db_session).reextract_post(MagicMock(), uuid4())
    extract.assert_not_called()


def test_reextract_publish_failure_propagates(
    db_session: Session, stored_post: Post
) -> None:
    with (
        patch(
            "src.adapters.content_extractor.extract_article",
            return_value={"content": "New body"},
        ),
        patch(
            "src.services.source_processor.post_publisher.publish_post_parsed_success",
            side_effect=pika.exceptions.UnroutableError([]),
        ),
        pytest.raises(pika.exceptions.UnroutableError),
    ):
        SourceProcessorService(db_session).reextract_post(
            MagicMock(), stored_post.post_id
        )


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
    assert channel.basic_publish.call_args.kwargs["mandatory"]
    calls = [call[0] for call in channel.method_calls]
    assert calls.index("basic_publish") < calls.index("basic_ack")
    channel.basic_nack.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [
        b'{"event_id":"other"}',
        b'{"event_id":"failed","event_type":"other"}',
    ],
)
def test_feed_replay_requeues_unexpected_message(body: bytes) -> None:
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


def test_empty_dlq_is_not_published() -> None:
    channel = MagicMock()
    channel.basic_get.return_value = (None, None, None)
    assert not replay_failed_feed(channel, "failed")
    channel.basic_publish.assert_not_called()


@pytest.mark.parametrize("succeeded, expected_exit", [(True, 0), (False, 1)])
def test_reextract_command_closes_connection(
    succeeded: bool, expected_exit: int, capsys: pytest.CaptureFixture[str]
) -> None:
    channel = MagicMock()
    with (
        patch(
            "sys.argv",
            ["reextract_post", "00000000-0000-0000-0000-000000000001"],
        ),
        patch.object(
            reextract_command,
            "create_replay_publisher_channel",
            return_value=channel,
        ),
        patch.object(reextract_command, "SessionLocal") as sessions,
        patch.object(reextract_command, "SourceProcessorService") as service,
    ):
        service.return_value.reextract_post.return_value = succeeded
        assert reextract_command.main() == expected_exit
        if succeeded:
            assert capsys.readouterr().out == (
                "Post snapshot published after re-extraction.\n"
            )
        service.return_value.reextract_post.assert_called_once_with(
            channel, UUID("00000000-0000-0000-0000-000000000001")
        )
        sessions.return_value.__exit__.assert_called_once()
    channel.connection.close.assert_called_once()


@pytest.mark.parametrize("succeeded, expected_exit", [(True, 0), (False, 1)])
def test_feed_replay_command_enables_confirms(
    succeeded: bool, expected_exit: int
) -> None:
    with (
        patch("sys.argv", ["replay_failed_feed", "event-id"]),
        patch.object(replay_command.pika, "BlockingConnection") as connect,
        patch.object(
            replay_command, "replay_failed_feed", return_value=succeeded
        ) as replay,
    ):
        channel = (
            connect.return_value.__enter__.return_value.channel.return_value
        )
        assert replay_command.main() == expected_exit
        channel.confirm_delivery.assert_called_once()
        replay.assert_called_once_with(channel, "event-id")
        connect.return_value.__exit__.assert_called_once()

import json
from unittest.mock import MagicMock

from src.services import event_publisher


def _extract_publish_args(channel: MagicMock) -> tuple[str, bytes]:
    kwargs = channel.basic_publish.call_args.kwargs
    return kwargs["routing_key"], kwargs["body"]


def test_publish_post_parsed_success_emits_content_body() -> None:
    channel = MagicMock()

    event_publisher.publish_post_parsed_success(
        channel,
        post_id="a1",
        source_id="s1",
        item_guid="g1",
        url="https://example.com/a1",
        title="Title",
        correlation_id="corr-123",
        content="Full body",
        content_length=9,
        description="A short description",
        published_at="2026-05-05T00:00:00+00:00",
        image_url="https://example.com/images/a1.png",
    )

    routing_key, body = _extract_publish_args(channel)
    envelope = json.loads(body.decode())

    assert routing_key == "post.parsed.v1"
    assert envelope["correlation_id"] == "corr-123"
    assert envelope["payload"]["content"] == "Full body"
    assert envelope["payload"]["content_length"] == 9
    assert (
        envelope["payload"]["description"] == "A short description"
    )
    assert (
        envelope["payload"]["image_url"]
        == "https://example.com/images/a1.png"
    )

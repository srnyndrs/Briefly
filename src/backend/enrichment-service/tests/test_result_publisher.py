import json
from unittest.mock import MagicMock

import pytest

from src.adapters.result_publisher import publish_result
from src.config.settings import settings


def test_publishes_persistent_mandatory_result() -> None:
    channel = MagicMock()
    event = {"event_id": "fixed-id", "event_type": "post.enriched.v1"}

    publish_result(channel, event)

    kwargs = channel.basic_publish.call_args.kwargs
    assert kwargs["exchange"] == settings.result_exchange
    assert kwargs["routing_key"] == "post.enriched.v1"
    assert kwargs["mandatory"] is True
    assert json.loads(kwargs["body"]) == event
    assert kwargs["properties"].delivery_mode == 2


def test_unconfirmed_result_raises() -> None:
    channel = MagicMock()
    channel.basic_publish.return_value = False

    with pytest.raises(RuntimeError, match="not confirmed"):
        publish_result(channel, {"event_id": "fixed-id"})

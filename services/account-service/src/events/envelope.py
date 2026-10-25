from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

_PRODUCER_NAME = "account-service"


def build_envelope(
    *,
    event_type: str,
    partition_key: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
    event_id: str | None = None,
    occurred_at: str | None = None,
) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "event_id": event_id if event_id is not None else str(uuid4()),
        "event_type": event_type,
        "schema_version": 1,
        "occurred_at": (
            occurred_at
            if occurred_at is not None
            else datetime.now(UTC).isoformat()
        ),
        "producer": _PRODUCER_NAME,
        "partition_key": partition_key,
        "payload": payload,
    }

    if correlation_id is not None:
        envelope["correlation_id"] = correlation_id
        envelope["trace"] = {
            "trace_id": uuid4().hex,
            "span_id": uuid4().hex[:16],
        }

    return envelope

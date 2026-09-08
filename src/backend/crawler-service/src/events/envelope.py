import uuid
from datetime import datetime, timezone
from typing import Any


def build_envelope(
    *,
    event_type: str,
    partition_key: str,
    payload: dict[str, Any],
    correlation_id: str,
    trace_id: str | None = None,
    span_id: str | None = None,
    producer: str = "crawler-service",
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "schema_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "producer": producer,
        "correlation_id": correlation_id,
        "partition_key": partition_key,
        "trace": {
            "trace_id": trace_id or uuid.uuid4().hex,
            "span_id": span_id or uuid.uuid4().hex[:16],
        },
        "payload": payload,
    }

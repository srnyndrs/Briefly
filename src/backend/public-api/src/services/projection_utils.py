from datetime import datetime


def parse_dt(value: str | None) -> datetime | None:
    """Parse ISO 8601 datetime string with optional Z suffix."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

import json

from src.app import scrub_sentry_event


def test_scrubber_keeps_exception_locations_without_account_data() -> None:
    event = {
        key: {"value": "sensitive-account-data"}
        for key in (
            "request",
            "breadcrumbs",
            "extra",
            "contexts",
            "user",
            "logentry",
        )
    }
    event["exception"] = {
        "values": [
            {
                "type": "RuntimeError",
                "value": "sensitive-account-data",
                "stacktrace": {
                    "frames": [
                        {
                            "filename": "account_service.py",
                            "lineno": 42,
                            "vars": {"password": "sensitive-account-data"},
                            "context_line": "sensitive-account-data",
                            "pre_context": ["sensitive-account-data"],
                            "post_context": ["sensitive-account-data"],
                        }
                    ]
                },
            }
        ]
    }
    scrubbed = scrub_sentry_event(event, {})
    assert "sensitive-account-data" not in json.dumps(scrubbed)
    exception = scrubbed["exception"]["values"][0]
    assert exception["type"] == "RuntimeError"
    assert exception["stacktrace"]["frames"] == [
        {"filename": "account_service.py", "lineno": 42}
    ]

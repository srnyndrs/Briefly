import logging
from unittest.mock import Mock

from src.adapters.http_client import FetchHeaders, RequestsHttpClient


def test_response_diagnostics_omit_secrets_and_bound_validators(
    monkeypatch, caplog
):
    body = "<feed>distinctive-private-xml</feed>"
    validator = "tag\n" + "x" * 1000
    response = Mock(status_code=200, text=body, headers={"ETag": validator})
    monkeypatch.setattr(
        "src.adapters.http_client.requests.get", Mock(return_value=response)
    )

    with caplog.at_level(logging.INFO, logger="src.adapters.http_client"):
        RequestsHttpClient.fetch(
            "https://example.com/feed?token=query-secret-value", FetchHeaders()
        )

    assert "host=example.com" in caplog.text
    assert "status=200" in caplog.text
    assert "query-secret-value" not in caplog.text
    assert body not in caplog.text
    assert "tag\\n" in caplog.text
    assert "tag\n" not in caplog.text
    assert validator not in caplog.text
    assert "x" * 1000 not in caplog.text
    assert "..." in caplog.text

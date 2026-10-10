import logging
from unittest.mock import Mock

import pytest

from src.adapters.http_client import FetchHeaders, RequestsHttpClient


@pytest.mark.parametrize(
    ("headers", "expected_request_headers"),
    [
        (
            FetchHeaders(etag='"saved"', last_modified="saved-date"),
            {"If-None-Match": '"saved"', "If-Modified-Since": "saved-date"},
        ),
        (FetchHeaders(), {}),
    ],
)
def test_fetch_sends_saved_validators_and_logs_actual_response(
    monkeypatch, caplog, headers, expected_request_headers
):
    response = Mock(status_code=200, text="<feed/>")
    response.headers = {"ETag": '"fresh"', "Last-Modified": "fresh-date"}
    response.raise_for_status.return_value = None
    get = Mock(return_value=response)
    monkeypatch.setattr("src.adapters.http_client.requests.get", get)

    with caplog.at_level(logging.INFO, logger="src.adapters.http_client"):
        result = RequestsHttpClient.fetch("https://example.com/feed?secret=x", headers)

    sent = get.call_args.kwargs["headers"]
    assert {key: sent[key] for key in expected_request_headers} == expected_request_headers
    assert result.body == "<feed/>"
    assert result.etag == '"fresh"'
    assert result.last_modified == "fresh-date"
    assert "host=example.com" in caplog.text
    assert "status=200" in caplog.text
    assert "secret" not in caplog.text
    assert "fresh-date" in caplog.text
    assert "saved-date" in caplog.text if expected_request_headers else "<absent>" in caplog.text


def test_fetch_logs_response_headers_before_304_return(monkeypatch, caplog):
    response = Mock(status_code=304, text="")
    response.headers = {"ETag": '"response-etag"', "Last-Modified": "response-date"}
    response.raise_for_status.return_value = None
    get = Mock(return_value=response)
    monkeypatch.setattr("src.adapters.http_client.requests.get", get)

    with caplog.at_level(logging.INFO, logger="src.adapters.http_client"):
        result = RequestsHttpClient.fetch(
            "https://example.com/feed",
            FetchHeaders(etag='"saved-etag"', last_modified="saved-date"),
        )

    assert result.status_code == 304
    assert result.etag == '"saved-etag"'
    assert "response-etag" in caplog.text
    assert "response-date" in caplog.text


def test_validator_log_values_are_escaped_and_bounded(monkeypatch, caplog):
    response = Mock(status_code=200, text="<feed/>")
    response.headers = {"ETag": "tag\n" + "x" * 1000}
    response.raise_for_status.return_value = None
    monkeypatch.setattr("src.adapters.http_client.requests.get", Mock(return_value=response))

    with caplog.at_level(logging.INFO, logger="src.adapters.http_client"):
        RequestsHttpClient.fetch("https://example.com/feed", FetchHeaders())

    message = caplog.records[0].getMessage()
    assert "\\n" in message
    assert len(message) < 500

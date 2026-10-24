import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from src.adapters.gemini_provider import GeminiProvider
from src.services.classification import ArticleInput
from src.services.provider import ProviderError, instructions


@pytest.fixture(autouse=True)
def block_real_requests(monkeypatch) -> None:
    def fail(*_, **__):
        raise AssertionError("Tests must not call the real Gemini API")

    monkeypatch.setattr("src.adapters.gemini_provider.urlopen", fail)


class FakeResponse:
    def __init__(self, data: object) -> None:
        self.stream = BytesIO(json.dumps(data).encode())

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        self.stream.close()

    def read(self, size: int) -> bytes:
        return self.stream.read(size)


def gemini_response(content: str = '{"category_ids":["science"]}') -> dict:
    return {
        "modelVersion": "test-model-v2",
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {"text": "Internal thought", "thought": True},
                        {"text": content},
                    ]
                },
            }
        ],
        "usageMetadata": {"promptTokenCount": 42, "candidatesTokenCount": 8},
    }


def make_provider() -> GeminiProvider:
    return GeminiProvider(
        model="test-model",
        instructions=instructions([]),
        api_key="test-key",
        timeout=4,
    )


def test_gemini_sends_shared_prompt_and_parses_result(monkeypatch) -> None:
    requests = []

    def fake_open(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(
            gemini_response('{"category_ids":["health","science"]}')
        )

    monkeypatch.setattr("src.adapters.gemini_provider.urlopen", fake_open)
    result = make_provider()(ArticleInput(title="A study", language="en"))
    assert result.category_ids == ("science", "health")
    assert result.model == "test-model-v2"
    assert (result.input_tokens, result.output_tokens) == (42, 8)
    request, timeout = requests[0]
    payload = json.loads(request.data)
    assert timeout == 4
    assert request.full_url.endswith("/test-model:generateContent")
    assert request.get_header("X-goog-api-key") == "test-key"
    assert "test-key" not in request.full_url
    assert payload["systemInstruction"]["parts"][0]["text"] == instructions([])
    assert (
        json.loads(payload["contents"][0]["parts"][0]["text"])["title"] == "A study"
    )
    config = payload["generationConfig"]
    assert config["temperature"] == 0
    assert config["maxOutputTokens"] == 128
    assert config["responseFormat"]["text"]["mimeType"] == "APPLICATION_JSON"
    assert (
        config["responseFormat"]["text"]["schema"]["properties"]["category_ids"][
            "maxItems"
        ]
        == 2
    )


@pytest.mark.parametrize(
    "content",
    [
        '{"category_ids":["unknown"]}',
        "not JSON",
    ],
)
def test_gemini_rejects_invalid_category(monkeypatch, content: str) -> None:
    monkeypatch.setattr(
        "src.adapters.gemini_provider.urlopen",
        lambda *_, **__: FakeResponse(gemini_response(content)),
    )
    with pytest.raises(ValueError):
        make_provider()(ArticleInput(title="A study"))


@pytest.mark.parametrize(
    "response",
    [
        {"candidates": [{"finishReason": "MAX_TOKENS"}]},
        {"padding": "x" * 16_384},
    ],
)
def test_gemini_rejects_missing_incomplete_or_large_result(
    monkeypatch, response
) -> None:
    monkeypatch.setattr(
        "src.adapters.gemini_provider.urlopen",
        lambda *_, **__: FakeResponse(response),
    )
    with pytest.raises(ValueError):
        make_provider()(ArticleInput(title="A study"))


def test_gemini_accepts_abstention_without_usage(monkeypatch) -> None:
    response = gemini_response('{"category_ids":[]}')
    del response["usageMetadata"]
    del response["modelVersion"]
    monkeypatch.setattr(
        "src.adapters.gemini_provider.urlopen",
        lambda *_, **__: FakeResponse(response),
    )
    result = make_provider()(ArticleInput(title="Unclear"))
    assert result.category_ids == ()
    assert result.model == "test-model"
    assert result.input_tokens is None
    assert result.output_tokens is None


def test_gemini_http_error_is_bounded_and_redacts_key(monkeypatch) -> None:
    body = b'{"error":{"status":"RESOURCE_EXHAUSTED","message":"test-key quota"}}'

    def fail(*_, **__):
        raise HTTPError("https://example.test", 429, "quota", {}, BytesIO(body))

    monkeypatch.setattr("src.adapters.gemini_provider.urlopen", fail)
    with pytest.raises(ProviderError) as error:
        make_provider()(ArticleInput(title="A study"))
    assert "HTTP 429" in str(error.value)
    assert "test-key" not in str(error.value)
    assert len(str(error.value)) <= 1000

import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from src.adapters.ollama_provider import OllamaProvider, ollama_category_schema
from src.services.classification import ArticleInput
from src.services.provider import ProviderError, instructions


class FakeResponse:
    def __init__(self, data: object) -> None:
        self.stream = BytesIO(
            data if isinstance(data, bytes) else json.dumps(data).encode()
        )

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        self.stream.close()

    def read(self, size: int) -> bytes:
        return self.stream.read(size)


@pytest.fixture(autouse=True)
def block_real_requests(monkeypatch) -> None:
    def fail(*_, **__):
        raise AssertionError("Tests must not call a real Ollama server")

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fail)


def ollama_response(content: str = '{"category_ids":["science"]}') -> dict:
    return {
        "model": "test-model:resolved",
        "message": {
            "role": "assistant",
            "content": content,
            "thinking": "ignore",
        },
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 42,
        "eval_count": 8,
    }


def make_provider() -> OllamaProvider:
    return OllamaProvider(
        model="test-model",
        instructions=instructions([]),
        base_url="http://localhost:11434/",
        timeout=4,
    )


def test_resolves_installed_model_digest(monkeypatch) -> None:
    def fake_open(request, *, timeout):
        assert request.full_url == "http://localhost:11434/api/tags"
        assert request.get_method() == "GET"
        assert timeout == 4
        return FakeResponse(
            {"models": [{"name": "test-model:latest", "digest": "sha256:one"}]}
        )

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fake_open)
    assert make_provider().model_digest() == "sha256:one"


def test_model_resolution_fails_before_consumption(monkeypatch) -> None:
    listing = {"models": []}
    monkeypatch.setattr(
        "src.adapters.ollama_provider.urlopen",
        lambda *_, **__: FakeResponse(listing),
    )
    with pytest.raises(ProviderError):
        make_provider().model_digest()


def test_ollama_sends_shared_schema_and_parses_answer(monkeypatch) -> None:
    requests = []

    def fake_open(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(ollama_response())

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fake_open)
    result = make_provider()(ArticleInput(title="A study", language="en"))
    assert result.category_ids == ("science",)
    assert result.model == "test-model:resolved"
    assert (result.input_tokens, result.output_tokens) == (42, 8)

    request, timeout = requests[0]
    payload = json.loads(request.data)
    assert timeout == 4
    assert request.full_url == "http://localhost:11434/api/chat"
    assert request.get_method() == "POST"
    assert request.get_header("Content-type") == "application/json"
    assert payload["model"] == "test-model"
    assert payload["messages"][0] == {
        "role": "system",
        "content": instructions([]),
    }
    assert payload["messages"][1]["role"] == "user"
    assert json.loads(payload["messages"][1]["content"])["title"] == "A study"
    assert payload["stream"] is False
    assert payload["format"] == ollama_category_schema()
    alternatives = ollama_category_schema()["properties"]["category_ids"][
        "oneOf"
    ]
    assert "other" not in alternatives[0]["items"]["enum"]
    assert alternatives[1]["items"]["enum"] == ["other"]
    assert alternatives[1]["minItems"] == alternatives[1]["maxItems"] == 1

    assert payload["options"] == {"temperature": 0, "num_predict": 128}


def test_ollama_accepts_abstention_without_usage_or_response_model(
    monkeypatch,
) -> None:
    response = ollama_response('{"category_ids":[]}')
    del response["model"]
    del response["prompt_eval_count"]
    del response["eval_count"]
    monkeypatch.setattr(
        "src.adapters.ollama_provider.urlopen",
        lambda *_, **__: FakeResponse(response),
    )
    result = make_provider()(ArticleInput(title="Unclear"))
    assert result.category_ids == ()
    assert result.model == "test-model"
    assert result.input_tokens is None
    assert result.output_tokens is None


@pytest.mark.parametrize(
    "response",
    [
        b"not JSON",
        {**ollama_response(), "done": False},
        ollama_response('{"category_ids":["unknown"]}'),
        {"padding": "x" * 16_384},
    ],
)
def test_ollama_rejects_invalid_or_incomplete_response(
    monkeypatch, response
) -> None:
    monkeypatch.setattr(
        "src.adapters.ollama_provider.urlopen",
        lambda *_, **__: FakeResponse(response),
    )
    with pytest.raises(ValueError):
        make_provider()(ArticleInput(title="A study"))


def test_ollama_http_missing_model_has_bounded_safe_detail(monkeypatch) -> None:
    def fail(*_, **__):
        raise HTTPError(
            "http://localhost:11434/api/chat",
            404,
            "not found",
            {},
            BytesIO(b'{"error":"private server detail"}'),
        )

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fail)
    with pytest.raises(ProviderError) as error:
        make_provider()(ArticleInput(title="A study"))
    assert "HTTP 404" in str(error.value)
    assert "private server detail" not in str(error.value)
    assert len(str(error.value)) <= 1_000


def test_ollama_timeout_has_safe_detail(monkeypatch) -> None:
    failure = TimeoutError("secret timeout detail")

    def fail(*_, **__):
        raise failure

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fail)
    with pytest.raises(
        ProviderError, match="Ollama request timed out"
    ) as error:
        make_provider()(ArticleInput(title="A study"))
    assert "secret" not in str(error.value)

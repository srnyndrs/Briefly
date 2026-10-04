import json
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from src.adapters.ollama_provider import OllamaProvider
from src.config.settings import settings
from src.scripts.evaluate_providers import main
from src.services.classification import ArticleInput
from src.services.provider import ProviderError, category_schema, instructions


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


def ollama_response(content: str = '{"category_id":"science"}') -> dict:
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


def test_ollama_sends_shared_schema_and_parses_answer(monkeypatch) -> None:
    requests = []

    def fake_open(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(ollama_response())

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fake_open)
    result = make_provider()(ArticleInput(title="A study", language="en"))
    assert result.category_id == "science"
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
    assert payload["format"] == category_schema()
    assert payload["options"] == {"temperature": 0, "num_predict": 128}


def test_ollama_accepts_abstention_without_usage_or_response_model(
    monkeypatch,
) -> None:
    response = ollama_response('{"category_id":null}')
    del response["model"]
    del response["prompt_eval_count"]
    del response["eval_count"]
    monkeypatch.setattr(
        "src.adapters.ollama_provider.urlopen",
        lambda *_, **__: FakeResponse(response),
    )
    result = make_provider()(ArticleInput(title="Unclear"))
    assert result.category_id is None
    assert result.model == "test-model"
    assert result.input_tokens is None
    assert result.output_tokens is None


@pytest.mark.parametrize(
    "response",
    [
        b"not JSON",
        [],
        {"message": {"content": '{"category_id":"science"}'}, "done": False},
        {**ollama_response(), "done": False},
        {**ollama_response(), "done": 1},
        {**ollama_response(), "done_reason": "length"},
        {**ollama_response(), "done_reason": None},
        {**ollama_response(), "message": None},
        {
            **ollama_response(),
            "message": {"thinking": '{"category_id":"science"}', "content": ""},
        },
        ollama_response("not JSON"),
        ollama_response('{"category_id":"unknown"}'),
        ollama_response('{"category_id":"science","extra":true}'),
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


@pytest.mark.parametrize("tokens", [-1, True, "42"])
def test_ollama_rejects_invalid_usage(monkeypatch, tokens) -> None:
    response = ollama_response()
    response["eval_count"] = tokens
    monkeypatch.setattr(
        "src.adapters.ollama_provider.urlopen",
        lambda *_, **__: FakeResponse(response),
    )
    with pytest.raises(ValueError, match="token usage"):
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
    assert "pull it before evaluation" in str(error.value)
    assert "private server detail" not in str(error.value)
    assert len(str(error.value)) <= 1_000


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("secret timeout detail"),
        URLError(TimeoutError("timed out")),
    ],
)
def test_ollama_timeout_has_safe_detail(monkeypatch, failure) -> None:
    def fail(*_, **__):
        raise failure

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fail)
    with pytest.raises(
        ProviderError, match="Ollama request timed out"
    ) as error:
        make_provider()(ArticleInput(title="A study"))
    assert "secret" not in str(error.value)


def test_ollama_evaluation_needs_no_gemini_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"one","title":"Study","category_id":"science"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "ollama_base_url", "http://localhost:11434")
    monkeypatch.setattr(
        "src.adapters.ollama_provider.urlopen",
        lambda *_, **__: FakeResponse(ollama_response()),
    )
    assert (
        main(
            [
                "--provider",
                "ollama",
                "--dataset",
                str(dataset),
                "--max-calls",
                "1",
                "--model",
                "test-model",
            ]
        )
        == 0
    )
    row = json.loads(capsys.readouterr().out)
    assert row["provider"] == "ollama"
    assert row["model"] == "test-model:resolved"
    assert row["actual"] == "science"
    assert row["correct"] is True

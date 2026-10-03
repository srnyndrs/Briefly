import json
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from src.adapters.gemini_provider import GeminiProvider
from src.adapters.providers import PROVIDERS
from src.config.settings import settings
from src.scripts.evaluate_providers import (
    evaluate_articles,
    load_articles,
    main,
)
from src.services.classification import ArticleInput
from src.services.provider import ProviderError, ProviderResult, instructions


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


def gemini_response(content: str = '{"category_id":"science"}') -> dict:
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
        return FakeResponse(gemini_response())

    monkeypatch.setattr("src.adapters.gemini_provider.urlopen", fake_open)
    result = make_provider()(ArticleInput(title="A study", language="en"))
    assert result.category_id == "science"
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
        json.loads(payload["contents"][0]["parts"][0]["text"])["title"]
        == "A study"
    )
    config = payload["generationConfig"]
    assert config["maxOutputTokens"] == 128
    assert config["responseFormat"]["text"]["mimeType"] == "application/json"
    assert (
        config["responseFormat"]["text"]["schema"]["properties"]["category_id"][
            "enum"
        ][-1]
        is None
    )


@pytest.mark.parametrize(
    "content",
    [
        '{"category_id":"unknown"}',
        '{"category_id":"science","extra":true}',
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
        {},
        {"candidates": []},
        {"candidates": [{"finishReason": "MAX_TOKENS"}]},
        {"candidates": [{"finishReason": "SAFETY"}]},
        {"candidates": [{"finishReason": "STOP", "content": {"parts": []}}]},
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
    response = gemini_response('{"category_id":null}')
    del response["usageMetadata"]
    del response["modelVersion"]
    monkeypatch.setattr(
        "src.adapters.gemini_provider.urlopen",
        lambda *_, **__: FakeResponse(response),
    )
    result = make_provider()(ArticleInput(title="Unclear"))
    assert result.category_id is None
    assert result.model == "test-model"
    assert result.input_tokens is None
    assert result.output_tokens is None


@pytest.mark.parametrize("tokens", [-1, True, "42"])
def test_gemini_rejects_invalid_usage(monkeypatch, tokens) -> None:
    response = gemini_response()
    response["usageMetadata"]["promptTokenCount"] = tokens
    monkeypatch.setattr(
        "src.adapters.gemini_provider.urlopen",
        lambda *_, **__: FakeResponse(response),
    )
    with pytest.raises(ValueError, match="token usage"):
        make_provider()(ArticleInput(title="A study"))


def test_gemini_propagates_transport_failure(monkeypatch) -> None:
    def fail(*_, **__):
        raise URLError("offline")

    monkeypatch.setattr("src.adapters.gemini_provider.urlopen", fail)
    with pytest.raises(URLError):
        make_provider()(ArticleInput(title="A study"))


@pytest.mark.parametrize(
    "body",
    [
        b'{"error":{"status":"RESOURCE_EXHAUSTED","message":"test-key quota"}}',
        b"not JSON",
    ],
)
def test_gemini_http_error_is_bounded_and_redacts_key(
    monkeypatch, body
) -> None:
    def fail(*_, **__):
        raise HTTPError("https://example.test", 429, "quota", {}, BytesIO(body))

    monkeypatch.setattr("src.adapters.gemini_provider.urlopen", fail)
    with pytest.raises(ProviderError) as error:
        make_provider()(ArticleInput(title="A study"))
    assert "HTTP 429" in str(error.value)
    assert "test-key" not in str(error.value)
    assert len(str(error.value)) <= 1000


def test_evaluation_checks_call_cap_before_first_request(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"one","title":"Study","category_id":"science"}\n'
        '{"id":"two","title":"Match","category_id":"sports"}\n',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        main(
            [
                "--dataset",
                str(dataset),
                "--max-calls",
                "1",
                "--model",
                "test",
            ]
        )


def test_evaluation_rejects_example_overlap(tmp_path: Path) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"same","title":"Study","category_id":"science"}\n',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        main(
            [
                "--dataset",
                str(dataset),
                "--examples",
                str(dataset),
                "--max-calls",
                "1",
                "--model",
                "test",
            ]
        )


def test_examples_file_has_valid_labels() -> None:
    path = Path(__file__).resolve().parents[1] / "examples" / "categories.jsonl"
    assert len(load_articles(path)) == 5


def test_evaluation_records_one_gemini_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch,
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"article-1","title":"Medicine","category_id":"health"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(
        "src.adapters.gemini_provider.urlopen",
        lambda *_, **__: FakeResponse(
            gemini_response('{"category_id":"health"}')
        ),
    )
    assert (
        main(
            [
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
    result = json.loads(capsys.readouterr().out)
    assert result["id"] == "article-1"
    assert result["correct"] is True
    assert result["provider"] == "gemini"
    assert result["model"] == "test-model-v2"
    assert "Medicine" not in result.values()


def test_evaluation_records_failure_and_waits_between_calls(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch,
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"one","title":"Study","category_id":"science"}\n'
        '{"id":"two","title":"Match","category_id":"sports"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    waits = []
    monkeypatch.setattr(
        "src.scripts.evaluate_providers.time.sleep", waits.append
    )

    def fail(*_, **__):
        raise URLError("offline")

    monkeypatch.setattr("src.adapters.gemini_provider.urlopen", fail)
    assert (
        main(
            [
                "--dataset",
                str(dataset),
                "--max-calls",
                "2",
                "--model",
                "test-model",
                "--request-interval",
                "5",
            ]
        )
        == 0
    )
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(rows) == 2
    assert all(
        row["error"] == "URLError" and not row["correct"] for row in rows
    )
    assert waits == [5]


def test_evaluation_requires_key(tmp_path: Path, monkeypatch) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"one","title":"Study","category_id":"science"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "gemini_api_key", None)
    with pytest.raises(SystemExit):
        main(["--dataset", str(dataset), "--max-calls", "1", "--model", "test"])


def test_evaluation_rejects_unknown_provider_before_construction(
    tmp_path: Path, monkeypatch
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"one","title":"Study","category_id":"science"}\n',
        encoding="utf-8",
    )

    def fail(**_):
        raise AssertionError("No provider should be constructed")

    monkeypatch.setitem(PROVIDERS, "gemini", fail)
    with pytest.raises(SystemExit):
        main(
            [
                "--provider",
                "unknown",
                "--dataset",
                str(dataset),
                "--max-calls",
                "1",
                "--model",
                "test",
            ]
        )


def test_evaluation_selects_temporary_provider_from_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"one","title":"Study","category_id":"science"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "gemini_api_key", None)
    constructed = []
    called = []

    def create_fake(*, model: str, instructions: str, timeout: float):
        constructed.append((model, instructions, timeout))

        def classify(article: ArticleInput) -> ProviderResult:
            called.append(article.title)
            return ProviderResult("science", model)

        return classify

    monkeypatch.setitem(PROVIDERS, "fake", create_fake)
    assert (
        main(
            [
                "--provider",
                "fake",
                "--dataset",
                str(dataset),
                "--max-calls",
                "1",
                "--model",
                "fake-model",
                "--timeout",
                "7",
            ]
        )
        == 0
    )
    row = json.loads(capsys.readouterr().out)
    assert row["provider"] == "fake"
    assert row["model"] == "fake-model"
    assert row["correct"] is True
    assert called == ["Study"]
    assert constructed[0][0] == "fake-model"
    assert "Classify the article" in constructed[0][1]
    assert constructed[0][2] == 7


def test_evaluation_accepts_fake_provider_and_continues_after_failures(
    capsys: pytest.CaptureFixture[str], monkeypatch
) -> None:
    articles = [
        ("success", ArticleInput(title="Study"), "science"),
        ("abstain", ArticleInput(title="Unclear"), None),
        ("provider-error", ArticleInput(title="Broken"), "sports"),
        ("unexpected", ArticleInput(title="Secret"), "health"),
        ("after-errors", ArticleInput(title="Match"), "sports"),
    ]
    waits = []
    calls = []
    monkeypatch.setattr(
        "src.scripts.evaluate_providers.time.sleep", waits.append
    )

    def fake_provider(article: ArticleInput) -> ProviderResult:
        calls.append(article.title)
        if article.title == "Broken":
            raise ProviderError("safe detail" + "x" * 1_000)
        if article.title == "Secret":
            raise RuntimeError("private detail")
        category = {
            "Study": "science",
            "Unclear": None,
            "Match": "sports",
        }[article.title]
        return ProviderResult(category, "fake-model-v2", 4, 2)

    evaluate_articles(fake_provider, "fake", "fake-model", articles, 0.5)
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert calls == [article.title for _, article, _ in articles]
    assert waits == [0.5] * 4
    assert [row["id"] for row in rows] == [item[0] for item in articles]
    assert all(row["provider"] == "fake" for row in rows)
    assert rows[0]["actual"] == "science" and rows[0]["correct"] is True
    assert rows[0]["model"] == "fake-model-v2"
    assert rows[1]["actual"] is None and rows[1]["correct"] is True
    assert rows[2]["error"] == "ProviderError"
    assert len(rows[2]["error_detail"]) == 1_000
    assert rows[2]["model"] == "fake-model"
    assert rows[3]["error"] == "RuntimeError"
    assert rows[3]["error_detail"] is None
    assert rows[4]["correct"] is True

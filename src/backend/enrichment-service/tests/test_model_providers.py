import json
import sys
from io import BytesIO
from pathlib import Path
from urllib.error import URLError

import pytest

from src.adapters.model_providers import ChatHttpProvider, CliProvider
from src.scripts.evaluate_providers import load_articles, main
from src.services.classification import ArticleInput
from src.services.provider import instructions


class FakeResponse:
    def __init__(self, data: object) -> None:
        self.stream = BytesIO(json.dumps(data).encode())

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        self.stream.close()

    def read(self, size: int) -> bytes:
        return self.stream.read(size)


def test_http_adapter_sends_shared_prompt_and_parses_result(
    monkeypatch,
) -> None:
    requests = []

    def fake_open(request, *, timeout):
        requests.append((request, timeout))
        return FakeResponse(
            {
                "model": "test-model-v2",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"category_id":"science"}'},
                    }
                ],
                "usage": {"prompt_tokens": 42, "completion_tokens": 8},
            }
        )

    monkeypatch.setattr("src.adapters.model_providers.urlopen", fake_open)
    provider = ChatHttpProvider(
        url="https://example.test/chat/completions",
        model="test-model",
        instructions=instructions([]),
        api_key="test-key",
        timeout=4,
        response_format="schema",
    )
    result = provider(ArticleInput(title="A study", language="en"))

    assert result.category_id == "science"
    assert result.model == "test-model-v2"
    assert (result.input_tokens, result.output_tokens) == (42, 8)
    request, timeout = requests[0]
    payload = json.loads(request.data)
    assert timeout == 4
    assert request.get_header("Authorization") == "Bearer test-key"
    assert payload["messages"][1]["content"] == (
        '{"title": "A study", "description": null, "body": null, '
        '"language": "en"}'
    )
    assert payload["response_format"]["type"] == "json_schema"
    assert (
        payload["response_format"]["json_schema"]["schema"]["properties"][
            "category_id"
        ]["enum"][-1]
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
def test_http_adapter_rejects_invalid_output(monkeypatch, content: str) -> None:
    monkeypatch.setattr(
        "src.adapters.model_providers.urlopen",
        lambda *_, **__: FakeResponse(
            {
                "choices": [
                    {"finish_reason": "stop", "message": {"content": content}}
                ]
            }
        ),
    )
    provider = ChatHttpProvider(
        url="https://example.test/chat/completions",
        model="test-model",
        instructions=instructions([]),
        api_key=None,
    )
    with pytest.raises(ValueError):
        provider(ArticleInput(title="A study"))


def test_http_adapter_propagates_transport_failure(monkeypatch) -> None:
    def fail(*_, **__):
        raise URLError("offline")

    monkeypatch.setattr("src.adapters.model_providers.urlopen", fail)
    provider = ChatHttpProvider(
        url="https://example.test/chat/completions",
        model="test-model",
        instructions=instructions([]),
        api_key=None,
    )
    with pytest.raises(URLError):
        provider(ArticleInput(title="A study"))


def test_cli_adapter_uses_json_stdin_and_stdout() -> None:
    command = [
        sys.executable,
        "-c",
        "import json,sys; x=json.load(sys.stdin); "
        "print(json.dumps({'category_id':'health','model':x['model']}))",
    ]
    provider = CliProvider(
        command=command,
        model="local-test",
        instructions=instructions([]),
    )
    result = provider(ArticleInput(title="Medicine"))
    assert result.category_id == "health"
    assert result.model == "local-test"


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
                "--provider",
                "cli",
                "--model",
                "test",
                "--command",
                "missing-command",
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
                "--provider",
                "cli",
                "--model",
                "test",
                "--command",
                "missing-command",
            ]
        )


def test_examples_file_has_valid_labels() -> None:
    path = Path(__file__).resolve().parents[1] / "examples" / "categories.jsonl"
    assert len(load_articles(path)) == 5


def test_evaluation_records_one_cli_result(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"article-1","title":"Medicine","category_id":"health"}\n',
        encoding="utf-8",
    )
    command = (
        "import json,sys; json.load(sys.stdin); "
        "print(json.dumps({'category_id':'health'}))"
    )
    assert (
        main(
            [
                "--dataset",
                str(dataset),
                "--max-calls",
                "1",
                "--provider",
                "cli",
                "--model",
                "local-test",
                "--command",
                sys.executable,
                "--command-arg=-c",
                f"--command-arg={command}",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["id"] == "article-1"
    assert result["correct"] is True
    assert result["model"] == "local-test"
    assert "Medicine" not in result.values()

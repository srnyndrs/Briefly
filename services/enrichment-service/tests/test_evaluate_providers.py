import json
from io import BytesIO
from pathlib import Path

import pytest

from src.adapters.providers import PROVIDERS
from src.config.settings import settings
from src.scripts.evaluate_providers import evaluate_articles, main, summarize
from src.services.classification import ArticleInput
from src.services.provider import ProviderError, ProviderResult


@pytest.fixture(autouse=True)
def block_real_requests(monkeypatch):
    def fail(*_, **__):
        raise AssertionError("Evaluation tests must not call real providers")

    monkeypatch.setattr("src.adapters.ollama_provider.urlopen", fail)
    monkeypatch.setattr("src.adapters.gemini_provider.urlopen", fail)


def test_evaluation_checks_call_cap_before_first_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"one","title":"Study","category_ids":["science"]}\n'
        '{"id":"two","title":"Match","category_ids":["sports"]}\n',
        encoding="utf-8",
    )

    def fail(**_):
        raise AssertionError("Provider must not be constructed")

    monkeypatch.setitem(PROVIDERS, "gemini", fail)
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


def test_evaluation_rejects_example_overlap(tmp_path: Path, monkeypatch) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"same","title":"Study","category_ids":["science"]}\n',
        encoding="utf-8",
    )

    def fail(**_):
        raise AssertionError("Provider must not be constructed")

    monkeypatch.setitem(PROVIDERS, "gemini", fail)
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


def test_evaluation_metrics_penalize_unnecessary_second_label() -> None:
    rows = [
        {
            "expected": ["science"],
            "actual": ["science", "health"],
            "correct": False,
            "error": None,
            "language": "en",
            "elapsed_seconds": 1.0,
        },
        {
            "expected": ["science", "health"],
            "actual": ["science", "health"],
            "correct": True,
            "error": None,
            "language": "hu",
            "elapsed_seconds": 3.0,
        },
    ]
    metrics = summarize(rows)
    # Science: F1=1; health: F1=2/3. Overall: TP=3, FP=1, FN=0.
    assert metrics["micro_f1"] == pytest.approx(6 / 7)
    assert metrics["macro_f1"] == pytest.approx((1 + 2 / 3) / 2)
    assert metrics["exact_set_match"] == 0.5
    assert metrics["second_label_precision"] == 0.75
    assert metrics["unnecessary_two_label_predictions"] == 1
    assert metrics["mean_latency_seconds"] == 2.0


@pytest.mark.parametrize(
    "error, expected_rate",
    [
        (ValueError("Unsupported category"), 1.0),
        (ProviderError("Connection failed"), 0.0),
    ],
)
def test_evaluation_counts_invalid_output_separately_from_transport_failure(
    error: Exception,
    expected_rate: float,
) -> None:
    def fail(_: ArticleInput) -> ProviderResult:
        raise error

    rows = evaluate_articles(
        fail,
        "fake",
        "fake-model",
        [("one", ArticleInput(title="Article"), ("science",))],
        0,
    )
    metrics = summarize(rows)
    assert metrics["invalid_output_rate"] == expected_rate
    assert metrics["failure_rate"] == 1.0


def test_evaluation_accepts_fake_provider_and_continues_after_failures(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch
) -> None:
    articles = [
        ("success", ArticleInput(title="Study"), ("science",)),
        ("abstain", ArticleInput(title="Unclear"), ()),
        ("provider-error", ArticleInput(title="Broken"), ("sports",)),
        ("unexpected", ArticleInput(title="Secret"), ("health",)),
        ("after-errors", ArticleInput(title="Match"), ("sports",)),
    ]
    waits = []
    calls = []
    monkeypatch.setattr("src.scripts.evaluate_providers.time.sleep", waits.append)

    def fake_provider(article: ArticleInput) -> ProviderResult:
        calls.append(article.title)
        if article.title == "Broken":
            raise ProviderError("safe detail" + "x" * 1_000)
        if article.title == "Secret":
            raise RuntimeError("private detail")
        category = {
            "Study": ("science",),
            "Unclear": (),
            "Match": ("sports",),
        }[article.title]
        return ProviderResult(category, "fake-model-v2", 4, 2)

    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        "".join(
            json.dumps(
                {
                    "id": key,
                    "title": article.title,
                    "category_ids": list(expected),
                }
            )
            + "\n"
            for key, article, expected in articles
        ),
        encoding="utf-8",
    )
    constructed = []

    def factory(**kwargs):
        constructed.append(kwargs["model"])
        return fake_provider

    monkeypatch.setitem(PROVIDERS, "fake", factory)
    assert (
        main(
            [
                "--provider",
                "fake",
                "--dataset",
                str(dataset),
                "--max-calls",
                "5",
                "--model",
                "fake-model",
                "--request-interval",
                "0.5",
            ]
        )
        == 0
    )
    assert constructed == ["fake-model"]
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert calls == [article.title for _, article, _ in articles]
    assert waits == [0.5] * 4
    assert [row["id"] for row in rows] == [item[0] for item in articles]
    assert all(row["provider"] == "fake" for row in rows)
    assert rows[0]["actual"] == ["science"] and rows[0]["correct"] is True
    assert rows[0]["model"] == "fake-model-v2"
    assert rows[1]["actual"] == [] and rows[1]["correct"] is True
    assert rows[2]["error"] == "ProviderError"
    assert len(rows[2]["error_detail"]) == 1_000
    assert rows[2]["model"] == "fake-model"
    assert rows[3]["error"] == "RuntimeError"
    assert rows[3]["error_detail"] is None
    assert rows[4]["correct"] is True


def test_ollama_evaluation_needs_no_gemini_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch
) -> None:
    dataset = tmp_path / "articles.jsonl"
    dataset.write_text(
        '{"id":"one","title":"Study","category_ids":["science"]}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "ollama_base_url", "http://localhost:11434")
    monkeypatch.setattr(
        "src.adapters.ollama_provider.urlopen",
        lambda *_, **__: BytesIO(
            json.dumps(
                {
                    "model": "test-model:resolved",
                    "done": True,
                    "done_reason": "stop",
                    "message": {"content": '{"category_ids":["science"]}'},
                }
            ).encode()
        ),
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
    assert row["actual"] == ["science"]
    assert row["correct"] is True

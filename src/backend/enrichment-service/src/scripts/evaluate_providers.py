"""Compare a bounded labelled sample without writing production results."""

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from src.adapters.providers import PROVIDERS
from src.services.classification import ArticleInput, normalize_article
from src.services.provider import (
    PROMPT_VERSION,
    Provider,
    ProviderError,
    instructions,
    parse_categories,
)


def load_articles(
    path: Path,
) -> list[tuple[str, ArticleInput, tuple[str, ...]]]:
    rows = []
    seen = set()
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), 1
    ):
        if not line.strip():
            continue
        data = json.loads(line)
        if not isinstance(data, dict):
            raise ValueError(f"{path}:{line_number}: expected a JSON object")
        article_id = data.get("id")
        if not isinstance(article_id, str) or not article_id.strip():
            raise ValueError(f"{path}:{line_number}: id must be text")
        if article_id in seen:
            raise ValueError(f"{path}:{line_number}: duplicate id")
        seen.add(article_id)
        category = parse_categories({"category_ids": data["category_ids"]})
        keywords = data.get("keywords", [])
        if not isinstance(keywords, list) or any(
            not isinstance(value, str) for value in keywords
        ):
            raise ValueError(
                f"{path}:{line_number}: keywords must be a list of strings"
            )
        article = normalize_article(
            ArticleInput(
                title=data["title"],
                description=data.get("description"),
                body=data.get("body"),
                language=data.get("language"),
                source_category=data.get("source_category"),
                keywords=tuple(keywords),
            )
        )
        if not any((article.title, article.description, article.body)):
            raise ValueError(f"{path}:{line_number}: article text is empty")
        rows.append((article_id, article, category))
    if not rows:
        raise ValueError(f"{path}: no articles")
    return rows


def evaluate_articles(
    provider: Provider,
    provider_name: str,
    model: str,
    articles: list[tuple[str, ArticleInput, tuple[str, ...]]],
    request_interval: float,
) -> list[dict]:
    rows: list[dict] = []
    for index, (article_id, article, expected) in enumerate(articles):
        if index and request_interval:
            time.sleep(request_interval)
        started = time.monotonic()
        try:
            result = provider(article)
            row = {
                "id": article_id,
                "expected": expected,
                "actual": list(result.category_ids),
                "correct": result.category_ids == expected,
                "model": result.model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "error": None,
                "invalid_output": False,
                "error_detail": None,
            }
        except Exception as exc:
            row = {
                "id": article_id,
                "expected": expected,
                "actual": None,
                "correct": False,
                "model": model,
                "input_tokens": None,
                "output_tokens": None,
                "error": type(exc).__name__,
                "invalid_output": isinstance(exc, ValueError),
                "error_detail": str(exc)
                if isinstance(exc, ProviderError)
                else None,
            }
        row.update(
            provider=provider_name,
            prompt_version=PROMPT_VERSION,
            language=article.language,
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    return rows


def summarize(rows: list[dict]) -> dict:
    labels = set()
    for row in rows:
        labels.update(row["expected"])
        labels.update(row["actual"] or [])
    per_category = {}
    true_positive = false_positive = false_negative = 0
    for label in sorted(labels):
        tp = sum(
            label in row["expected"] and label in (row["actual"] or [])
            for row in rows
        )
        fp = sum(
            label not in row["expected"] and label in (row["actual"] or [])
            for row in rows
        )
        fn = sum(
            label in row["expected"] and label not in (row["actual"] or [])
            for row in rows
        )
        true_positive += tp
        false_positive += fp
        false_negative += fn
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_category[label] = {
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0,
        }
    micro_denominator = 2 * true_positive + false_positive + false_negative
    two_label = [
        row
        for row in rows
        if row["actual"] is not None and len(row["actual"]) == 2
    ]
    by_language = Counter(row["language"] or "unknown" for row in rows)
    successful = [row for row in rows if row["error"] is None]
    return {
        "articles": len(rows),
        "exact_set_match": sum(row["correct"] for row in rows) / len(rows),
        "per_category": per_category,
        "macro_f1": sum(item["f1"] for item in per_category.values())
        / len(per_category)
        if per_category
        else 0.0,
        "micro_f1": 2 * true_positive / micro_denominator
        if micro_denominator
        else 0.0,
        "abstention_rate": sum(row["actual"] == [] for row in rows) / len(rows),
        "invalid_output_rate": sum(
            row.get("invalid_output", False) for row in rows
        )
        / len(rows),
        "failure_rate": sum(row["error"] is not None for row in rows)
        / len(rows),
        "second_label_precision": sum(
            len(set(row["actual"]) & set(row["expected"])) for row in two_label
        )
        / (2 * len(two_label))
        if two_label
        else None,
        "unnecessary_two_label_predictions": sum(
            len(row["expected"]) == 1 for row in two_label
        ),
        "language": {
            language: {
                "articles": count,
                "exact_set_match": sum(
                    row["correct"]
                    for row in rows
                    if (row["language"] or "unknown") == language
                )
                / count,
            }
            for language, count in by_language.items()
        },
        "mean_latency_seconds": sum(
            row["elapsed_seconds"] for row in successful
        )
        / len(successful)
        if successful
        else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="labelled article JSONL file",
    )
    parser.add_argument(
        "--examples", type=Path, help="separate labelled prompt examples"
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        required=True,
        help="call limit; must cover every dataset row",
    )
    parser.add_argument("--model", required=True, help="provider model ID")
    parser.add_argument(
        "--provider",
        choices=PROVIDERS,
        default="gemini",
        help="provider name (default: gemini)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="seconds per call (default: 30)",
    )
    parser.add_argument(
        "--request-interval",
        type=float,
        default=0,
        help="seconds to wait between calls (default: 0)",
    )
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.request_interval < 0:
        parser.error("--request-interval cannot be negative")

    articles = load_articles(args.dataset)
    examples = load_articles(args.examples) if args.examples else []
    if args.max_calls < len(articles):
        parser.error("--max-calls must cover the entire dataset")
    if set(row[0] for row in articles) & set(row[0] for row in examples):
        parser.error("example and evaluation IDs must differ")
    prompt = instructions([(row[1], row[2]) for row in examples])
    try:
        provider: Provider = PROVIDERS[args.provider](
            model=args.model,
            instructions=prompt,
            timeout=args.timeout,
        )
    except ValueError as exc:
        parser.error(str(exc))

    rows = evaluate_articles(
        provider, args.provider, args.model, articles, args.request_interval
    )
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "examples_sha256": hashlib.sha256(
            args.examples.read_bytes()
        ).hexdigest()
        if args.examples
        else None,
        "provider": args.provider,
        "model": args.model,
        "prompt_version": PROMPT_VERSION,
        "summary": summarize(rows),
    }
    print(json.dumps(manifest, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

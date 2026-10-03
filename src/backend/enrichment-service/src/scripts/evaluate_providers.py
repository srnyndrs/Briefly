"""Compare a bounded labelled sample without writing production results."""

import argparse
import json
import sys
import time
from pathlib import Path

from src.adapters.providers import PROVIDERS
from src.services.classification import ArticleInput, normalize_article
from src.services.provider import (
    PROMPT_VERSION,
    Provider,
    ProviderError,
    instructions,
    parse_category,
)


def load_articles(path: Path) -> list[tuple[str, ArticleInput, str | None]]:
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
        category = parse_category({"category_id": data["category_id"]})
        article = normalize_article(
            ArticleInput(
                title=data["title"],
                description=data.get("description"),
                body=data.get("body"),
                language=data.get("language"),
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
    articles: list[tuple[str, ArticleInput, str | None]],
    request_interval: float,
) -> None:
    for index, (article_id, article, expected) in enumerate(articles):
        if index and request_interval:
            time.sleep(request_interval)
        started = time.monotonic()
        try:
            result = provider(article)
            row = {
                "id": article_id,
                "expected": expected,
                "actual": result.category_id,
                "correct": result.category_id == expected,
                "model": result.model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "error": None,
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
                "error_detail": str(exc)
                if isinstance(exc, ProviderError)
                else None,
            }
        row.update(
            provider=provider_name,
            prompt_version=PROMPT_VERSION,
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
        print(json.dumps(row, ensure_ascii=False), flush=True)


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

    evaluate_articles(
        provider, args.provider, args.model, articles, args.request_interval
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

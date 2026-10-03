"""Compare a bounded labelled sample without writing production results."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from src.adapters.model_providers import ChatHttpProvider, CliProvider
from src.services.classification import ArticleInput, normalize_article
from src.services.provider import (
    PROMPT_VERSION,
    Provider,
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
    parser.add_argument(
        "--provider",
        choices=("http", "cli"),
        required=True,
        help="HTTP endpoint or JSON stdin/stdout command",
    )
    parser.add_argument("--model", required=True, help="provider model ID")
    parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="seconds per call (default: 30)",
    )
    parser.add_argument("--url", help="HTTP Chat Completions endpoint")
    parser.add_argument(
        "--api-key-env", help="name of environment variable with HTTP API key"
    )
    parser.add_argument(
        "--response-format",
        choices=("plain", "json", "schema"),
        default="plain",
        help="HTTP output mode (default: plain)",
    )
    parser.add_argument("--command", help="CLI wrapper executable")
    parser.add_argument(
        "--command-arg",
        action="append",
        default=[],
        help="fixed CLI argument; repeat for more arguments",
    )
    args = parser.parse_args(argv)

    articles = load_articles(args.dataset)
    examples = load_articles(args.examples) if args.examples else []
    if args.max_calls < len(articles):
        parser.error("--max-calls must cover the entire dataset")
    if set(row[0] for row in articles) & set(row[0] for row in examples):
        parser.error("example and evaluation IDs must differ")
    prompt = instructions([(row[1], row[2]) for row in examples])
    provider: Provider
    if args.provider == "http":
        if not args.url:
            parser.error("--url is required for HTTP")
        if args.api_key_env and not os.environ.get(args.api_key_env):
            parser.error("the API key environment variable is empty")
        provider = ChatHttpProvider(
            url=args.url,
            model=args.model,
            instructions=prompt,
            api_key=os.environ.get(args.api_key_env)
            if args.api_key_env
            else None,
            timeout=args.timeout,
            response_format=args.response_format,
        )
    else:
        if not args.command:
            parser.error("--command is required for CLI")
        provider = CliProvider(
            command=[args.command, *args.command_arg],
            model=args.model,
            instructions=prompt,
            timeout=args.timeout,
        )

    for article_id, article, expected in articles:
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
            }
        except Exception as exc:
            row = {
                "id": article_id,
                "expected": expected,
                "actual": None,
                "correct": False,
                "model": args.model,
                "input_tokens": None,
                "output_tokens": None,
                "error": type(exc).__name__,
            }
        row.update(
            provider=args.provider,
            prompt_version=PROMPT_VERSION,
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
        print(json.dumps(row, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

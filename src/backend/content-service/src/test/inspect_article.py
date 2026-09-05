#!/usr/bin/env python3
"""
Article Playground & newspaper4k Inspector
-------------------------------------------
Usage:
    poetry run python src/test/inspect_article.py
    poetry run python src/test/inspect_article.py <article_url>
    poetry run python src/test/inspect_article.py <article_url> --nlp
    poetry run python src/test/inspect_article.py <article_url> --full-text
    poetry run python src/test/inspect_article.py <article_url> --json
    poetry run python src/test/inspect_article.py <article_url> --export
    poetry run python src/test/inspect_article.py <article_url> --export --nlp
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import newspaper
from newspaper import Article, Config

# Ensure UTF-8 output encoding on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_TEST_URL = (
    "https://telex.hu/english/2026/08/18/"
    "fidesz-members-can-share-their-opinion-on-viktor-orban-s-suitability-in-internal-survey"
)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 BrieflyBot/1.0"
)


def _safe_serialize(obj: Any) -> Any:
    """Recursively convert newspaper objects, datetimes, sets to JSON-serializable primitives."""
    if obj is None or isinstance(obj, (int, float, str, bool)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (set, tuple, list)):
        return [_safe_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): _safe_serialize(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        return {
            str(k): _safe_serialize(v)
            for k, v in obj.__dict__.items()
            if not str(k).startswith("_")
        }
    return str(obj)


def _sanitize_filename(name: str) -> str:
    """Strip invalid characters for safe file naming across operating systems."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", name)
    cleaned = cleaned.strip(" ._-")
    return cleaned or "article_export"


def _generate_export_filename(
    url: str, title: str | None = None
) -> str:
    """Generate a readable, unique JSON export filename."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace(":", "_") or "article"

    slug = ""
    if title:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", title).strip("_")[:40]
    elif parsed.path:
        slug = re.sub(
            r"[^a-zA-Z0-9_-]+", "_", Path(parsed.path).stem
        ).strip("_")[:40]

    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    if slug:
        return f"{domain}_{slug}_{url_hash}.json"
    return f"{domain}_{url_hash}.json"


def inspect_article(
    url: str,
    run_nlp: bool = False,
    show_full_text: bool = False,
    dump_json: bool = False,
    export_json: bool = False,
    export_html: bool = False,
    language: str | None = None,
    user_agent: str | None = None,
    timeout: int = 15,
) -> None:
    print(f"\n{'=' * 80}")
    print(f">> Fetching & Inspecting Article with newspaper4k: {url}")
    print(f"{'=' * 80}\n")

    # Configure newspaper
    config = Config()
    config.browser_user_agent = user_agent or DEFAULT_USER_AGENT
    config.request_timeout = timeout
    config.fetch_images = True
    config.memorize_articles = False
    if language:
        config.language = language

    article = Article(url, config=config)

    # 1. Download
    t0_download = time.perf_counter()
    try:
        article.download()
        download_duration = time.perf_counter() - t0_download
    except Exception as exc:
        print(f"[!] HTTP / Network Download Exception: {exc}")
        sys.exit(1)

    if not getattr(article, "is_downloaded", False):
        err_msg = (
            getattr(article, "download_exception_msg", None)
            or "Unknown download error"
        )
        download_state = getattr(article, "download_state", "FAILED")
        print("[!] Download Failed:")
        print(f"  * Error: {err_msg}")
        print(f"  * State: {download_state}")
        print(
            "  * Note: The website may be blocking automated scrapers with HTTP 403/WAF/Paywall."
        )
        sys.exit(1)

    # 2. Parse
    t0_parse = time.perf_counter()
    try:
        article.parse()
        parse_duration = time.perf_counter() - t0_parse
    except Exception as exc:
        print(f"[!] Parse Error: {exc}")
        sys.exit(1)

    # 3. Optional NLP
    nlp_duration = 0.0
    if run_nlp:
        t0_nlp = time.perf_counter()
        try:
            article.nlp()
            nlp_duration = time.perf_counter() - t0_nlp
        except Exception as exc:
            print(f"[!] NLP Processing Warning: {exc}")

    # Prepare extracted data dictionary
    raw_html = article.html or ""
    text_content = (
        getattr(article, "text_cleaned", None) or article.text or ""
    )
    word_count = len(text_content.split())
    reading_time_mins = (
        max(1, round(word_count / 200)) if word_count else 0
    )

    tags = list(getattr(article, "tags", None) or [])
    meta_keywords = list(getattr(article, "meta_keywords", None) or [])
    nlp_keywords = (
        list(getattr(article, "keywords", None) or [])
        if run_nlp
        else []
    )
    images = list(getattr(article, "images", None) or [])
    movies = list(getattr(article, "movies", None) or [])

    structured_data = {
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "newspaper_version": getattr(
            newspaper, "__version__", "unknown"
        ),
        "timings_seconds": {
            "download": round(download_duration, 4),
            "parse": round(parse_duration, 4),
            "nlp": round(nlp_duration, 4) if run_nlp else None,
            "total": round(
                download_duration + parse_duration + nlp_duration, 4
            ),
        },
        "metadata": {
            "title": article.title,
            "authors": article.authors,
            "publish_date": _safe_serialize(article.publish_date),
            "canonical_link": getattr(article, "canonical_link", None),
            "meta_site_name": getattr(article, "meta_site_name", None),
            "meta_favicon": getattr(article, "meta_favicon", None),
            "meta_lang": getattr(article, "meta_lang", None),
            "meta_description": getattr(
                article, "meta_description", None
            ),
            "meta_img": getattr(article, "meta_img", None),
            "top_image": getattr(article, "top_image", None)
            or getattr(article, "top_img", None),
        },
        "content": {
            "text": text_content,
            "word_count": word_count,
            "character_count": len(text_content),
            "estimated_reading_time_minutes": reading_time_mins,
            "summary": getattr(article, "summary", "")
            if run_nlp
            else None,
        },
        "taxonomy": {
            "tags": sorted(tags),
            "meta_keywords": meta_keywords,
            "nlp_keywords": nlp_keywords,
        },
        "media": {
            "top_image": getattr(article, "top_image", None)
            or getattr(article, "top_img", None),
            "images_count": len(images),
            "images": sorted(images),
            "movies_count": len(movies),
            "movies": movies,
        },
        "meta_data": _safe_serialize(getattr(article, "meta_data", {})),
        "html_size_bytes": len(raw_html.encode("utf-8")),
    }

    # Handle Exporting to file
    test_dir = Path(__file__).resolve().parent

    if export_json:
        filename = _generate_export_filename(url, article.title)
        export_path = test_dir / filename
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        print(
            f"[+] Exported structured article data: {export_path.name} ({export_path.stat().st_size:,} bytes)"
        )
        print(f"    Location: {export_path}\n")

    if export_html:
        base_name = _generate_export_filename(
            url, article.title
        ).replace(".json", ".html")
        html_path = test_dir / base_name
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(raw_html)
        print(
            f"[+] Exported raw HTML: {html_path.name} ({html_path.stat().st_size:,} bytes)"
        )
        print(f"    Location: {html_path}\n")

    # Handle --json output
    if dump_json:
        print(json.dumps(structured_data, indent=2, ensure_ascii=False))
        return

    # Formatted terminal display
    print("[1] DOWNLOAD & PARSER METRICS")
    print(
        f"  * newspaper4k version: {structured_data['newspaper_version']}"
    )
    print(f"  * Download time:       {download_duration:.3f}s")
    print(f"  * Parse time:          {parse_duration:.3f}s")
    if run_nlp:
        print(f"  * NLP processing time: {nlp_duration:.3f}s")
    print(
        f"  * Raw HTML payload:    {len(raw_html.encode('utf-8')):,} bytes"
    )
    print()

    print("[2] CORE ARTICLE METADATA")
    print(f"  * Title:           {article.title or '(None)'}")
    print(
        f"  * Authors:         {', '.join(article.authors) if article.authors else '(None detected)'}"
    )
    pub_date_str = _safe_serialize(article.publish_date)
    print(f"  * Publish Date:    {pub_date_str or '(None detected)'}")
    print(
        f"  * Language:        {getattr(article, 'meta_lang', None) or '(Not specified)'}"
    )
    print(
        f"  * Canonical URL:   {getattr(article, 'canonical_link', None) or '(None)'}"
    )
    print(
        f"  * Site Name:       {getattr(article, 'meta_site_name', None) or '(None)'}"
    )
    print(
        f"  * Favicon:         {getattr(article, 'meta_favicon', None) or '(None)'}"
    )
    print(
        f"  * Meta Desc:       {getattr(article, 'meta_description', None) or '(None)'}"
    )
    print()

    print("[3] ARTICLE CONTENT & METRICS")
    print(
        f"  * Word Count:      {word_count:,} words (~{reading_time_mins} min read)"
    )
    print(f"  * Character Count: {len(text_content):,} chars")

    if text_content:
        if show_full_text:
            print("\n  --- FULL ARTICLE TEXT ---")
            for paragraph in text_content.splitlines():
                if paragraph.strip():
                    print(f"  {paragraph}")
            print("  --- END FULL TEXT ---\n")
        else:
            preview = text_content[:500].strip()
            print(
                "\n  --- TEXT PREVIEW (First 500 chars, use --full-text to see all) ---"
            )
            for paragraph in preview.splitlines():
                if paragraph.strip():
                    print(f"  {paragraph}")
            if len(text_content) > 500:
                print(
                    f"  ... [+{len(text_content) - 500:,} more characters]"
                )
            print("  --- END PREVIEW ---\n")
    else:
        print("  * Text:            (No text extracted)")

    if run_nlp:
        print("[3.1] NLP SUMMARY")
        summary = getattr(article, "summary", "").strip()
        if summary:
            for line in summary.splitlines():
                if line.strip():
                    print(f"  {line}")
        else:
            print("  (No NLP summary generated)")
        print()
    else:
        print(
            "  * Tip: Run with --nlp to generate automatic summary and NLP keywords."
        )
        print()

    print("[4] MEDIA & MULTIMEDIA ASSETS")
    top_img = getattr(article, "top_image", None) or getattr(
        article, "top_img", None
    )
    meta_img = getattr(article, "meta_img", None)

    print(f"  * Top Image:       {top_img or '(None)'}")
    print(f"  * Meta Image:      {meta_img or '(None)'}")
    print(f"  * Discovered Images: {len(images)} image(s)")
    for idx, img_url in enumerate(images[:5], 1):
        is_top = " [TOP]" if img_url == top_img else ""
        print(f"    [{idx}] {img_url}{is_top}")
    if len(images) > 5:
        print(f"    ... and {len(images) - 5} more images")

    print(f"  * Videos / Movies: {len(movies)} media embed(s)")
    for idx, movie_url in enumerate(movies, 1):
        print(f"    [{idx}] {movie_url}")
    print()

    print("[5] TAXONOMY, TAGS & KEYWORDS")
    print(
        f"  * Tags:            {', '.join(tags) if tags else '(None)'}"
    )
    print(
        f"  * Meta Keywords:   {', '.join(meta_keywords) if meta_keywords else '(None)'}"
    )
    if run_nlp:
        print(
            f"  * NLP Keywords:    {', '.join(nlp_keywords) if nlp_keywords else '(None)'}"
        )
    print()

    print("[6] RAW META DATA / OPENGRAPH / TWITTER")
    meta_data = getattr(article, "meta_data", {})
    if meta_data:
        og_items = {
            k: v
            for k, v in meta_data.items()
            if k.startswith("og:") or k.startswith("og_")
        }
        twitter_items = {
            k: v
            for k, v in meta_data.items()
            if k.startswith("twitter:") or k.startswith("twitter_")
        }
        other_items = {
            k: v
            for k, v in meta_data.items()
            if k not in og_items and k not in twitter_items
        }

        if og_items:
            print("  * OpenGraph (og:*):")
            for k, v in og_items.items():
                print(f"      {k}: {v}")
        if twitter_items:
            print("  * Twitter Cards (twitter:*):")
            for k, v in twitter_items.items():
                print(f"      {k}: {v}")
        if other_items:
            print(f"  * Other Meta Tags ({len(other_items)} items):")
            for k in sorted(other_items.keys())[:10]:
                print(f"      {k}: {other_items[k]}")
            if len(other_items) > 10:
                print(
                    f"      ... and {len(other_items) - 10} more meta keys"
                )
    else:
        print("  * (No meta_data dictionary found)")
    print()

    # Introspect all available attributes on the Article object safely
    public_attrs = []
    for a in dir(article):
        if a.startswith("_"):
            continue
        try:
            val = getattr(article, a)
            if not callable(val):
                public_attrs.append(a)
        except Exception:
            # Property raised exception on access (e.g. lazy uninitialized doc parser)
            public_attrs.append(f"{a} (uninitialized)")

    print(
        f"[7] ALL ARTICLE ATTRIBUTES ({len(public_attrs)} public properties)"
    )
    print(f"  {sorted(public_attrs)}")
    print()

    print(f"{'=' * 80}")
    print(">> Inspection Complete.")
    print(f"{'=' * 80}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect article extraction details and explore newspaper4k output."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=DEFAULT_TEST_URL,
        help=f"URL of the article to inspect (default: {DEFAULT_TEST_URL})",
    )
    parser.add_argument(
        "--nlp",
        action="store_true",
        help="Run natural language processing (NLP) to extract summary and keywords",
    )
    parser.add_argument(
        "--full-text",
        action="store_true",
        help="Display the entire extracted article body in terminal instead of preview snippet",
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default=None,
        help="Language code override (e.g. 'en', 'hu', 'de')",
    )
    parser.add_argument(
        "--user-agent",
        "-u",
        type=str,
        default=None,
        help="Custom User-Agent header for fetching the article",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="HTTP request timeout in seconds (default: 15)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Dump parsed article as JSON structure to stdout",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export parsed article data as a JSON file into the src/test/ directory",
    )
    parser.add_argument(
        "--export-html",
        action="store_true",
        help="Export raw downloaded HTML as a file into the src/test/ directory",
    )

    args = parser.parse_args()
    inspect_article(
        url=args.url,
        run_nlp=args.nlp,
        show_full_text=args.full_text,
        dump_json=args.json,
        export_json=args.export,
        export_html=args.export_html,
        language=args.language,
        user_agent=args.user_agent,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()

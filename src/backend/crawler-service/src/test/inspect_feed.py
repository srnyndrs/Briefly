#!/usr/bin/env python3
"""
RSS Feed Playground & Inspector
-------------------------------
Usage:
    poetry run python test/inspect_feed.py <feed_url>
    poetry run python test/inspect_feed.py https://24.hu/feed/
    poetry run python test/inspect_feed.py https://24.hu/feed/ --max-entries 3
    poetry run python test/inspect_feed.py https://24.hu/feed/ --json
    poetry run python test/inspect_feed.py https://24.hu/feed/ --export
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import feedparser
import requests

# Ensure UTF-8 output encoding on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _format_parsed_date(time_struct) -> str | None:
    if not time_struct:
        return None
    try:
        dt = datetime(*time_struct[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return str(time_struct)


def _safe_dict(obj: Any) -> Any:
    """Recursively convert feedparser structures to serializable dicts/primitives."""
    if isinstance(obj, dict):
        return {k: _safe_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_dict(item) for item in obj]
    if hasattr(obj, "keys"):
        return {k: _safe_dict(obj[k]) for k in obj.keys()}
    if hasattr(obj, "__dict__"):
        return {
            k: _safe_dict(v)
            for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    return str(obj)


def _sanitize_filename(name: str) -> str:
    """Strip invalid characters for safe file naming across OSes."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", name)
    cleaned = cleaned.strip(" ._-")
    return cleaned or "feed_export"


def _generate_export_filename(
    etag: str | None, url: str, content: bytes
) -> str:
    if etag:
        cleaned_etag = etag.strip()
        if cleaned_etag.startswith("W/"):
            cleaned_etag = cleaned_etag[2:]
        cleaned_etag = cleaned_etag.strip("\"'")
        sanitized = _sanitize_filename(cleaned_etag)
        if sanitized:
            return f"{sanitized}.json"

    # Fallback if no ETag is provided
    domain = urlparse(url).netloc.replace(":", "_") or "feed"
    content_hash = hashlib.sha256(content).hexdigest()[:10]
    return f"no_etag_{domain}_{content_hash}.json"


def inspect_feed(
    url: str,
    max_entries: int = 3,
    dump_json: bool = False,
    export_json: bool = False,
) -> None:
    print(f"\n{'=' * 80}")
    print(f">> Fetching Feed: {url}")
    print(f"{'=' * 80}\n")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 BrieflyBot/1.0"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except Exception as exc:
        print(f"[!] HTTP Fetch Error: {exc}")
        sys.exit(1)

    etag = response.headers.get("ETag")
    last_modified = response.headers.get("Last-Modified")

    print("[1] HTTP TRANSPORT DETAILS")
    print(
        f"  * HTTP Status:     {response.status_code} {response.reason}"
    )
    print(
        f"  * Content-Type:    {response.headers.get('Content-Type', 'N/A')}"
    )
    print(f"  * Content-Length:  {len(response.content):,} bytes")
    print(f"  * ETag:            {etag or 'None'}")
    print(f"  * Last-Modified:   {last_modified or 'None'}")
    print(
        f"  * Cache-Control:   {response.headers.get('Cache-Control', 'None')}"
    )
    print()

    parsed = feedparser.parse(response.content)

    # Build full serializable payload for JSON output / export
    serializable_full = {
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_transport": {
            "status_code": response.status_code,
            "reason": response.reason,
            "content_type": response.headers.get("Content-Type"),
            "content_length": len(response.content),
            "etag": etag,
            "last_modified": last_modified,
            "cache_control": response.headers.get("Cache-Control"),
        },
        "bozo": parsed.get("bozo"),
        "bozo_exception": str(parsed.get("bozo_exception", "")),
        "version": parsed.get("version"),
        "namespaces": parsed.get("namespaces"),
        "feed": _safe_dict(parsed.get("feed", {})),
        "entries_count": len(parsed.entries),
        "entries": [_safe_dict(e) for e in parsed.entries],
    }

    if export_json:
        test_dir = Path(__file__).resolve().parent
        filename = _generate_export_filename(
            etag, url, response.content
        )
        export_path = test_dir / filename

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(
                serializable_full, f, indent=2, ensure_ascii=False
            )

        print(
            f"[+] Exported feed results to JSON: {export_path.name} "
            f"({export_path.stat().st_size:,} bytes)"
        )
        print(f"    Location: {export_path}\n")

    if dump_json:
        # If --json was specified, print JSON to stdout
        serializable_stdout = dict(serializable_full)
        if max_entries is not None and max_entries > 0:
            serializable_stdout["entries"] = serializable_full[
                "entries"
            ][:max_entries]
        print(
            json.dumps(
                serializable_stdout, indent=2, ensure_ascii=False
            )
        )
        return

    print("[2] PARSER & FORMAT DETECTION")
    print(
        f"  * Feed Version:    {parsed.get('version', 'Unknown')}"
    )
    print(
        f"  * Bozo Bit:        {parsed.get('bozo', 0)} "
        "(1 if XML was malformed or non-standard)"
    )
    if parsed.get("bozo"):
        print(
            f"  * Bozo Exception:  {parsed.get('bozo_exception')}"
        )
    print(
        f"  * Namespaces:      {list(parsed.get('namespaces', {}).keys())}"
    )
    print()

    feed = parsed.feed
    print("[3] CHANNEL / FEED-LEVEL METADATA")
    print(f"  * Title:           {feed.get('title', 'N/A')}")
    print(
        f"  * Subtitle/Desc:   {feed.get('subtitle') or feed.get('description', 'N/A')}"
    )
    print(f"  * Main Link:       {feed.get('link', 'N/A')}")
    print(f"  * Language:        {feed.get('language', 'N/A')}")
    print(
        f"  * Published:       {feed.get('published', 'N/A')} "
        f"(parsed: {_format_parsed_date(feed.get('published_parsed'))})"
    )
    print(
        f"  * Updated:         {feed.get('updated', 'N/A')} "
        f"(parsed: {_format_parsed_date(feed.get('updated_parsed'))})"
    )
    print(f"  * Rights:          {feed.get('rights', 'N/A')}")
    print()

    print("[4] CMS, GENERATOR & FREQUENCY SIGNALS")
    generator = feed.get("generator_detail") or feed.get(
        "generator"
    )
    if isinstance(generator, dict):
        print(
            f"  * Generator:       {generator.get('name')} "
            f"(v{generator.get('version')}) - {generator.get('href')}"
        )
    else:
        print(
            f"  * Generator:       {generator or 'None detected'}"
        )

    sy_period = feed.get("sy_updateperiod") or feed.get(
        "updateperiod"
    )
    sy_freq = feed.get("sy_updatefrequency") or feed.get(
        "updatefrequency"
    )
    ttl = feed.get("ttl")
    print(f"  * sy:updatePeriod: {sy_period or 'Not specified'}")
    print(f"  * sy:updateFreq:   {sy_freq or 'Not specified'}")
    print(f"  * <ttl> (minutes): {ttl or 'Not specified'}")
    print()

    print("[5] LINKS, HUBS & PAGINATION DISCOVERY")
    links = feed.get("links", [])
    if links:
        for idx, link_item in enumerate(links, 1):
            rel = link_item.get("rel", "alternate")
            href = link_item.get("href")
            l_type = link_item.get("type", "")
            title = link_item.get("title", "")
            title_part = f" | title={title}" if title else ""
            print(
                f"  [{idx}] rel='{rel}' | type='{l_type}' | href='{href}'{title_part}"
            )
    else:
        print("  * No <link> elements found at feed level.")

    next_link = next(
        (
            link_item.get("href")
            for link_item in links
            if link_item.get("rel") == "next"
        ),
        None,
    )
    prev_link = next(
        (
            link_item.get("href")
            for link_item in links
            if link_item.get("rel") in ("prev", "previous")
        ),
        None,
    )
    hub_link = next(
        (
            link_item.get("href")
            for link_item in links
            if link_item.get("rel") == "hub"
        ),
        None,
    )
    self_link = next(
        (
            link_item.get("href")
            for link_item in links
            if link_item.get("rel") == "self"
        ),
        None,
    )

    print("\n  >> Pagination & WebSub summary:")
    print(f"    - Self Link:      {self_link or 'None'}")
    print(
        f"    - Next Page Link: {next_link or '[None] (RFC 5005 next not present)'}"
    )
    print(f"    - Prev Page Link: {prev_link or 'None'}")
    print(f"    - WebSub Hub:     {hub_link or '[None]'}")
    print()

    print(f"[6] ALL CHANNEL KEYS ({len(feed.keys())} keys)")
    print(f"  {sorted(list(feed.keys()))}")
    print()

    entries_count = len(parsed.entries)
    print(f"[7] ENTRIES ({entries_count} total entries found)")
    if entries_count > 0:
        first_entry = parsed.entries[0]
        last_entry = parsed.entries[-1]
        print(
            f"  * Newest entry date: {_format_parsed_date(first_entry.get('published_parsed') or first_entry.get('updated_parsed'))}"
        )
        print(
            f"  * Oldest entry date: {_format_parsed_date(last_entry.get('published_parsed') or last_entry.get('updated_parsed'))}"
        )
        print()

        shown = min(entries_count, max_entries)
        print(f"--- Showing details for first {shown} entries ---")

        for idx, entry in enumerate(parsed.entries[:shown], 1):
            print(f"\n[Entry #{idx}]")
            print(
                f"  * Title:        {entry.get('title', 'Untitled')}"
            )
            print(f"  * Link:         {entry.get('link', 'N/A')}")
            print(
                f"  * ID / GUID:    {entry.get('id') or entry.get('guid', 'N/A')}"
            )
            print(
                f"  * Published:    {entry.get('published', 'N/A')} "
                f"(parsed: {_format_parsed_date(entry.get('published_parsed'))})"
            )
            print(
                f"  * Updated:      {entry.get('updated', 'N/A')} "
                f"(parsed: {_format_parsed_date(entry.get('updated_parsed'))})"
            )
            print(f"  * Author:       {entry.get('author', 'N/A')}")

            tags = [
                t.get("term")
                for t in entry.get("tags", [])
                if t.get("term")
            ]
            if tags:
                tag_str = ", ".join(tags[:6])
                if len(tags) > 6:
                    tag_str += "..."
                print(f"  * Tags:         {tag_str}")

            enclosures = entry.get("enclosures", [])
            if enclosures:
                enc_info = [
                    f"{e.get('type')}: {e.get('href')}"
                    for e in enclosures
                ]
                print(f"  * Enclosures:   {enc_info}")

            media_thumbnails = entry.get("media_thumbnail", [])
            if media_thumbnails:
                print(
                    f"  * Thumbnails:   {[m.get('url') for m in media_thumbnails]}"
                )

            summary = entry.get("summary", "")
            content_list = entry.get("content", [])
            print(f"  * Summary len:  {len(summary)} chars")
            if content_list:
                c_type = content_list[0].get("type")
                c_val = content_list[0].get("value", "")
                print(
                    f"  * Content items:{len(content_list)} "
                    f"(type: {c_type}, {len(c_val)} chars)"
                )

            print(f"  * Available keys on entry #{idx}:")
            print(f"    {sorted(list(entry.keys()))}")

        if entries_count > shown:
            print(
                f"\n... and {entries_count - shown} more entries."
            )

    print(f"\n{'=' * 80}")
    print(">> Inspection Complete.")
    print(f"{'=' * 80}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect RSS/Atom feed details and explore feedparser output."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://24.hu/feed/",
        help="URL of the RSS/Atom feed to inspect (default: https://24.hu/feed/)",
    )
    parser.add_argument(
        "--max-entries",
        "-n",
        type=int,
        default=3,
        help="Maximum number of entries to display in detail (default: 3)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Dump parsed feed as raw JSON structure to stdout",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export parsed feed as a JSON file named by its ETag into the test/ directory",
    )

    args = parser.parse_args()
    inspect_feed(
        url=args.url,
        max_entries=args.max_entries,
        dump_json=args.json,
        export_json=args.export,
    )


if __name__ == "__main__":
    main()

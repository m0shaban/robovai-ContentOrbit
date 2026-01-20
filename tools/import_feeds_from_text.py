"""Import many RSS feed URLs into data/feeds.json.

Usage:
  python tools/import_feeds_from_text.py --input feeds.txt --language ar --category tech

- Expects one URL per line (comments starting with # are ignored).
- Deduplicates by URL.
- Auto-generates id/name when missing.

This script does not validate URLs online; it only updates feeds.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class FeedInput:
    url: str
    name: Optional[str] = None


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _norm_url(url: str) -> str:
    url = url.strip()
    url = re.sub(r"\s+", "", url)
    return url


def _guess_name(url: str) -> str:
    host = urlparse(url).netloc or url
    host = host.lower().replace("www.", "")
    return host


def _guess_category(url: str, default_category: str) -> str:
    u = url.lower()
    if any(k in u for k in ["ai", "ml", "machinelearning", "artificialintelligence"]):
        return "ai"
    if any(k in u for k in ["dev", "program", "python", "javascript", "node", "react", "css", "docker", "kubernetes"]):
        return "programming"
    if any(k in u for k in ["startup", "business", "saas", "marketing"]):
        return "business"
    return default_category


def _load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: List[Dict[str, Any]]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_urls(input_path: Path) -> List[FeedInput]:
    items: List[FeedInput] = []
    for raw in input_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Allow "Name | URL" lines.
        if "|" in line:
            left, right = [p.strip() for p in line.split("|", 1)]
            url = _norm_url(right)
            if url:
                items.append(FeedInput(url=url, name=left or None))
            continue
        url = _norm_url(line)
        if url:
            items.append(FeedInput(url=url))
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Text file with one RSS URL per line")
    parser.add_argument("--feeds", default="data/feeds.json", help="Path to feeds.json")
    parser.add_argument("--language", choices=["ar", "en"], default="ar")
    parser.add_argument("--category", default="tech", help="Default category when not inferred")
    parser.add_argument("--priority", type=int, default=5)
    parser.add_argument("--active", action="store_true", help="Mark imported feeds as active")

    args = parser.parse_args()

    input_path = Path(args.input)
    feeds_path = Path(args.feeds)

    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 2

    feeds = _load_json(feeds_path)
    existing_urls = {str(f.get("url", "")).strip().lower() for f in feeds}

    new_items = _read_urls(input_path)
    added = 0

    for item in new_items:
        url = item.url
        if not url.lower().startswith(("http://", "https://")):
            continue
        key = url.strip().lower()
        if key in existing_urls:
            continue

        feed_id = f"feed_{args.language}_{len(feeds) + 1}"
        name = item.name or _guess_name(url)
        category = _guess_category(url, args.category)

        feeds.append(
            {
                "id": feed_id,
                "name": name,
                "url": url,
                "category": category,
                "language": args.language,
                "is_active": bool(args.active),
                "priority": args.priority,
                "last_fetched": None,
                "created_at": _now_iso(),
            }
        )
        existing_urls.add(key)
        added += 1

    _save_json(feeds_path, feeds)
    print(f"Added {added} feed(s). Total now: {len(feeds)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import feedparser
import httpx


ALLOWED_CATEGORIES = {
    "tech",
    "business",
    "ai",
    "programming",
    "news",
    "lifestyle",
    "education",
    "other",
}


def _load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: List[Dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _norm_url(url: str) -> str:
    url = (url or "").strip()
    url = re.sub(r"\s+", "", url)
    return url


def _arabic_ratio(text: str) -> float:
    if not text:
        return 0.0
    arabic = sum(1 for ch in text if "\u0600" <= ch <= "\u06ff")
    return arabic / max(1, len(text))


def _looks_mojibake(text: str) -> bool:
    if not text:
        return False
    # Common UTF-8->Latin-1 mojibake markers.
    return (
        any(m in text for m in ["Ã", "Â", "Ø", "Ù", "â€", "™", "œ"])
        and _arabic_ratio(text) < 0.05
    )


def _try_fix_mojibake_once(text: str) -> Optional[str]:
    # Common cases:
    # - UTF-8 bytes decoded as latin1 -> contains ØÙ
    # - UTF-8 bytes decoded as cp1252 -> contains â€™ â€œ ™ etc
    for enc in ("latin1", "cp1252"):
        try:
            fixed = text.encode(enc, errors="strict").decode("utf-8", errors="strict")
        except Exception:
            continue

        if fixed != text:
            return fixed

    return None


def fix_text(text: str) -> Tuple[str, bool]:
    if not text:
        return text, False

    if not _looks_mojibake(text):
        return text, False

    best = text
    best_score = _arabic_ratio(text)

    candidate = _try_fix_mojibake_once(text)
    if candidate:
        score = _arabic_ratio(candidate)
        if score > best_score:
            best, best_score = candidate, score

        # Sometimes it was double-mangled.
        candidate2 = _try_fix_mojibake_once(candidate)
        if candidate2:
            score2 = _arabic_ratio(candidate2)
            if score2 > best_score:
                best, best_score = candidate2, score2

    changed = best != text
    return best, changed


def normalize_category(cat: str) -> str:
    c = (cat or "other").strip().lower()
    if c in ALLOWED_CATEGORIES:
        return c

    # Some legacy values
    mapping = {
        "artificial intelligence": "ai",
        "machine learning": "ai",
        "dev": "programming",
        "security": "news",
        "cyber": "news",
    }
    return mapping.get(c, "other")


@dataclass
class ValidateResult:
    ok: bool
    reason: str
    status_code: Optional[int] = None


def validate_feed(url: str, client: httpx.Client) -> ValidateResult:
    try:
        resp = client.get(url)
    except Exception as e:
        return ValidateResult(False, f"request_error:{type(e).__name__}")

    status = resp.status_code

    if status in (404, 410):
        return ValidateResult(False, "http_not_found", status)

    # TooManyRequests/Forbidden: could be temporary or UA-based.
    if status in (401, 403, 429):
        return ValidateResult(True, f"http_{status}_kept", status)

    if status < 200 or status >= 400:
        return ValidateResult(False, f"http_{status}", status)

    content = resp.content or b""
    parsed = feedparser.parse(content)

    has_entries = bool(getattr(parsed, "entries", None)) and len(parsed.entries) > 0
    has_title = bool(getattr(getattr(parsed, "feed", None), "title", ""))

    if has_entries or has_title:
        return ValidateResult(True, "ok", status)

    # If parser failed and we got no content, mark as invalid.
    if getattr(parsed, "bozo", 0) and not has_entries and not has_title:
        return ValidateResult(False, "invalid_feed", status)

    return ValidateResult(False, "not_a_feed", status)


async def validate_feed_async(url: str, client: httpx.AsyncClient) -> ValidateResult:
    try:
        resp = await client.get(url)
    except Exception as e:
        return ValidateResult(False, f"request_error:{type(e).__name__}")

    status = resp.status_code

    if status in (404, 410):
        return ValidateResult(False, "http_not_found", status)

    if status in (401, 403, 429):
        return ValidateResult(True, f"http_{status}_kept", status)

    if status < 200 or status >= 400:
        return ValidateResult(False, f"http_{status}", status)

    content = resp.content or b""
    parsed = feedparser.parse(content)

    has_entries = bool(getattr(parsed, "entries", None)) and len(parsed.entries) > 0
    has_title = bool(getattr(getattr(parsed, "feed", None), "title", ""))

    if has_entries or has_title:
        return ValidateResult(True, "ok", status)

    if getattr(parsed, "bozo", 0) and not has_entries and not has_title:
        return ValidateResult(False, "invalid_feed", status)

    return ValidateResult(False, "not_a_feed", status)


async def _validate_active_feeds(
    active_feeds: List[Dict[str, Any]],
    timeout_seconds: float,
    disable_invalid: bool,
    headers: Dict[str, str],
    concurrency: int = 20,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    disabled: List[Dict[str, Any]] = []
    kept_warn: List[Dict[str, Any]] = []

    limits = httpx.Limits(
        max_connections=concurrency, max_keepalive_connections=concurrency
    )
    timeout = httpx.Timeout(
        timeout_seconds,
        connect=timeout_seconds,
        read=timeout_seconds,
        write=timeout_seconds,
        pool=timeout_seconds,
    )

    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers=headers,
        limits=limits,
    ) as client:

        async def one(feed: Dict[str, Any]) -> None:
            url = str(feed.get("url", ""))
            if not url:
                return
            async with sem:
                result = await validate_feed_async(url, client)

            if result.ok:
                if result.reason != "ok":
                    kept_warn.append(
                        {
                            "url": url,
                            "reason": result.reason,
                            "status": result.status_code,
                        }
                    )
                return

            if disable_invalid:
                feed["is_active"] = False
                disabled.append(
                    {"url": url, "reason": result.reason, "status": result.status_code}
                )

        await asyncio.gather(*(one(f) for f in active_feeds))

    return disabled, kept_warn


def dedupe_feeds(feeds: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_url: Dict[str, Dict[str, Any]] = {}
    for f in feeds:
        url = _norm_url(str(f.get("url", "")))
        if not url:
            continue
        key = url.lower()

        if key not in by_url:
            by_url[key] = f
            continue

        # Prefer active, then higher priority.
        existing = by_url[key]
        score_existing = (
            1 if existing.get("is_active") else 0,
            int(existing.get("priority") or 0),
        )
        score_new = (1 if f.get("is_active") else 0, int(f.get("priority") or 0))
        if score_new > score_existing:
            by_url[key] = f

    return list(by_url.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feeds", default="data/feeds.json")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument(
        "--max", type=int, default=200, help="Max feeds to validate (active only)"
    )
    parser.add_argument(
        "--disable-invalid", action="store_true", help="Disable invalid active feeds"
    )
    parser.add_argument(
        "--skip-validate", action="store_true", help="Skip online validation"
    )
    args = parser.parse_args()

    feeds_path = Path(args.feeds)
    feeds = _load_json(feeds_path)

    before_active = sum(1 for f in feeds if f.get("is_active"))

    # Normalize + fix names
    fixed_names = 0
    for f in feeds:
        f["url"] = _norm_url(str(f.get("url", "")))
        f["category"] = normalize_category(str(f.get("category", "other")))
        lang = str(f.get("language", "en")).strip().lower()
        if lang.startswith("ar"):
            f["language"] = "ar"
        elif lang.startswith("en"):
            f["language"] = "en"
        elif re.match(r"^[a-z]{2}(-[a-z]{2})?$", lang):
            f["language"] = lang.split("-", 1)[0]
        else:
            f["language"] = "en"

        name = str(f.get("name", "")).strip()
        fixed, changed = fix_text(name)
        if changed:
            f["name"] = fixed
            fixed_names += 1

    feeds = dedupe_feeds(feeds)

    # Validate active feeds online
    headers = {
        "User-Agent": "ContentOrbitFeedValidator/1.0 (+https://robovai.com)",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    }

    disabled: List[Dict[str, Any]] = []
    kept_warn: List[Dict[str, Any]] = []

    if not args.skip_validate:
        active_feeds = [f for f in feeds if f.get("is_active")]
        active_feeds = active_feeds[: max(0, int(args.max))]

        try:
            disabled, kept_warn = asyncio.run(
                _validate_active_feeds(
                    active_feeds=active_feeds,
                    timeout_seconds=float(args.timeout),
                    disable_invalid=bool(args.disable_invalid),
                    headers=headers,
                )
            )
        except KeyboardInterrupt:
            print("Interrupted: saving partial cleanup results...")

    after_active = sum(1 for f in feeds if f.get("is_active"))

    _save_json(feeds_path, feeds)

    print(f"TOTAL={len(feeds)}")
    print(f"ACTIVE_BEFORE={before_active}")
    print(f"ACTIVE_AFTER={after_active}")
    print(f"FIXED_NAMES={fixed_names}")
    print(f"DISABLED={len(disabled)}")
    if disabled:
        print("DISABLED_LIST=")
        for d in disabled[:50]:
            print(f"- {d['url']} ({d['reason']} {d.get('status')})")
    if kept_warn:
        print(f"KEPT_WITH_WARN={len(kept_warn)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

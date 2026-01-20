"""Add curated Chinese/Russian/Japanese RSS sources into data/feeds.json.

Goal: push total feeds to at least a target count (default: 150).

This script only appends (dedupe by URL). Validation/disable can be done via tools/clean_feeds.py.

Usage:
  python tools/add_international_feeds.py --feeds data/feeds.json --target 150
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: List[Dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _norm_url(url: str) -> str:
    return (url or "").strip()


def curated_feeds() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    # ── Japan (ja)
    nhk = [
        ("NHK News (総合)", "https://www3.nhk.or.jp/rss/news/cat0.xml", "news"),
        ("NHK News (社会)", "https://www3.nhk.or.jp/rss/news/cat1.xml", "news"),
        ("NHK News (政治)", "https://www3.nhk.or.jp/rss/news/cat2.xml", "news"),
        ("NHK News (国際)", "https://www3.nhk.or.jp/rss/news/cat3.xml", "news"),
        ("NHK News (経済)", "https://www3.nhk.or.jp/rss/news/cat4.xml", "business"),
        ("NHK News (エンタメ)", "https://www3.nhk.or.jp/rss/news/cat5.xml", "news"),
        ("NHK News (スポーツ)", "https://www3.nhk.or.jp/rss/news/cat6.xml", "news"),
        ("NHK News (科学・医療)", "https://www3.nhk.or.jp/rss/news/cat7.xml", "tech"),
        ("NHK News (地域)", "https://www3.nhk.or.jp/rss/news/cat8.xml", "news"),
    ]
    for name, url, cat in nhk:
        items.append(
            {
                "name": name,
                "url": url,
                "category": cat,
                "language": "ja",
                "priority": 4,
                "is_active": True,
            }
        )

    qiita_tags = [
        ("Qiita: python", "https://qiita.com/tags/python/feed", "programming"),
        ("Qiita: javascript", "https://qiita.com/tags/javascript/feed", "programming"),
        ("Qiita: typescript", "https://qiita.com/tags/typescript/feed", "programming"),
        ("Qiita: react", "https://qiita.com/tags/react/feed", "programming"),
        ("Qiita: vue", "https://qiita.com/tags/vue.js/feed", "programming"),
        ("Qiita: docker", "https://qiita.com/tags/docker/feed", "programming"),
        ("Qiita: kubernetes", "https://qiita.com/tags/kubernetes/feed", "programming"),
        ("Qiita: aws", "https://qiita.com/tags/aws/feed", "programming"),
        ("Qiita: gcp", "https://qiita.com/tags/gcp/feed", "programming"),
        ("Qiita: azure", "https://qiita.com/tags/azure/feed", "programming"),
        ("Qiita: devops", "https://qiita.com/tags/devops/feed", "programming"),
        ("Qiita: security", "https://qiita.com/tags/security/feed", "news"),
        ("Qiita: machine learning", "https://qiita.com/tags/machine-learning/feed", "ai"),
        ("Qiita: deep learning", "https://qiita.com/tags/deep-learning/feed", "ai"),
        ("Qiita: llm", "https://qiita.com/tags/llm/feed", "ai"),
        ("Qiita: openai", "https://qiita.com/tags/openai/feed", "ai"),
        ("Qiita: data science", "https://qiita.com/tags/data-science/feed", "ai"),
        ("Qiita: flutter", "https://qiita.com/tags/flutter/feed", "programming"),
    ]
    for name, url, cat in qiita_tags:
        items.append(
            {
                "name": name,
                "url": url,
                "category": cat,
                "language": "ja",
                "priority": 4,
                "is_active": True,
            }
        )

    # ── Russia (ru)
    ru_items = [
        ("Habr (All)", "https://habr.com/ru/rss/all/all/?fl=ru", "programming"),
        ("Habr Hub: AI", "https://habr.com/ru/hubs/artificial_intelligence/rss/", "ai"),
        ("Habr Hub: ML", "https://habr.com/ru/hubs/machine_learning/rss/", "ai"),
        ("Habr Hub: DevOps", "https://habr.com/ru/hubs/devops/rss/", "programming"),
        ("Habr Hub: InfoSec", "https://habr.com/ru/hubs/infosecurity/rss/", "news"),
        ("Habr Hub: Python", "https://habr.com/ru/hubs/python/rss/", "programming"),
        ("RT (RSS)", "https://www.rt.com/rss/", "news"),
        ("Tproger", "https://tproger.ru/feed/", "programming"),
        ("Kaspersky Blog", "https://www.kaspersky.com/blog/feed/", "news"),
        ("Yandex Blog", "https://yandex.com/blog/rss.xml", "tech"),
    ]
    for name, url, cat in ru_items:
        items.append(
            {
                "name": name,
                "url": url,
                "category": cat,
                "language": "ru",
                "priority": 4,
                "is_active": True,
            }
        )

    # ── China (zh)
    zh_items = [
        ("阮一峰的网络日志", "http://www.ruanyifeng.com/blog/atom.xml", "programming"),
        ("酷壳 CoolShell", "https://coolshell.cn/feed", "programming"),
        ("少数派 SSPAI", "https://sspai.com/feed", "tech"),
        ("Solidot", "https://www.solidot.org/index.rss", "tech"),
        ("OSCHINA News", "https://www.oschina.net/news/rss", "tech"),
        ("InfoQ China", "https://www.infoq.cn/feed.xml", "programming"),
        ("TechNode", "https://technode.com/feed/", "tech"),
        ("PingWest 品玩", "https://www.pingwest.com/feed", "tech"),
        ("36Kr", "https://36kr.com/feed", "business"),
        ("虎嗅 Huxiu", "https://www.huxiu.com/rss/0.xml", "business"),
    ]
    for name, url, cat in zh_items:
        items.append(
            {
                "name": name,
                "url": url,
                "category": cat,
                "language": "zh",
                "priority": 4,
                "is_active": True,
            }
        )

    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feeds", default="data/feeds.json")
    parser.add_argument("--target", type=int, default=150)
    args = parser.parse_args()

    feeds_path = Path(args.feeds)
    feeds = _load_json(feeds_path)

    existing = {str(f.get("url", "")).strip().lower() for f in feeds}
    added = 0

    for item in curated_feeds():
        url = _norm_url(item["url"])
        if not url.startswith(("http://", "https://")):
            continue
        key = url.lower()
        if key in existing:
            continue

        lang = str(item.get("language", "en")).strip().lower() or "en"
        feed_id = f"feed_{lang}_{len(feeds) + 1}"

        feeds.append(
            {
                "id": feed_id,
                "name": item["name"],
                "url": url,
                "category": item.get("category", "other"),
                "language": lang,
                "is_active": bool(item.get("is_active", True)),
                "priority": int(item.get("priority", 4)),
                "last_fetched": None,
                "created_at": _now_iso(),
            }
        )
        existing.add(key)
        added += 1

    _save_json(feeds_path, feeds)

    print(f"ADDED={added}")
    print(f"TOTAL={len(feeds)}")
    if len(feeds) < int(args.target):
        print(f"WARNING: total {len(feeds)} is still below target {args.target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

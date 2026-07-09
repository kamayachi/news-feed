# -*- coding: utf-8 -*-
"""Google News RSSから過去24時間のニュースを取得し news/latest.json に保存する。標準ライブラリのみ使用。"""
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

THEMES = {
    "ai": [
        "生成AI OR 人工知能 OR AI規制",
        "OpenAI OR Anthropic OR Google AI OR AIモデル",
    ],
    "semiconductor": [
        "半導体 OR TSMC OR ラピダス OR キオクシア",
        "半導体 工場 OR 増産 OR 補助金 OR 投資",
    ],
    "carbon_neutral": [
        "カーボンニュートラル OR 脱炭素 OR GX",
        "再生可能エネルギー OR 太陽光 OR 洋上風力 OR 水素",
    ],
    "industry": [
        "設備投資 OR 新工場 OR 増産 発表",
        "資本業務提携 OR 買収 OR 中期経営計画 OR 新規事業",
    ],
}

MAX_ITEMS_PER_QUERY = 12
UA = "Mozilla/5.0 (compatible; news-fetcher/1.0)"


def fetch_rss(query: str):
    q = urllib.parse.quote(f"{query} when:1d")
    url = f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    items = []
    for item in root.iter("item"):
        source = item.find("source")
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "pubDate": (item.findtext("pubDate") or "").strip(),
            "source": (source.text or "").strip() if source is not None else "",
        })
        if len(items) >= MAX_ITEMS_PER_QUERY:
            break
    return items


def main():
    out = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "themes": {},
    }
    for theme, queries in THEMES.items():
        seen = set()
        merged = []
        for q in queries:
            try:
                for it in fetch_rss(q):
                    key = it["title"]
                    if key and key not in seen:
                        seen.add(key)
                        merged.append(it)
            except Exception as e:
                print(f"WARN: {theme} / {q}: {e}")
        out["themes"][theme] = merged
        print(f"{theme}: {len(merged)} items")

    os.makedirs("news", exist_ok=True)
    with open("news/latest.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    with open("news/latest.md", "w", encoding="utf-8") as f:
        f.write(f"# News feed ({out['generated_at_utc']})\n\n")
        for theme, items in out["themes"].items():
            f.write(f"## {theme}\n\n")
            for it in items:
                f.write(f"- [{it['title']}]({it['link']}) — {it['source']} ({it['pubDate']})\n")
            f.write("\n")


if __name__ == "__main__":
    main()

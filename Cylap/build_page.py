#!/usr/bin/env python3
"""Builds honeylens_live.html: the HoneyLens design with real news from news.json.
Open honeylens_live.html by double-clicking it. Standard library only."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
MARKER = '/*NEWS_JSON*/{"updated":"","items":[]}'


def build():
    tpl = (BASE / "honeylens_template.html").read_text(encoding="utf-8")
    if MARKER not in tpl:
        raise RuntimeError("honeylens_template.html is missing the news marker")
    news_file = BASE / "news.json"
    if news_file.exists():
        news = json.loads(news_file.read_text(encoding="utf-8"))
    else:
        news = {"updated": "", "items": []}
    data = (json.dumps(news, ensure_ascii=False)
            .replace("</", "<\\/").replace("<!--", "<\\!--").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
    out = BASE / "honeylens_live.html"
    out.write_text(tpl.replace(MARKER, data), encoding="utf-8")
    print(f"Built {out.name} with {len(news.get('items', []))} stories")


if __name__ == "__main__":
    build()

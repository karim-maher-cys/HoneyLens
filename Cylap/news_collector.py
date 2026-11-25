#!/usr/bin/env python3
"""HoneyLens news collector.

Reads security RSS/Atom feeds, removes duplicates, tags each story,
stores everything in SQLite and exports news.json for the dashboard.
Standard library only: no pip install needed (Python 3.8+).
"""
import hashlib, html, json, logging, re, sqlite3, sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "news.db"
JSON_PATH = BASE / "news.json"
KEEP_DAYS = 90
EXPORT_LIMIT = 200
TIMEOUT = 20

FEEDS = {
    "CISA": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
}

TAGS = {
    "Ransomware": r"ransomware|lockbit|blackcat|alphv|extortion|ransom",
    "Vulnerability": r"cve-\d{4}-\d+|vulnerab|zero-day|0-day|patch|exploit|rce\b",
    "Data breach": r"data breach|breach|leak|exposed|stolen data|compromised",
    "Malware": r"malware|trojan|botnet|infostealer|stealer|backdoor|spyware|loader",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("collector")


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def clean(text, limit=300):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[: limit - 1] + "…" if len(text) > limit else text


def parse_date(value):
    if not value:
        return datetime.now(timezone.utc)
    value = value.strip()
    try:
        d = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def local(tag):
    return tag.rsplit("}", 1)[-1]


def child_text(node, *names):
    for c in node:
        if local(c.tag) in names and (c.text or "").strip():
            return c.text
    return ""


def parse_feed(xml_bytes):
    """Return list of dicts: title, link, summary, published (RSS 2.0 and Atom)."""
    root = ET.fromstring(xml_bytes)
    items = []
    for node in root.iter():
        kind = local(node.tag)
        if kind not in ("item", "entry"):
            continue
        link = child_text(node, "link")
        if not link:  # Atom stores the URL in href
            for c in node:
                if local(c.tag) == "link" and c.get("href"):
                    if c.get("rel", "alternate") == "alternate":
                        link = c.get("href")
                        break
        title = clean(child_text(node, "title"), 200)
        if not title or not link:
            continue
        items.append({
            "title": title,
            "link": link.strip(),
            "summary": clean(child_text(node, "description", "summary", "content", "encoded")),
            "published": parse_date(child_text(node, "pubDate", "published", "updated", "date")),
        })
    return items


def tag_for(title, summary):
    text = f"{title} {summary}".lower()
    for tag, pattern in TAGS.items():
        if re.search(pattern, text):
            return tag
    return "General"


def init_db(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS news(
        id TEXT PRIMARY KEY, title TEXT, link TEXT, summary TEXT,
        source TEXT, tag TEXT, published TEXT)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pub ON news(published)")


def save(conn, source, items):
    added = 0
    for it in items:
        uid = hashlib.sha256(it["link"].split("#")[0].encode()).hexdigest()[:24]
        cur = conn.execute(
            "INSERT OR IGNORE INTO news VALUES (?,?,?,?,?,?,?)",
            (uid, it["title"], it["link"], it["summary"], source,
             tag_for(it["title"], it["summary"]), it["published"].isoformat()))
        added += cur.rowcount
    return added


def export_json(conn):
    rows = conn.execute(
        "SELECT title, link, summary, source, tag, published FROM news "
        "ORDER BY published DESC LIMIT ?", (EXPORT_LIMIT,)).fetchall()
    data = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": [dict(zip(("title", "link", "summary", "source", "tag", "published"), r)) for r in rows],
    }
    tmp = JSON_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(JSON_PATH)  # atomic: the dashboard never reads a half-written file
    return len(rows)


def run(feeds=None, fetcher=fetch):
    feeds = feeds or FEEDS
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    total_new, failed = 0, []
    for name, url in feeds.items():
        try:
            items = parse_feed(fetcher(url))
            n = save(conn, name, items)
            conn.commit()
            total_new += n
            log.info("%s: %d items, %d new", name, len(items), n)
        except Exception as e:  # one broken feed must never stop the others
            failed.append(name)
            log.warning("%s failed: %s", name, e)
    conn.execute("DELETE FROM news WHERE published < datetime('now', ?)", (f"-{KEEP_DAYS} days",))
    conn.commit()
    exported = export_json(conn)
    conn.close()
    log.info("Done. new=%d exported=%d failed=%s", total_new, exported, failed or "none")
    return 1 if len(failed) == len(feeds) else 0


if __name__ == "__main__":
    code = run()
    try:  # rebuild the pretty HTML page after every collection
        import build_page
        build_page.build()
    except Exception as e:
        log.warning("page build skipped: %s", e)
    sys.exit(code)

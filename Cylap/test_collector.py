import json, sqlite3, news_collector as nc

RSS = b"""<?xml version="1.0"?><rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<item><title>LockBit affiliate arrested</title><link>https://a.example/1</link>
<description>&lt;p&gt;Police seize &lt;b&gt;ransomware&lt;/b&gt; servers&lt;/p&gt;</description>
<pubDate>Tue, 10 Nov 2026 08:30:00 GMT</pubDate></item>
<item><title>Patch for CVE-2026-1234 released</title><link>https://a.example/2</link>
<description>Critical flaw fixed</description><pubDate>Mon, 09 Nov 2026 10:00:00 +0200</pubDate></item>
<item><title>No link item</title></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>New infostealer found</title><link rel="alternate" href="https://b.example/9"/>
<summary>Stealer malware spreads via fake installers</summary><updated>2026-11-08T12:00:00Z</updated></entry>
<entry><title>Weekly roundup</title><link href="https://b.example/10"/><updated>bad-date</updated></entry>
</feed>"""

def fake(url):
    if "rss" in url: return RSS
    if "atom" in url: return ATOM
    if "broken" in url: return b"<html>not xml"
    raise OSError("network down")

feeds = {"RSS": "http://x/rss", "ATOM": "http://x/atom", "BROKEN": "http://x/broken", "DOWN": "http://x/down"}
assert nc.run(feeds, fake) == 0
d = json.load(open("news.json", encoding="utf-8"))
tags = {i["title"]: i["tag"] for i in d["items"]}
print(tags)
assert len(d["items"]) == 4
assert tags["LockBit affiliate arrested"] == "Ransomware"
assert tags["Patch for CVE-2026-1234 released"] == "Vulnerability"
assert tags["New infostealer found"] == "Malware"
assert tags["Weekly roundup"] == "General"
assert "<" not in d["items"][0]["summary"]
# second run must not duplicate
nc.run(feeds, fake)
assert len(json.load(open("news.json"))["items"]) == 4
# all feeds failing -> exit code 1
assert nc.run({"DOWN": "http://x/down"}, fake) == 1
print("ALL TESTS PASSED")

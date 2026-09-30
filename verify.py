#!/usr/bin/env python3
"""
Check what a crawler that doesn't run JavaScript sees.

    python3 verify.py                                        # the local build in ./public
    python3 verify.py path/to/dir
    python3 verify.py https://workshops.senseandrespond.co   # the live site

Reads the raw index.html and workshops.json from the same place and fails (exit 1) unless:

    - the workshop titles in the HTML <h2 class="ws-title">s match the titles in workshops.json exactly
    - the JSON-LD parses and has one Event per workshop, with matching names
    - every <time> has a YYYY-MM-DD datetime, and every workshop has an anchor id
    - robots.txt, sitemap.xml and llms.txt are present

Standard library only.
"""

import html.parser
import json
import os
import re
import sys
import urllib.request
from collections import Counter

USER_AGENT = "sr-workshops-mirror-verify/1.0 (+https://senseandrespond.co)"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


class PageParser(html.parser.HTMLParser):
    """Collects workshop <h2 class="ws-title"> titles, article ids, <time datetime>s and JSON-LD blocks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titles, self.article_ids, self.times, self.jsonld = [], [], [], []
        self._in_h2 = self._in_ld = False
        self._buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h2" and "ws-title" in (a.get("class") or "").split():
            self._in_h2, self._buf = True, []
        elif tag == "article":
            self.article_ids.append(a.get("id"))
        elif tag == "time":
            self.times.append(a.get("datetime"))
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld, self._buf = True, []

    def handle_endtag(self, tag):
        if tag == "h2" and self._in_h2:
            self.titles.append(" ".join("".join(self._buf).split()))
            self._in_h2 = False
        elif tag == "script" and self._in_ld:
            self.jsonld.append("".join(self._buf))
            self._in_ld = False

    def handle_data(self, data):
        if self._in_h2 or self._in_ld:
            self._buf.append(data)


def fetch(base, name):
    if re.match(r"https?://", base):
        req = urllib.request.Request(f"{base.rstrip('/')}/{name}", headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8")
        except OSError:
            return None
    path = os.path.join(base, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main(argv):
    base = argv[1] if len(argv) > 1 else "public"
    problems = []

    # On the live site, fetch "/" rather than "/index.html": that's the URL crawlers request.
    page = fetch(base, "" if re.match(r"https?://", base) else "index.html")
    feed = fetch(base, "workshops.json")
    if page is None or feed is None:
        print(f"FAIL: could not read index.html and workshops.json from {base}")
        return 1

    expected = [e["title"] for e in json.loads(feed)["events"]]
    p = PageParser()
    p.feed(page)

    if Counter(p.titles) != Counter(expected):
        missing = Counter(expected) - Counter(p.titles)
        extra = Counter(p.titles) - Counter(expected)
        problems.append(f"titles differ. Missing from HTML: {sorted(missing)}. "
                        f"Extra in HTML: {sorted(extra)}")

    events = []
    for block in p.jsonld:
        try:
            doc = json.loads(block)
        except ValueError as exc:
            problems.append(f"JSON-LD does not parse: {exc}")
            continue
        nodes = doc.get("@graph", [doc]) if isinstance(doc, dict) else doc
        events += [n for n in nodes if n.get("@type") == "Event"]
    if Counter(e.get("name") for e in events) != Counter(expected):
        problems.append(f"JSON-LD has {len(events)} Event(s), names don't match workshops.json")
    for e in events:
        for field in ("startDate", "endDate", "url", "eventAttendanceMode", "organizer", "offers"):
            if field not in e:
                problems.append(f"JSON-LD Event {e.get('name')!r} lacks {field}")

    if len(p.article_ids) != len(expected) or not all(p.article_ids):
        problems.append("not every workshop has an anchor id")
    bad_times = [t for t in p.times if not t or not DATE_RE.match(t)]
    if bad_times:
        problems.append(f"<time> without a YYYY-MM-DD datetime: {bad_times}")

    for name in ("robots.txt", "sitemap.xml", "llms.txt"):
        if fetch(base, name) is None:
            problems.append(f"{name} missing")

    if problems:
        for msg in problems:
            print(f"FAIL: {msg}")
        return 1
    print(f"OK: {len(expected)} workshop title(s) in the raw HTML match workshops.json. "
          f"{len(events)} JSON-LD Event(s), {len(p.times)} <time> element(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

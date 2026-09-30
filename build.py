#!/usr/bin/env python3
"""
Build a static mirror of the Sense & Respond Learning public workshops page.

Reads upcoming events from Ti.to and writes two files into ./public:

    public/workshops.json   - structured data feed
    public/index.html      - a standalone, styled, crawlable page

Data sources, in order of preference:
    1. Ti.to Admin API   (set TITO_API_TOKEN) - structured dates, locations, prices
    2. Public timeline   (no token needed)    - scraped from ti.to/<account>

Environment variables:
    TITO_API_TOKEN   Ti.to API token. Optional; falls back to scraping.
    TITO_ACCOUNT     Account slug. Default: sense-respond-learning
    OUT_DIR          Output directory. Default: ./public
    DEDUPE           "true" (default) collapses events with an identical
                     title + start + end + location into one card.
    SITE_URL         Canonical URL of the published mirror, for <link rel=canonical>.
"""

import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

ACCOUNT = os.environ.get("TITO_ACCOUNT", "sense-respond-learning")
TOKEN = os.environ.get("TITO_API_TOKEN", "").strip()
OUT_DIR = os.environ.get("OUT_DIR", "public")
DEDUPE = os.environ.get("DEDUPE", "true").lower() not in ("false", "0", "no")
SITE_URL = os.environ.get("SITE_URL", "").strip()

TIMELINE_URL = f"https://ti.to/{ACCOUNT}/"
API_BASE = f"https://api.tito.io/v2/{ACCOUNT}"
USER_AGENT = "sr-workshops-mirror/1.0 (+https://senseandrespond.co)"

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "CA$", "AUD": "A$"}


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# --------------------------------------------------------------------------
# Source 1: Ti.to Admin API
# --------------------------------------------------------------------------

def fetch_from_api():
    """Return a list of event dicts, or raise."""
    headers = {
        "Authorization": f"Token token={TOKEN}",
        "Accept": "application/vnd.api+json",
    }
    url = f"{API_BASE}/events?include=releases"
    events, included, guard = [], [], 0

    while url and guard < 25:
        guard += 1
        payload = json.loads(get(url, headers))
        events.extend(payload.get("data") or [])
        included.extend(payload.get("included") or [])
        url = ((payload.get("links") or {}).get("next")) or None

    # id -> release attributes, so we can price each event
    releases = {r["id"]: r.get("attributes", {}) for r in included if r.get("type") == "releases"}

    today = dt.date.today()
    out = []
    for ev in events:
        a = ev.get("attributes", {}) or {}

        # Skip anything the public can't buy.
        if a.get("private") or a.get("test-mode") or not a.get("live", True):
            continue

        start = parse_date(a.get("start-date"))
        end = parse_date(a.get("end-date")) or start
        if end and end < today:
            continue  # already finished

        rel_ids = [
            r.get("id")
            for r in (((ev.get("relationships") or {}).get("releases") or {}).get("data") or [])
        ]
        price, currency = cheapest_price(rel_ids, releases, a.get("currency"))

        slug = a.get("slug") or ev.get("id")
        out.append({
            "title": (a.get("title") or "").strip(),
            "slug": slug,
            "url": f"https://ti.to/{ACCOUNT}/{slug}",
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "date_label": format_range(start, end),
            "location": (a.get("location") or "").strip() or None,
            "banner": a.get("banner-url"),
            "price_from": price,
            "currency": currency,
        })

    return out


def cheapest_price(rel_ids, releases, fallback_currency):
    """Lowest price across the releases a member of the public could actually buy."""
    prices = []
    for rid in rel_ids:
        r = releases.get(rid)
        if not r or r.get("archived") or r.get("secret") or r.get("not-a-ticket"):
            continue
        p = r.get("price")
        if p is None:
            continue
        try:
            prices.append(float(p))
        except (TypeError, ValueError):
            continue
    return (min(prices) if prices else None), (fallback_currency or "USD")


def parse_date(value):
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Source 2: public timeline scrape (no token required)
# --------------------------------------------------------------------------

EVENT_BLOCK = re.compile(r'<div class="tito-event">(.*?)(?=<div class="tito-event">|$)', re.S)
LINK_RE = re.compile(r'<a href="([^"]+)" class="tito-event--event-link"')
TITLE_RE = re.compile(r'<h2 class="tito-event--title">(.*?)</h2>', re.S)
TIME_RE = re.compile(r'<div class="tito-event--time">(.*?)</div>', re.S)
LOC_RE = re.compile(r'<div class="tito-event--location">(.*?)</div>', re.S)
BANNER_RE = re.compile(r'<img src="([^"]+)" class="tito-event--banner"')


def fetch_from_timeline():
    """Parse the server-rendered public timeline. Upcoming events only."""
    page = get(TIMELINE_URL)

    # The timeline renders upcoming events first, then a past-events section.
    cuts = [
        page.find(m)
        for m in ('class="tito-events--unscheduled"', 'class="tito-events--past"', "Past events")
    ]
    cuts = [c for c in cuts if c != -1]
    upcoming = page[: min(cuts)] if cuts else page

    out = []
    for chunk in EVENT_BLOCK.findall(upcoming):
        link = LINK_RE.search(chunk)
        title = TITLE_RE.search(chunk)
        if not link or not title:
            continue
        loc = LOC_RE.search(chunk)
        banner = BANNER_RE.search(chunk)
        time_label = TIME_RE.search(chunk)
        url = html.unescape(link.group(1))
        out.append({
            "title": clean(title.group(1)),
            "slug": url.rstrip("/").rsplit("/", 1)[-1],
            "url": url,
            "start": None,
            "end": None,
            "date_label": clean(time_label.group(1)) if time_label else "",
            "location": clean(loc.group(1)) if loc else None,
            "banner": html.unescape(banner.group(1)) if banner else None,
            "price_from": None,
            "currency": None,
        })
    return out


def clean(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------

def ordinal(n):
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def format_range(start, end):
    """Match Ti.to's own phrasing: 'September 17th-October 8th, 2026'."""
    if not start:
        return ""
    if not end or end == start:
        return f"{start:%B} {ordinal(start.day)}, {start.year}"
    if (start.year, start.month) == (end.year, end.month):
        return f"{start:%B} {ordinal(start.day)}–{ordinal(end.day)}, {start.year}"
    if start.year == end.year:
        return f"{start:%B} {ordinal(start.day)}–{end:%B} {ordinal(end.day)}, {start.year}"
    return (f"{start:%B} {ordinal(start.day)}, {start.year}–"
            f"{end:%B} {ordinal(end.day)}, {end.year}")


def format_price(amount, currency):
    if amount is None:
        return None
    symbol = CURRENCY_SYMBOLS.get((currency or "").upper(), "")
    whole = int(amount)
    body = f"{whole:,}" if abs(amount - whole) < 0.005 else f"{amount:,.2f}"
    return f"{symbol}{body}" if symbol else f"{body} {currency}"


def dedupe(events):
    """Collapse rows that are indistinguishable to a visitor. Returns (kept, dropped)."""
    seen, kept, dropped = {}, [], []
    for e in events:
        key = (e["title"].lower(), e.get("start"), e.get("end"), e["date_label"],
               (e.get("location") or "").lower())
        if key in seen:
            dropped.append(e)
        else:
            seen[key] = True
            kept.append(e)
    return kept, dropped


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def card_html(e):
    esc = html.escape
    price = format_price(e.get("price_from"), e.get("currency"))
    meta = [m for m in (e.get("date_label"), e.get("location") or "Live online") if m]

    bits = [f'  <article class="srw-card">']
    if e.get("banner"):
        bits.append(
            f'    <a class="srw-banner" href="{esc(e["url"])}" tabindex="-1" aria-hidden="true">'
            f'<img src="{esc(e["banner"])}" alt="" loading="lazy"></a>'
        )
    bits.append('    <div class="srw-body">')
    bits.append(f'      <h3 class="srw-title"><a href="{esc(e["url"])}">{esc(e["title"])}</a></h3>')
    bits.append(f'      <p class="srw-meta">{esc(" · ".join(meta))}</p>')
    if price:
        bits.append(f'      <p class="srw-price">From {esc(price)}</p>')
    bits.append(
        f'      <a class="srw-cta" href="{esc(e["url"])}">Register'
        f'<span class="srw-sr">: {esc(e["title"])}</span></a>'
    )
    bits.append('    </div>')
    bits.append('  </article>')
    return "\n".join(bits)


STYLES = """
:root{
  --srw-ink:#101617; --srw-muted:#5a6a6c; --srw-teal:#345C60; --srw-teal-bright:#038A98;
  --srw-lime:#E2F46F; --srw-paper:#F9FAF0; --srw-card:#FFFFFF; --srw-line:#e3e6d9;
  --srw-head:'Oswald',Impact,sans-serif; --srw-body:'Roboto',Helvetica,Arial,sans-serif;
}
.srw{font-family:var(--srw-body);color:var(--srw-ink);}
.srw *{box-sizing:border-box;}
.srw-grid{display:grid;gap:22px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
  list-style:none;margin:0;padding:0;}
.srw-card{display:flex;flex-direction:column;background:var(--srw-card);
  border:1px solid var(--srw-line);border-radius:14px;overflow:hidden;
  transition:transform .15s ease,box-shadow .15s ease;}
.srw-card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(16,22,23,.10);}
.srw-banner{display:block;line-height:0;background:var(--srw-paper);}
.srw-banner img{width:100%;height:auto;display:block;}
.srw-body{display:flex;flex-direction:column;gap:10px;padding:20px 20px 22px;flex:1;}
.srw-title{font-family:var(--srw-head);font-weight:400;font-size:1.32rem;line-height:1.22;
  letter-spacing:-.01em;margin:0;}
.srw-title a{color:var(--srw-ink);text-decoration:none;}
.srw-title a:hover{color:var(--srw-teal-bright);}
.srw-meta{margin:0;font-size:.875rem;color:var(--srw-muted);line-height:1.5;}
.srw-price{margin:0;font-size:.875rem;font-weight:600;color:var(--srw-teal);}
.srw-cta{margin-top:auto;align-self:flex-start;background:var(--srw-teal);color:#fff;
  text-decoration:none;font-size:.86rem;font-weight:500;padding:9px 22px;border-radius:300px;
  transition:background .15s ease;}
.srw-cta:hover{background:var(--srw-teal-bright);color:#fff;}
.srw-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);
  clip-path:inset(50%);white-space:nowrap;}
.srw-foot{margin:26px 0 0;font-size:.78rem;color:var(--srw-muted);}
.srw-foot a{color:var(--srw-teal);}
.srw-empty{margin:0;padding:28px;border:1px dashed var(--srw-line);border-radius:14px;
  background:var(--srw-card);color:var(--srw-muted);}
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Public Workshops | Sense &amp; Respond Learning</title>
<meta name="description" content="Upcoming public workshops from Sense &amp; Respond Learning: product management, discovery, OKRs and storytelling training.">
{canonical}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:var(--srw-paper);padding:48px 20px 64px;}}
.srw-wrap{{max-width:1120px;margin:0 auto;}}
.srw-h1{{font-family:var(--srw-head);font-weight:400;font-size:clamp(2rem,5vw,3.1rem);
  letter-spacing:-.02em;margin:0 0 10px;}}
.srw-lede{{margin:0 0 36px;max-width:60ch;color:var(--srw-muted);font-size:1.02rem;line-height:1.6;}}
{styles}
</style>
</head>
<body>
<div class="srw srw-wrap">
  <h1 class="srw-h1">Public Workshops</h1>
  <p class="srw-lede">Product management, discovery, OKRs and storytelling training and workshops.
     Open to individuals &mdash; book a seat below.</p>
  <div class="srw-grid">
{cards}
  </div>
  <p class="srw-foot">Workshop list last updated {updated}. Tickets are sold and fulfilled through
     <a href="{timeline}">Ti.to</a>.</p>
</div>
<script type="application/ld+json">{schema}</script>
</body>
</html>
"""


def render_page(events, updated):
    if events:
        cards = "\n".join(card_html(e) for e in events)
    else:
        cards = ('  <p class="srw-empty">No public workshops are scheduled right now. '
                 f'Check <a href="{TIMELINE_URL}">our ticketing page</a> for the latest.</p>')

    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Event",
                    "name": e["title"],
                    "url": e["url"],
                    **({"startDate": e["start"]} if e.get("start") else {}),
                    **({"endDate": e["end"]} if e.get("end") else {}),
                    "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
                    "organizer": {"@type": "Organization",
                                  "name": "Sense & Respond Learning",
                                  "url": "https://senseandrespond.co"},
                },
            }
            for i, e in enumerate(events)
        ],
    }

    canonical = f'<link rel="canonical" href="{html.escape(SITE_URL)}">' if SITE_URL else ""
    return PAGE.format(
        canonical=canonical,
        styles=STYLES,
        cards=cards,
        updated=updated,
        timeline=TIMELINE_URL,
        schema=json.dumps(schema, ensure_ascii=False),
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    source = "api"
    if TOKEN:
        try:
            events = fetch_from_api()
            print(f"Ti.to API: {len(events)} upcoming event(s).")
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError) as exc:
            print(f"WARNING: API fetch failed ({exc}); falling back to the public timeline.")
            events, source = fetch_from_timeline(), "timeline-fallback"
    else:
        print("No TITO_API_TOKEN set; reading the public timeline.")
        events, source = fetch_from_timeline(), "timeline"

    events.sort(key=lambda e: (e.get("start") or "9999", e["title"].lower()))

    dropped = []
    if DEDUPE:
        events, dropped = dedupe(events)
        for d in dropped:
            print(f"  deduped: {d['title']} ({d['slug']})")

    for e in events:
        e["price_label"] = format_price(e.get("price_from"), e.get("currency"))

    previous = os.path.join(OUT_DIR, "workshops.json")
    prior_events, prior_updated = None, None
    if os.path.exists(previous):
        try:
            with open(previous, encoding="utf-8") as fh:
                prior = json.load(fh)
            prior_events, prior_updated = prior.get("events"), prior.get("updated")
        except (ValueError, OSError):
            pass

    # A total wipeout is almost always a transient upstream problem, not an
    # empty calendar. Refuse to publish an empty page over a good one.
    if not events and prior_events:
        print("ERROR: fetched 0 event(s) but the last good build had "
              f"{len(prior_events)}. Keeping the existing files.")
        return 1

    # Nothing changed upstream, so don't touch the files. This keeps the
    # timestamp on the page honest (it means "the list changed then", not
    # "a job ran then") and keeps the repo free of no-op commits.
    if events == prior_events:
        print(f"No change: {len(events)} event(s), same as the last build "
              f"({prior_updated}). Nothing written.")
        return 0

    updated = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(os.path.join(OUT_DIR, "workshops.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "account": ACCOUNT,
            "source": source,
            "updated": updated,
            "updated_iso": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "ticketing_url": TIMELINE_URL,
            "count": len(events),
            "deduped": len(dropped),
            "events": events,
        }, fh, ensure_ascii=False, indent=2)

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(render_page(events, updated))

    print(f"Wrote {len(events)} event(s) to {OUT_DIR}/ (source: {source}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

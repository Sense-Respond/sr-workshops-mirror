#!/usr/bin/env python3
"""
Build the Sense & Respond Learning public workshops page.

Reads upcoming events from Ti.to and writes a static, server-rendered site into ./public:

    public/index.html      - the page. Every workshop is in the HTML; no JavaScript
    public/workshops.json  - the same data as JSON, and the "last good build" record
    public/robots.txt      - welcomes search and AI crawlers
    public/sitemap.xml
    public/llms.txt        - plain-text summary for LLMs

Data sources:
    1. Ti.to Admin API   (set TITO_API_TOKEN) - structured dates, locations, prices.
                         If the token is set and the API fails, the build exits 1 and
                         writes nothing.
    2. Public timeline   (no token)           - scraped from ti.to/<account>. For local
                         runs only. Since late September 2026 the timeline renders its
                         events client-side, so this returns nothing.

Options:
    --from-json PATH  Build from a saved workshops.json, e.g. docs/sample-workshops.json
    --force           Write even when the data and template are unchanged

Environment variables:
    TITO_API_TOKEN   Ti.to API token.
    TITO_ACCOUNT     Account slug. Default: sense-respond-learning
    OUT_DIR          Output directory. Default: ./public
    DEDUPE           "true" (default) collapses events with an identical
                     title + start + end + location into one card.
    SITE_URL         Canonical URL. Default: https://workshops.senseandrespond.co
"""

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zoneinfo

ACCOUNT = os.environ.get("TITO_ACCOUNT", "sense-respond-learning")
TOKEN = os.environ.get("TITO_API_TOKEN", "").strip()
OUT_DIR = os.environ.get("OUT_DIR", "public")
DEDUPE = os.environ.get("DEDUPE", "true").lower() not in ("false", "0", "no")
SITE_URL = (os.environ.get("SITE_URL", "").strip()
            or "https://workshops.senseandrespond.co").rstrip("/")

# Bump whenever the rendered output changes, so the no-change guard lets the new design ship.
TEMPLATE_VERSION = 7

TIMELINE_URL = f"https://ti.to/{ACCOUNT}/"
API_BASE = f"https://api.tito.io/v3/{ACCOUNT}"
USER_AGENT = "sr-workshops-mirror/1.0 (+https://senseandrespond.co)"

# Google Analytics 4: the main site's property, so senseandrespond.co and this subdomain report
# together. Default cookie settings (cookie_domain auto) share sessions across the two.
GA_MEASUREMENT_ID = "G-WPJMQ52FEF"
# Ti.to Source Tracking: appended to every on-page link to an event, so Ti.to can attribute
# orders to this page. The source must also be saved on each event in the Ti.to dashboard.
TITO_SOURCE = "workshops-page"

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "CA$", "AUD": "A$", "INR": "₹"}


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# --------------------------------------------------------------------------
# Source 1: Ti.to Admin API v3 (v2 was retired; it 404s as of 30 September 2026)
# --------------------------------------------------------------------------

def api_get_all(path, key, headers):
    """GET a v3 list endpoint, following meta.next_page. Returns the items under `key`."""
    items, page, guard = [], 1, 0
    while page and guard < 25:
        guard += 1
        query = urllib.parse.urlencode({"page[number]": page, "page[size]": 100})
        payload = json.loads(get(f"{API_BASE}/{path}?{query}", headers))
        items.extend(payload.get(key) or [])
        page = (payload.get("meta") or {}).get("next_page")
    return items


def fetch_from_api():
    """Return a list of event dicts, or raise. Ti.to Admin API v3."""
    headers = {
        "Authorization": f"Token token={TOKEN}",
        "Accept": "application/json",
    }
    events = api_get_all("events", "events", headers)  # upcoming events only, per the v3 docs

    today = dt.date.today()
    out = []
    for a in events:
        # Skip anything the public can't buy.
        if a.get("private") or a.get("test_mode") or not a.get("live", True):
            continue

        start = parse_date(a.get("start_date"))
        end = parse_date(a.get("end_date")) or start
        if start and start <= today:
            continue  # started or finished: in-progress workshops aren't listed
        if end and end < today:
            continue  # already finished

        slug = a.get("slug") or str(a.get("id"))
        releases = api_get_all(f"{slug}/releases", "releases", headers)
        by_id = {r.get("id"): r for r in releases}
        price, currency = cheapest_price(list(by_id), by_id, a.get("currency"))

        banner = banner_url(a.get("banner_url") or ((a.get("banner") or {}).get("url")
                                         if isinstance(a.get("banner"), dict) else None))
        out.append({
            "title": (a.get("title") or "").strip(),
            "slug": slug,
            "url": f"https://ti.to/{ACCOUNT}/{slug}",
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "date_label": format_range(start, end),
            "location": (a.get("location") or "").strip() or None,
            "banner": banner,
            "price_from": price,
            "currency": currency,
            "start_at": a.get("start_at"),
            "end_at": a.get("end_at"),
            "timezone": a.get("timezone"),
            "sold_out": sold_out(releases),
            "region": region_from_description(a.get("description")),
        })

    return out


def is_public_release(r):
    """A release a member of the public could actually buy."""
    return bool(r) and not (r.get("archived") or r.get("secret") or r.get("not_a_ticket"))


def release_sold_out(r):
    return bool(r.get("sold_out") or r.get("state_name") == "sold_out")


def cheapest_price(rel_ids, releases, fallback_currency):
    """Lowest price across the releases a member of the public could buy right now."""
    prices = []
    for rid in rel_ids:
        r = releases.get(rid)
        if not is_public_release(r) or release_sold_out(r):
            continue
        p = r.get("price")
        if p is None:
            continue
        try:
            prices.append(float(p))
        except (TypeError, ValueError):
            continue
    return (min(prices) if prices else None), (fallback_currency or "USD")


def sold_out(releases):
    """True if every public release is sold out, False if any isn't, None if there are none."""
    public = [r for r in releases if is_public_release(r)]
    if not public:
        return None
    return all(release_sold_out(r) for r in public)


# S&R marks a regional cohort with a globe icon on the first line of the Ti.to description,
# e.g. '<i class="fa-light fa-globe"></i> Americas & Europe'. Same-title, same-date events
# for different regions are separate cohorts, not duplicates.
REGION_RE = re.compile(r'fa-globe[^>]*>(?:\s*</i>)?\s*([^<\r\n]+)')


def region_from_description(description):
    m = REGION_RE.search(description or "") if isinstance(description, str) else None
    return (clean(m.group(1)).strip(" *_") or None) if m else None


def banner_url(value):
    # Ti.to v3 returns banner_url with the full URL appended to its own folder, e.g.
    # ".../banner/1164882/https://.../banner/1164882/x.png", which CloudFront rejects (403).
    # Keep the last full URL in the string.
    if not isinstance(value, str) or not value.strip():
        return None
    i = value.rfind("https://")
    return value[i:] if i > 0 else value.strip()


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


# Ti.to can report time zones by their Rails names. Map the ones our workshops use to IANA
# zones so we can show a proper abbreviation. Unknown names fall back to a UTC offset.
RAILS_ZONES = {
    "Eastern Time (US & Canada)": "America/New_York",
    "Central Time (US & Canada)": "America/Chicago",
    "Mountain Time (US & Canada)": "America/Denver",
    "Pacific Time (US & Canada)": "America/Los_Angeles",
    "London": "Europe/London", "Dublin": "Europe/Dublin", "Lisbon": "Europe/Lisbon",
    "Berlin": "Europe/Berlin", "Bern": "Europe/Zurich", "Vienna": "Europe/Vienna",
    "Amsterdam": "Europe/Amsterdam", "Paris": "Europe/Paris", "Madrid": "Europe/Madrid",
    "Rome": "Europe/Rome", "Stockholm": "Europe/Stockholm",
    "Chennai": "Asia/Kolkata", "Kolkata": "Asia/Kolkata", "Mumbai": "Asia/Kolkata",
    "New Delhi": "Asia/Kolkata", "Buenos Aires": "America/Argentina/Buenos_Aires",
    "Brasilia": "America/Sao_Paulo", "Mexico City": "America/Mexico_City",
    "Bogota": "America/Bogota", "Singapore": "Asia/Singapore", "Sydney": "Australia/Sydney",
    "UTC": "UTC",
}


def parse_datetime(value):
    """ISO 8601 datetime with an offset, or None. Accepts a trailing Z."""
    if not value:
        return None
    try:
        d = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else None


def event_zone(name):
    try:
        return zoneinfo.ZoneInfo(RAILS_ZONES.get(name, name)) if name else None
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        return None


def local_times(e):
    """(start, end) as aware datetimes in the event's own zone, or (None, None)."""
    start, end = parse_datetime(e.get("start_at")), parse_datetime(e.get("end_at"))
    if not start or not end:
        return None, None
    zone = event_zone(e.get("timezone"))
    if zone:
        start, end = start.astimezone(zone), end.astimezone(zone)
    # Ti.to fills start_at/end_at with midnight when no session time was entered.
    if (start.hour, start.minute, end.hour, end.minute) == (0, 0, 0, 0):
        return None, None
    return start, end


def zone_label(d):
    """'CDT' where the zone has a real abbreviation, else 'UTC+05:30'."""
    name = d.tzname() or ""
    if re.fullmatch(r"[A-Z]{2,5}", name):
        return name
    off = d.utcoffset()
    mins = int(off.total_seconds() // 60)
    sign = "+" if mins >= 0 else "-"
    return f"UTC{sign}{abs(mins) // 60:02d}:{abs(mins) % 60:02d}"


def clock(d):
    return f"{d.hour % 12 or 12}:{d.minute:02d}"


def format_times(start, end):
    """Daily session time, e.g. '9:00–11:00 AM CDT' or '11:00 AM–1:00 PM CEST'."""
    if not start or not end:
        return ""
    ms, me = ("AM" if start.hour < 12 else "PM"), ("AM" if end.hour < 12 else "PM")
    first = clock(start) if ms == me else f"{clock(start)} {ms}"
    return f"{first}–{clock(end)} {me} {zone_label(start)}"


def zone_name(tz):
    """Readable zone name: 'Central Time, US & Canada', 'Berlin', 'Buenos Aires'."""
    if "/" in tz:
        return tz.rsplit("/", 1)[-1].replace("_", " ")
    return tz.replace(" (", ", ").replace(")", "")


def format_zone(e):
    """'Time zone: CDT (Central Time, US & Canada)' when Ti.to has a zone but no times.

    Skips "UTC": it is Ti.to's default, and on 30 September 2026 every event marked UTC was a
    regional cohort whose real session times span several zones.
    """
    tz = (e.get("timezone") or "").strip()
    start = parse_date(e.get("start"))
    if not tz or tz.upper() in ("UTC", "ETC/UTC") or not start:
        return ""
    zone = event_zone(tz)
    if not zone:
        return f"Time zone: {tz}"
    abbr = zone_label(dt.datetime(start.year, start.month, start.day, 12, tzinfo=zone))
    name = zone_name(tz)
    return f"Time zone: {abbr} ({name})" if name != abbr else f"Time zone: {abbr}"


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
               (e.get("location") or "").lower(), (e.get("region") or "").lower())
        if key in seen:
            dropped.append(e)
        else:
            seen[key] = True
            kept.append(e)
    return kept, dropped



# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

ORGANIZER = {"@type": "Organization", "@id": "https://senseandrespond.co/#org",
             "name": "Sense & Respond Learning", "url": "https://senseandrespond.co"}

# Treated as online: no location at all, or one that says "online" or "zoom" in any case.
ONLINE_RE = re.compile(r"\b(online|zoom)\b", re.I)

# Crawlers robots.txt names explicitly. Goal 2 of the brief.
AI_CRAWLERS = ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "CCBot")


def is_online(location):
    return not location or bool(ONLINE_RE.search(location))


def anchor_id(slug):
    return re.sub(r"[^a-z0-9-]+", "-", (slug or "").lower()).strip("-") or "workshop"


def date_range_html(e):
    """format_range() with each date wrapped in <time datetime>. Same visible text."""
    start, end = parse_date(e.get("start")), parse_date(e.get("end"))
    if not start:
        return html.escape(e.get("date_label") or "")

    def t(d, text):
        return f'<time datetime="{d.isoformat()}">{text}</time>'

    if not end or end == start:
        return t(start, f"{start:%B} {ordinal(start.day)}, {start.year}")
    if (start.year, start.month) == (end.year, end.month):
        return (t(start, f"{start:%B} {ordinal(start.day)}") + "–"
                + t(end, f"{ordinal(end.day)}, {end.year}"))
    if start.year == end.year:
        return (t(start, f"{start:%B} {ordinal(start.day)}") + "–"
                + t(end, f"{end:%B} {ordinal(end.day)}, {end.year}"))
    return (t(start, f"{start:%B} {ordinal(start.day)}, {start.year}") + "–"
            + t(end, f"{end:%B} {ordinal(end.day)}, {end.year}"))


def time_range_html(e):
    """format_times() with both ends wrapped in <time datetime>. Empty if Ti.to gave no times."""
    start, end = local_times(e)
    text = format_times(start, end)
    if not text:
        return ""
    first, rest = text.split("–", 1)
    return (f'<time datetime="{start.isoformat(timespec="minutes")}">{html.escape(first)}</time>–'
            f'<time datetime="{end.isoformat(timespec="minutes")}">{html.escape(rest)}</time>')


def tracked_url(url):
    """The event URL with ?source= added, for links on the page. JSON-LD and llms.txt keep the
    plain URL, so crawlers and assistants see the canonical address."""
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    query = [(k, v) for k, v in query if k != "source"] + [("source", TITO_SOURCE)]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def place_label(e):
    return "Live online" if is_online(e.get("location")) else e["location"]


def card_html(e, anchor):
    esc = html.escape
    url = esc(tracked_url(e["url"]))
    price = format_price(e.get("price_from"), e.get("currency"))

    bits = [f'<article class="ws" id="{esc(anchor)}">']
    if e.get("banner"):
        bits.append(f'  <a class="ws-banner" href="{url}" tabindex="-1" aria-hidden="true">'
                    f'<img src="{esc(e["banner"])}" alt="" loading="lazy" decoding="async"></a>')
    bits += [
        '  <div class="ws-body">',
        f'    <h2 class="ws-title"><a href="{url}">{esc(e["title"])}</a></h2>',
        '    <div class="ws-facts">',
        f'      <p class="ws-when">{date_range_html(e)}</p>',
    ]
    times = time_range_html(e) or html.escape(format_zone(e))
    if times:
        bits.append(f'      <p class="ws-time">{times}</p>')
    if e.get("region"):
        bits.append(f'      <p class="ws-region">{esc(e["region"])}</p>')
    bits += [
        f'      <p class="ws-where">{esc(place_label(e))}</p>',
        '    </div>',
        '    <div class="ws-action">',
    ]
    if e.get("sold_out"):
        bits.append('      <p class="ws-price">Sold out</p>')
    elif price:
        bits.append(f'      <p class="ws-price">From {esc(price)}</p>')
    cta = "See details" if e.get("sold_out") else "Register"
    bits += [
        f'      <a class="btn" href="{url}">{cta}<span class="sr">: {esc(e["title"])}</span></a>',
        '    </div>',
        '  </div>',
        '</article>',
    ]
    return "\n".join(bits)


# Values measured from senseandrespond.co's computed styles on 2026-10-01, at 390, 768, 1024
# and 1440px wide (see docs/BRAND-SPEC.md, "Live site values"). The live site is the design
# reference (decided 2026-10-01); the brand guide fills in where it is silent. Squarespace
# scales type with the viewport, so sizes are clamp()s fitted to the measured points.
STYLES = """
:root{
  --black:#000000; --white:#FFFFFF; --chalk:#F9FAF0; --slate:#58585A; --iron:#39393D;
  --teal:#345C60; --lime:#E2F46F;
  --head:'Oswald','Arial Narrow',Impact,sans-serif;
  --body:'Roboto',Helvetica,Arial,sans-serif;
  --gutter:4vw;
}
*{box-sizing:border-box;}
html{-webkit-text-size-adjust:100%;}
body{margin:0;background:var(--white);color:var(--black);
  font:400 clamp(17px,16.1px + .25vw,19.73px)/1.6 var(--body);letter-spacing:.01em;}
a{color:var(--teal);}
a:focus-visible{outline:3px solid var(--iron);outline-offset:3px;}
img{max-width:100%;}
.wrap{max-width:1400px;margin:0 auto;padding:0 var(--gutter);}
.col{max-width:960px;margin:0 auto;}

/* Top bar. Logo 50px tall as on the live site, with the guide's clear space (50% of the
   logo's height, 25px) on every side. */
.top{background:var(--white);}
.top .wrap{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;
  gap:0 24px;}
.logo{display:block;padding:25px 0;line-height:0;}
.logo img{height:50px;width:auto;}

/* Hero: Natalia's white-to-gradient background behind the H1 and intro. */
.hero{background:var(--white) url("assets/hero-gradient.jpg") center bottom/cover no-repeat;
  padding:clamp(32px,5vw,72px) 0 clamp(56px,8vw,120px);}
h1{font:400 clamp(48px,18px + 4.2vw,78.48px)/1.032 var(--head);letter-spacing:-.02em;
  margin:0 0 clamp(32px,4vw,56px);}
.eyebrow{font-weight:700;color:var(--slate);margin:0 0 4px;}
.lede-head{font:400 clamp(38px,17.9px + 3vw,61.2px)/1.08 var(--head);letter-spacing:-.02em;
  margin:0 0 16px;}
.lede{max-width:40em;margin:0;}
mark{background:var(--lime);color:inherit;padding:0 .1em;
  -webkit-box-decoration-break:clone;box-decoration-break:clone;}

/* Buttons: the live site's primary button. Pill, Deep Teal, Roboto 600, hover fades to 80%. */
.btn{display:inline-block;background:var(--teal);color:var(--white);border-radius:300px;
  font:600 clamp(14.92px,14.4px + .13vw,16.27px)/normal var(--body);text-transform:capitalize;
  text-decoration:none;padding:1.106em 1.438em;transition:opacity .1s linear;}
.btn:hover{opacity:.8;}
/* Text links: the live site's tertiary button. Hover fills Deep Teal with white text. */
.link{display:inline-block;color:var(--teal);font:600 clamp(14.92px,14.4px + .13vw,16.27px)/normal var(--body);
  text-decoration:none;padding:.22em 0;transition:background-color .1s linear,color .1s linear;}
.link:hover{background:var(--teal);color:var(--white);}

/* Workshop list: one per row, banner across the card, details on white below (as on ti.to). */
.list{background:var(--chalk);padding:clamp(40px,5vw,80px) 0 clamp(56px,7vw,104px);}
.ws-list{display:grid;gap:clamp(24px,3vw,40px);}
.ws{background:var(--white);border-radius:16px;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,.08),0 4px 16px rgba(0,0,0,.04);}
.ws-banner{display:block;line-height:0;}
.ws-banner img{display:block;width:100%;height:auto;}
.ws-body{padding:28px 36px 32px;}
.ws-title{font:400 clamp(23px,21.5px + .36vw,26.64px)/1.176 var(--head);letter-spacing:-.02em;
  margin:0 0 12px;}
.ws-title a{color:var(--black);text-decoration:none;}
.ws-title a:hover{text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:4px;}
.ws-facts{color:var(--slate);margin:0 0 24px;}
.ws-facts p{margin:0;}
.ws-when{font-weight:700;}
.ws-action{display:flex;flex-wrap:wrap;align-items:center;gap:12px 28px;}
.ws-price{margin:0;font-weight:700;}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);
  clip-path:inset(50%);white-space:nowrap;}
.empty{background:var(--white);border-radius:16px;padding:28px 36px;margin:0;}

/* Cookie consent: the live site's banner. Fixed bar, Chalk, small text, a text-link button
   and a pill button. Hidden until the script shows it, so it never appears without JS. */
.consent{position:fixed;left:0;right:0;bottom:0;z-index:1000;background:var(--chalk);
  display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 20px;
  padding:14px 20px;box-shadow:0 -1px 0 rgba(0,0,0,.06);}
.consent[hidden]{display:none;}
.consent p{margin:0;flex:1 1 32em;font-size:clamp(13.84px,13.6px + .07vw,14.54px);line-height:1.6;}
.consent-actions{display:flex;gap:14px;align-items:center;}
.consent button{font:600 12px/normal var(--body);padding:11px 15px;border:0;cursor:pointer;}
.consent .decline{background:none;color:#038A98;}
.consent .decline:hover{background:var(--teal);color:var(--white);}
.consent .accept{background:var(--teal);color:var(--white);border-radius:300px;
  text-transform:capitalize;transition:opacity .1s linear;}
.consent .accept:hover{opacity:.8;}
.consent button:focus-visible{outline:3px solid var(--iron);outline-offset:3px;}

.site-foot{color:var(--slate);font-size:clamp(14.92px,14.4px + .13vw,16.27px);padding:40px 0 56px;}
.site-foot p{margin:0 0 8px;}

@media (max-width:767px){
  :root{--gutter:6vw;}
  .ws-body{padding:20px 20px 24px;}
}
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Public Workshops | Sense &amp; Respond Learning</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{site}/">
<link rel="icon" href="assets/sr-logomark.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:title" content="Public Workshops | Sense &amp; Respond Learning">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{site}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400&family=Roboto:wght@400;600;700&display=swap" rel="stylesheet">
<style>{styles}</style>
<script type="application/ld+json">{schema}</script>
<script>{analytics}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
</head>
<body>
<header class="top">
  <div class="wrap">
    <a class="logo" href="https://senseandrespond.co"><img src="assets/sr-logo.svg" alt="Sense &amp; Respond Learning" width="156" height="50"></a>
    <a class="link" href="https://www.senseandrespond.co/individuals">← Back to senseandrespond.co</a>
  </div>
</header>
<section class="hero">
  <div class="wrap">
    <div class="col">
      <h1>Public Workshops</h1>
      <p class="eyebrow">FLEXIBLE FORMATS</p>
      <h2 class="lede-head">{lede_head}</h2>
      <p class="lede">{lede}</p>
    </div>
  </div>
</section>
<main class="list">
  <div class="wrap">
    <div class="col ws-list">
{cards}
    </div>
  </div>
</main>
<footer class="site-foot">
  <div class="wrap">
    <p>List updated <time datetime="{updated_iso}">{updated}</time>.
       Tickets are sold through <a href="{timeline}">Ti.to</a>.</p>
    <p><a href="https://senseandrespond.co">Sense &amp; Respond Learning</a></p>
  </div>
</footer>
<section class="consent" id="consent" aria-label="Cookie consent" hidden>
  <p>Select “Accept all” to agree to our use of cookies and similar technologies for analytics. Select “Decline” to opt out.</p>
  <div class="consent-actions">
    <button type="button" class="decline" data-consent="denied">Decline</button>
    <button type="button" class="accept" data-consent="granted">Accept all</button>
  </div>
</section>
</body>
</html>
"""

DESCRIPTION = ("Upcoming workshops from Sense & Respond Learning: live training in Product "
               "Management, Lean UX, Product Discovery, OKRs, Outcomes, and Storytelling.")
LEDE_HEAD = "Build these skills, your way"
LEDE = ("Our training is available in person or online, live and interactive, delivered "
        "on-site or remotely, wherever you’re located. Created by Jeff Gothelf and Josh Seiden, "
        "and led by our Certified Training Partners worldwide, you get the same training, in "
        "the format that fits.")
# The key phrase in the lede, highlighted in Key Lime as the live site does.
LEDE_HIGHLIGHT = "you get the same training, in the format that fits"


# Google Consent Mode v2. Everything is denied until the visitor accepts; the choice is kept in
# localStorage and reapplied on later visits. With storage denied, gtag sends cookieless pings
# only. This script and gtag.js are the only JavaScript besides the JSON-LD. Neither touches
# the workshop list, which stays server-rendered (decided 2026-10-01).
# On "Accept all" the page view is sent again: the first one went out cookieless and GA
# doesn't report it, so a first visit would otherwise lose its traffic source (Jeff,
# 2026-10-06). No double count, since the cookieless one isn't reported.
ANALYTICS_JS = """
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
(function () {
  var KEY = "sr-consent", choice = null;
  try { choice = localStorage.getItem(KEY); } catch (e) {}
  function consent(v) {
    return {ad_storage: v, ad_user_data: v, ad_personalization: v, analytics_storage: v};
  }
  gtag("consent", "default", consent(choice === "granted" ? "granted" : "denied"));
  gtag("js", new Date());
  gtag("config", "%s");
  if (choice === "granted" || choice === "denied") return;
  document.addEventListener("DOMContentLoaded", function () {
    var banner = document.getElementById("consent");
    if (!banner) return;
    banner.hidden = false;
    banner.addEventListener("click", function (ev) {
      var v = ev.target.closest("[data-consent]");
      if (!v) return;
      v = v.getAttribute("data-consent");
      try { localStorage.setItem(KEY, v); } catch (e) {}
      gtag("consent", "update", consent(v));
      if (v === "granted") gtag("event", "page_view");
      banner.hidden = true;
    });
  });
})();
""" % GA_MEASUREMENT_ID


def event_schema(e, anchor):
    online = is_online(e.get("location"))
    start_at, end_at = local_times(e)
    ev = {
        "@type": "Event",
        "@id": f"{SITE_URL}/#{anchor}",
        "name": e["title"],
        "url": e["url"],
        **({"startDate": start_at.isoformat() if start_at else e["start"]} if e.get("start") else {}),
        **({"endDate": end_at.isoformat() if end_at else e["end"]} if e.get("end") else {}),
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/"
                               + ("OnlineEventAttendanceMode" if online
                                  else "OfflineEventAttendanceMode"),
        "location": ({"@type": "VirtualLocation", "url": e["url"]} if online
                     else {"@type": "Place", "name": e["location"], "address": e["location"]}),
        "organizer": {"@id": ORGANIZER["@id"]},
        **({"image": [e["banner"]]} if e.get("banner") else {}),
        **({"description": f'{e["region"]} cohort.'} if e.get("region") else {}),
    }
    offer = {"@type": "Offer", "url": e["url"]}
    if e.get("price_from") is not None:
        offer["price"] = f'{e["price_from"]:.2f}'
        offer["priceCurrency"] = (e.get("currency") or "USD").upper()
    if e.get("sold_out") is not None:
        offer["availability"] = ("https://schema.org/SoldOut" if e["sold_out"]
                                 else "https://schema.org/InStock")
    ev["offers"] = offer
    return ev


def json_for_script(obj):
    """JSON safe to embed in <script>: a title containing </script> can't close the tag."""
    return (json.dumps(obj, ensure_ascii=False, indent=1)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def assign_anchors(events):
    """One unique anchor id per event, from its slug."""
    seen, out = set(), []
    for e in events:
        base = anchor_id(e.get("slug"))
        a, n = base, 2
        while a in seen:
            a, n = f"{base}-{n}", n + 1
        seen.add(a)
        out.append(a)
    return out


def render_page(events, updated, updated_iso):
    anchors = assign_anchors(events)
    if events:
        cards = "\n".join(card_html(e, a) for e, a in zip(events, anchors))
    else:
        cards = ('<p class="empty">No public workshops are scheduled right now. '
                 f'See <a href="{TIMELINE_URL}">our ticketing page</a> for the latest.</p>')

    schema = {"@context": "https://schema.org",
              "@graph": [ORGANIZER] + [event_schema(e, a) for e, a in zip(events, anchors)]}

    return PAGE.format(
        description=html.escape(DESCRIPTION),
        lede_head=html.escape(LEDE_HEAD),
        lede=html.escape(LEDE).replace(html.escape(LEDE_HIGHLIGHT),
                                        f"<mark>{html.escape(LEDE_HIGHLIGHT)}</mark>", 1),
        site=html.escape(SITE_URL),
        styles=STYLES,
        analytics=ANALYTICS_JS,
        ga_id=GA_MEASUREMENT_ID,
        schema=json_for_script(schema),
        cards=cards,
        updated=html.escape(updated),
        updated_iso=html.escape(updated_iso),
        timeline=TIMELINE_URL,
    )


def render_robots():
    lines = ["# Sense & Respond Learning public workshops. Crawlers, including AI crawlers, "
             "are welcome.", ""]
    for bot in AI_CRAWLERS + ("*",):
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines.append(f"Sitemap: {SITE_URL}/sitemap.xml")
    return "\n".join(lines) + "\n"


def render_sitemap(updated_iso):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'  <url>\n    <loc>{html.escape(SITE_URL)}/</loc>\n'
            f'    <lastmod>{updated_iso[:10]}</lastmod>\n  </url>\n'
            '</urlset>\n')


def render_llms(events, updated):
    def md(text):
        return re.sub(r"([\[\]])", r"\\\1", text)

    lines = [
        "# Sense & Respond Learning: public workshops",
        "",
        f"> {DESCRIPTION} Open to individuals. Tickets are sold through Ti.to.",
        "",
        f"This list was last updated {updated}. The full page is at {SITE_URL}/ and the same "
        f"data is at {SITE_URL}/workshops.json.",
        "",
        "## Upcoming workshops",
        "",
    ]
    if not events:
        lines.append(f"No public workshops are scheduled right now. See {TIMELINE_URL}")
    for e, a in zip(events, assign_anchors(events)):
        facts = [e.get("date_label") or "Dates to be announced"]
        times = format_times(*local_times(e)) or format_zone(e)
        if times:
            facts.append(times)
        if e.get("region"):
            facts.append(e["region"])
        facts.append(place_label(e))
        price = format_price(e.get("price_from"), e.get("currency"))
        if e.get("sold_out"):
            facts.append("Sold out")
        elif price:
            facts.append(f"From {price}")
        lines.append(f"- [{md(e['title'])}]({SITE_URL}/#{a}): {'. '.join(facts)}. "
                     f"Register at {e['url']}")
    lines += ["", "## About", "",
              "- [Sense & Respond Learning](https://senseandrespond.co): training, workshops "
              "and courses for product, design, innovation and Transformation leaders"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def parse_args(argv):
    p = argparse.ArgumentParser(description="Build the public workshops page from Ti.to.")
    p.add_argument("--from-json", metavar="PATH",
                   help="read events from a saved workshops.json instead of Ti.to (development)")
    p.add_argument("--force", action="store_true",
                   help="write the files even if the data and template are unchanged")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.from_json:
        with open(args.from_json, encoding="utf-8") as fh:
            events = json.load(fh)["events"]
        source = f"file:{os.path.basename(args.from_json)}"
        print(f"Read {len(events)} event(s) from {args.from_json}.")
    elif TOKEN:
        # With a token, the API is the only source. The timeline scrape has no dates or
        # prices, so falling back to it would publish a worse page and hide the failure.
        try:
            events, source = fetch_from_api(), "api"
            print(f"Ti.to API: {len(events)} upcoming event(s).")
            for e in events:
                if e.get("region"):
                    print(f"  region: {e['slug']} -> {e['region']}")
        except (OSError, ValueError, KeyError) as exc:
            print(f"ERROR: Ti.to API fetch failed ({exc}). Keeping the existing files.")
            return 1
    else:
        print("No TITO_API_TOKEN set; reading the public timeline.")
        events, source = fetch_from_timeline(), "timeline"

    # Slug breaks ties, so the same duplicate survives dedupe on every run.
    events.sort(key=lambda e: (e.get("start") or "9999", e["title"].lower(), e.get("slug") or ""))

    dropped = []
    if DEDUPE:
        events, dropped = dedupe(events)
        for d in dropped:
            print(f"  deduped: {d['title']} ({d['slug']})")

    for e in events:
        e["price_label"] = format_price(e.get("price_from"), e.get("currency"))

    previous = os.path.join(OUT_DIR, "workshops.json")
    prior_events, prior_updated, prior_template = None, None, None
    if os.path.exists(previous):
        try:
            with open(previous, encoding="utf-8") as fh:
                prior = json.load(fh)
            prior_events, prior_updated = prior.get("events"), prior.get("updated")
            prior_template = prior.get("template_version")
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
    # "a job ran then") and keeps the repo free of no-op commits. A new
    # TEMPLATE_VERSION counts as a change, so design changes still ship.
    if not args.force and events == prior_events and prior_template == TEMPLATE_VERSION:
        print(f"No change: {len(events)} event(s), same as the last build "
              f"({prior_updated}). Nothing written.")
        return 0

    now = dt.datetime.now(dt.timezone.utc)
    updated = now.strftime("%d %b %Y, %H:%M UTC")
    updated_iso = now.isoformat(timespec="seconds")

    feed = json.dumps({
        "account": ACCOUNT,
        "source": source,
        "updated": updated,
        "updated_iso": updated_iso,
        "template_version": TEMPLATE_VERSION,
        "ticketing_url": TIMELINE_URL,
        "count": len(events),
        "deduped": len(dropped),
        "events": events,
    }, ensure_ascii=False, indent=2)

    # Render everything before writing anything, so a render error can't leave a mix.
    outputs = {
        "index.html": render_page(events, updated, updated_iso),
        "robots.txt": render_robots(),
        "sitemap.xml": render_sitemap(updated_iso),
        "llms.txt": render_llms(events, updated),
        "workshops.json": feed,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, body in outputs.items():
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as fh:
            fh.write(body)

    print(f"Wrote {len(events)} event(s) to {OUT_DIR}/ (source: {source}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

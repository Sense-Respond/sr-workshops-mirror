# Code notes

## What's here

| File | Status |
|---|---|
| `build.py` | Partly reusable. Data layer is built and tested. Render layer targets the abandoned approach and needs rewriting |
| `docs/sample-workshops.json` | Real snapshot of 15 workshops, 18 September 2026. Use it to develop and test the renderer without hitting the API |
| `docs/DEPRECATED-squarespace-code-block.html` | Do not ship. Kept as a record of the wrong approach. See `docs/FINDINGS.md`, dead end 1 |

`build.py` has no dependencies beyond the Python standard library. Run it with
`python3 build.py`.

## build.py: keep these

This half is tested and correct. Don't rewrite it.

| Function | What it does |
|---|---|
| `fetch_from_api()` | Reads the Ti.to API, filters out private, test-mode, not-live and finished events |
| `cheapest_price()` | Lowest price across releases a member of the public can actually buy. Ignores archived, secret and not-a-ticket releases |
| `fetch_from_timeline()` | Scrapes the public timeline as a fallback when there's no token or the API errors. Correctly excludes past and unscheduled events |
| `format_range()` | Matches Ti.to's own date phrasing, e.g. "September 17th to October 8th, 2026" |
| `format_price()`, `ordinal()`, `parse_date()`, `clean()` | Small helpers |
| `dedupe()` | Collapses events identical on title + start + end + location |
| The guards in `main()` | Two behaviors worth preserving, described below |

### Two guards to preserve

**Won't publish an empty page over a good one.** If a build returns zero events but the last
good build had some, it exits non-zero without writing. A Ti.to outage or an expired token
then leaves yesterday's list up and fails the Action loudly, instead of wiping the page.

**Won't write when nothing changed.** If the event data matches the previous build, it writes
nothing. This keeps the repo free of no-op commits and makes the "last updated" date on the
page mean the list changed then, rather than a job ran then.

## build.py: rewrite these

The render layer was written for the abandoned Squarespace approach. It produces a card grid
that does not meet the brand spec or the crawlability criteria.

| Item | What's wrong |
|---|---|
| `card_html()` | No `<time datetime>`, no anchor id, no gradient date band. Uses `<h3>` where the page structure now wants `<h2>` |
| `STYLES` | Sampled from the live site, not built from the brand spec. Wrong type scale, no gradient |
| `PAGE` | No logo, no `robots`/`sitemap`/`llms` siblings, thin JSON-LD |
| `render_page()` | JSON-LD omits price and only handles `ItemList`. Needs full `Event` objects |

## build.py: add these

- `robots.txt` emitter, explicitly allowing GPTBot, ClaudeBot, PerplexityBot,
  Google-Extended, CCBot
- `sitemap.xml` emitter for the subdomain
- `llms.txt` emitter, a plain-text catalogue summary at the root
- Anchor id per workshop, derived from the Ti.to slug
- `<time datetime="YYYY-MM-DD">` alongside every human-readable date
- Full JSON-LD `Event` per workshop: name, startDate, endDate, offers with price and
  currency, url, eventAttendanceMode, organizer
- S&R logo, and a link back to senseandrespond.co

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TITO_API_TOKEN` | unset | With it, uses the API. Without it, scrapes the public timeline |
| `TITO_ACCOUNT` | `sense-respond-learning` | Account slug |
| `OUT_DIR` | `public` | Output directory. Matches the Netlify publish directory |
| `DEDUPE` | `true` | Collapses identical events |
| `SITE_URL` | unset | Canonical URL. Set to `https://workshops.senseandrespond.co` |

## Tests that were run

Worth re-running after the rewrite:

- Timeline scrape against real markup: 11 events parsed, past events correctly excluded,
  HTML entities unescaped, location captured
- Date formatting: same month, cross month, cross year, single day, missing date
- Ordinals: 11th, 12th, 13th, 21st, 2nd, 3rd
- Price formatting: whole, decimal, null, unknown currency symbol
- API path against a JSON:API fixture: private, test-mode, not-live and finished events all
  excluded; secret releases ignored when pricing; events ending today retained
- Location-aware dedupe: same title and dates but different locations are **not** collapsed
- Empty-page guard: fetching zero events with a good prior build exits 1 and changes nothing
- No-op guard: an identical second run writes nothing and holds the timestamp

## The one test that matters

After deploying, fetch the published page with JavaScript disabled and confirm every
workshop title appears in the raw HTML. Everything else is secondary.

```bash
curl -s https://workshops.senseandrespond.co/ | grep -c "tito-event\|<h2"
```

Better: compare the set of titles in the raw HTML against the set in `workshops.json`. They
should match exactly.

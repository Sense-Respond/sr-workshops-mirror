# Code notes

## What's here

| File | Status |
|---|---|
| `build.py` | Data layer kept as-is. Render layer and `main()` rewritten 2026-09-30 |
| `verify.py` | Checks the raw HTML the way a non-JS crawler sees it. `python3 verify.py [dir or URL]` |
| `tests/` | stdlib `unittest`. `python3 -m unittest discover tests` |
| `.github/workflows/build.yml` | Daily build at 11:00 UTC: test, build, verify, commit `public/` if changed |
| `netlify.toml` | Publish `public/`, no build command, skip deploys that don't touch `public/` |
| `docs/sample-workshops.json` | Real snapshot of 15 workshops, 18 September 2026. Use it to develop and test the renderer without hitting the API |
| `docs/DEPRECATED-squarespace-code-block.html` | Do not ship. Kept as a record of the wrong approach. See `docs/FINDINGS.md`, dead end 1 |

`build.py` has no dependencies beyond the Python standard library. Run it with
`python3 build.py`.

## build.py: keep these

This half is tested and correct. Don't rewrite it.

| Function | What it does |
|---|---|
| `fetch_from_api()` | Reads the Ti.to **v3** API (v2 retired, moved 2026-09-30), filters out private, test-mode, not-live and finished events, one releases call per event. Also returns `start_at`, `end_at`, `timezone` and `sold_out` |
| `cheapest_price()` | Lowest price across releases a member of the public can actually buy. Ignores archived, secret and not-a-ticket releases. Field names updated for v3 (`not_a_ticket`) |
| `fetch_from_timeline()` | Scrapes the public timeline when no token is set. Correctly excludes past and unscheduled events. **Since late September 2026 the timeline is client-rendered, so this returns nothing.** See `FINDINGS.md` section 5 |
| `format_range()` | Matches Ti.to's own date phrasing, e.g. "September 17th–October 8th, 2026" (en dash, kept by decision 2026-09-30) |
| `format_price()`, `ordinal()`, `parse_date()`, `clean()` | Small helpers |
| `dedupe()` | Collapses events identical on title + start + end + location + **region** (region added 2026-09-30: the "duplicates" were regional cohorts) |
| The guards in `main()` | Two behaviors worth preserving, described below |

### Two guards to preserve

**Won't publish an empty page over a good one.** If a build returns zero events but the last
good build had some, it exits non-zero without writing. A Ti.to outage or an expired token
then leaves yesterday's list up and fails the Action loudly, instead of wiping the page.

**Won't write when nothing changed.** If the event data matches the previous build, it writes
nothing. This keeps the repo free of no-op commits and makes the "last updated" date on the
page mean the list changed then, rather than a job ran then.

## build.py: rewrite these (done 2026-09-30)

The render layer was written for the abandoned Squarespace approach. It produces a card grid
that does not meet the brand spec or the crawlability criteria.

| Item | What's wrong |
|---|---|
| `card_html()` | No `<time datetime>`, no anchor id, no gradient date band. Uses `<h3>` where the page structure now wants `<h2>` |
| `STYLES` | Sampled from the live site, not built from the brand spec. Wrong type scale, no gradient |
| `PAGE` | No logo, no `robots`/`sitemap`/`llms` siblings, thin JSON-LD |
| `render_page()` | JSON-LD omits price and only handles `ItemList`. Needs full `Event` objects |

## build.py: add these (done 2026-09-30, logo still a placeholder)

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
| `SITE_URL` | `https://workshops.senseandrespond.co` | Canonical URL, used in sitemap, robots and JSON-LD |

Options: `--from-json PATH` builds from a saved `workshops.json` (e.g.
`docs/sample-workshops.json`, with `OUT_DIR` pointed somewhere other than `public/`).
`--force` writes even when nothing changed.

## Tests

All of these are now in `tests/` and pass (54 tests, 2026-09-30; the API tests use v3-shaped fixtures). One caveat: the timeline
test originally ran against real markup (11 events). That markup no longer exists, so it now
runs against a synthetic fixture built from the documented class names, plus the real
30 September empty page.

The original list:

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

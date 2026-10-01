# Verified findings

Everything here was checked directly on 18 September 2026. Don't re-research it. Do re-check
anything marked **verify again** if more than a couple of months have passed.

---

## 1. AI crawlers do not run JavaScript

This is the finding the whole project rests on.

Per Vercel's "Rise of the AI Crawler" study:

- **GPTBot** fetched JavaScript files in about 11.5% of requests and never executed them
- **ClaudeBot** downloaded JavaScript in about 23.84% of requests and never executes it
- **PerplexityBot** parses the HTML it first receives and moves on
- **Googlebot** is the exception. It renders JavaScript, on a delay

Consequence: any solution that injects the workshop list client-side is invisible to the
exact audience we're targeting. The content must be in the server's first response.

**verify again** if revisiting in 2027. Crawler behavior changes.

## 2. Squarespace cannot host this

senseandrespond.co is **Squarespace 7.1** with Fluid Engine.
templateId `5c5a519771c10ba3470d8101`, templateVersion `7.1`, confirmed from the live page.

Three doors, all closed:

| Approach | Status |
|---|---|
| Content-write API | Does not exist. Squarespace's APIs cover Commerce, Inventory, Profiles, Forms, Webhooks. Nothing edits a page |
| Developer Mode (git-based templates) | 7.0 only. 7.1 never got it |
| Reverse proxy or path routing to another host | Not supported |

So nothing can put auto-updating, server-rendered HTML at `senseandrespond.co/workshops`.
This is a platform limit, not a preference. **Do not spend time looking for a workaround.**

Also noted: the Squarespace sitemap.xml has 177 entries but is heavy on blog and book-review
pages. A prior site audit flagged that main marketing pages are missing from it. Relevant to
the traffic OKR, not to this build.

## 3. The existing Netlify setup

`webinar.senseandrespond.co` is already on Netlify. Confirmed via the `Server: Netlify`
response header.

- Static, server-rendered. `<h1>` present in the raw HTML
- Oswald for headings, Roboto for body
- **Zero structured data.** No JSON-LD at all

**Correction, 2026-09-29.** An earlier version of this file said the workshops page would use
"the same pattern" as the webinar site. That is only half true. Same host, different deploy
mechanism: the webinar site is **not connected to GitHub**. It was deployed by drag-and-drop
or CLI. So the Netlify GitHub App has never been installed in the
josh@senseandrespond.co Netlify account, and installing it is a first-time step, not a repeat
of something already working.

Two Netlify accounts exist:

| Account | Holds | GitHub connection |
|---|---|---|
| josh@senseandrespond.co | webinar.senseandrespond.co | None yet |
| josh@seiden.co | Josh's personal projects | Connected to the josh@seiden.co GitHub account |

The workshops site goes in **josh@senseandrespond.co**, because that is where the company
domain already lives.

Netlify's GitHub App does not require the Netlify account owner to be the GitHub repo owner,
so a company Netlify account can deploy a repo owned by any account or org the app is
installed on. But Netlify's docs warn that the link is authorized by a person: if the user who
authorized the connection loses access to the repo, the site can stop building. That argues
for a company-owned GitHub org rather than a personal repo. See PROJECT_BRIEF.md for the
decision actually taken.

## 4. Ti.to API

**Correction, 2026-09-30. v2 is retired; use v3.** The first live build got
`HTTP 404` from the v2 URL below. Without credentials, every v2 path (including `/v2/hello`)
returns a plain 404 page, while `https://api.tito.io/v3/hello` returns
`{"authenticated":false}` and `/v3/sense-respond-learning/events` returns
`401 "The API token is missing"`, so the account slug is right. `build.py` now uses v3.
From the v3 docs (https://ti.to/docs/api/admin/3.0), checked 2026-09-30:

- **Events:** `GET https://api.tito.io/v3/{account}/events` lists upcoming events. Headers:
  `Authorization: Token token=...` and `Accept: application/json`. Plain JSON, not JSON:API:
  `{"events": [...], "meta": {"next_page": ...}}`. Paged with `page[number]` and
  `page[size]` (max 1000)
- **Event fields:** `title`, `slug`, `start_date`, `end_date`, `start_at`, `end_at`,
  `timezone`, `location`, `currency`, `live`, `private`, `test_mode`, `banner_url`
- **Releases:** `GET https://api.tito.io/v3/{account}/{event_slug}/releases`. Fields
  include `price`, `archived`, `secret`, `not_a_ticket`, `sold_out`, `state_name`. The docs
  don't say whether the events list embeds priced releases, so `build.py` makes one call
  per event
- **Tokens:** generated at https://id.tito.io, "Generate New Token". Only **secret** tokens
  work with the Admin API. **Not yet verified** that the token in the repo secret is a v3
  secret token. The first v3 run will tell: a 401 means it needs replacing

The v2 notes below are kept as a record.

**Endpoint:** `GET https://api.tito.io/v2/{account}/events?include=releases`
**Auth header:** `Authorization: Token token=YOUR-API-KEY`
**Account slug:** `sense-respond-learning`

Event attributes returned:

```
banner-url, currency, description, end-date, live, location,
logo-url, private, slug, start-date, test-mode, title
```

Release (ticket type) attributes that matter for pricing:

```
price, archived, secret, not-a-ticket, state, quantity
```

Filter out any event where `private`, `test-mode`, or `not live`. Filter out events whose
end date has passed. When computing a "from" price, ignore releases that are `archived`,
`secret` or `not-a-ticket`.

No pagination is documented for v2. `build.py` follows `links.next` defensively anyway.

The token is generated at the **account** level in the Ti.to dashboard, not inside an
individual event. Look under account settings for API tokens. **Not verified.** I could not
confirm the exact menu path without logging into the account.

## 5. The public timeline is server-rendered (useful fallback)

**Correction, 2026-09-30. No longer true.** Fetched on 30 September 2026 with a browser, curl
and GPTBot user agent: `https://ti.to/sense-respond-learning/` now returns an empty
`<tito-events account="sense-respond-learning"></tito-events>` and no event markup. The list is
rendered client-side. So the scrape fallback returns zero events, and the ti.to page is now
invisible to AI crawlers, which is the problem this project fixes. The response is saved as
`tests/fixtures/timeline-2026-09-30-client-rendered.html`. `build.py` now uses the scrape only
when no token is set, and the section below is kept as a record.

`https://ti.to/sense-respond-learning/` returns the full event list in its HTML. The
`<tito-events>` custom element is hydrated by `js.tito.io/v2/with/inline`, but the markup is
already there in the server response.

Stable class names:

```
.tito-events--upcoming    wrapper for upcoming events
.tito-events--unscheduled  (comes after upcoming)
.tito-events--past         (comes after unscheduled)
.tito-event                one event
.tito-event--event-link    the <a>
.tito-event--title         <h2>
.tito-event--time          date label
.tito-event--location      location, when present
.tito-event--banner        <img>
```

This makes scraping a genuine fallback, not a fig leaf. `build.py` already implements it and
it is tested. It loses prices, locations and machine-readable dates, so the API is still
preferred.

## 6. Duplicate events in Ti.to

**Correction, 2026-09-30. They are not duplicates.** Comparing each `-1`/`-2` pair's public
Ti.to page: `-1` is the **Americas & Europe** cohort (sessions 11:00 ET / 12:00 BRT /
17:00 CET) and `-2` is the **Asia-Pacific, Middle East & Africa** cohort (8:30 GST /
10:00 IST / 14:30 AEST), with different banners. Everything else is identical. The region
is the first line of the Ti.to description, after a globe icon
(`<i class="fa-light fa-globe"></i>`). The API gives all twelve the time zone "UTC", which
looks like Ti.to's default rather than a real setting. `build.py` now reads the region, shows
it, and includes it in the dedupe key. The section below is kept as a record.

As of 18 September 2026 the timeline lists **21 upcoming events, 6 of which are exact
duplicates**. Six pairs share a title and dates, with slugs differing only by a trailing
`-1` and `-2`, all under the `updated-product-training-for-2027` family:

| Workshop | Dates | Slugs |
|---|---|---|
| Lean Product Strategy | Sep 29 to Oct 1 | `...-lps-1` / `...-lps-2` |
| Objectives and Key Results | Oct 6 to 8 | `...-okrs-1` / `...-okrs-2` |
| Lean Product Management | Oct 13 to 27 | `...-lpm-1` / `...-lpm-2` |
| Lean Product Discovery | Nov 3 to 12 | `...-lpd-1` / `...-lpd-2` |
| Storytelling Superpowers | Nov 17 to 24 | `...-sty-1` / `...-sty-2` |
| Building AI Products | Dec 1 to 3 | `...-bai-1` / `...-bai-2` |

Visitors to the Ti.to page see each of these listed twice today.

The build dedupes on title + start + end + location, so if these are genuinely separate
cohorts or time zones and get distinct titles or locations in Ti.to, they stop collapsing
automatically. If they're mistakes, deleting them in Ti.to is the real fix.

**Re-check the count before launch.** These numbers are a snapshot.

## 7. The nav item already exists

senseandrespond.co's main nav already has **"Public Workshops"** pointing at
`https://ti.to/sense-respond-learning/`. Making this page reachable in one click is a link
change, not a new nav item.

Current nav: Home, For Product Teams, For Individuals, Certifications, Public Workshops,
Who We Are, Who We Serve, Resource Hub, Books, Blog, Contact.

## 8. Google Analytics on senseandrespond.co

Checked 1 October 2026 in headless Chrome and from the tag Google serves
(`googletagmanager.com/gtag/js?id=G-WPJMQ52FEF`).

- The main site is served at **www.senseandrespond.co** and sends every hit to two GA4
  properties: `G-WPJMQ52FEF` and `G-6MMTGMY8G1`. It also loads a Google Ads tag
  (`AW-18321099953`) and sets a Universal Analytics cookie, `_gat_gtag_UA_145067854_1`
- Its `_ga` cookies are on `.senseandrespond.co`, so the workshops subdomain, with default
  gtag settings, shares the same client ID
- It uses Consent Mode (Squarespace's banner); its hits carry `gcs` values
- The `G-WPJMQ52FEF` web stream has enhanced measurement on: page views, scroll, outbound
  clicks, downloads, forms, video, history events. No own domains are listed, so clicks to
  ti.to count as outbound
- Chrome DevTools shows GA's `/g/collect` requests as `ERR_ABORTED` on both sites. That's
  how it shows these fire-and-forget beacons, not a failure

**verify again** if GA settings change.

## 9. Ti.to Source Tracking

Checked 1 October 2026 (https://help.tito.io/en/articles/3846161-source-tracking,
https://ti.to/docs/api/admin/3.0):

- The parameter is `?source=`. Sources are saved per event, in the event dashboard under
  Source Tracking, which generates the link and the report
- The Admin API has **no endpoint to create or list sources**. Registrations do expose a
  `source` field ("The Source Tracking code that the person registered under")
- The docs don't say whether an order made through an **unsaved** source is recorded. Not
  tested. A one-time test would settle it: a free test event, a registration through
  `?source=test` without saving the source, then check the registration
- Ti.to's own GA integration sends only `begin_checkout` and `purchase`, and only through
  its checkout widget on your own site (https://help.tito.io/en/articles/2006249-google-analytics)

Consequence: per-event setup is not practical (the admin creates events), so the page
measures interest with GA outbound clicks instead. See `PROJECT_BRIEF.md`.

---

## Dead ends: do not revisit

**1. Squarespace code block that fetches a JSON feed.**
This was built first and it was wrong. It renders the workshop list client-side, which means
GPTBot, ClaudeBot and PerplexityBot see an empty div. It moves the invisibility problem from
ti.to onto our own domain. The file is kept at
`docs/DEPRECATED-squarespace-code-block.html` as a record of what not to ship.

**2. The `<tito-events>` embed widget.**
Ti.to offers `<tito-events account="sense-respond-learning">`, which renders the whole event
list live with one script tag. Zero maintenance and always current. Rejected for the same
reason: client-side rendering, invisible to LLM crawlers. It would be a fine choice if goal 2
did not exist.

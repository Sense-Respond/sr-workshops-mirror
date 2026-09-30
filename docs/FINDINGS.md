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

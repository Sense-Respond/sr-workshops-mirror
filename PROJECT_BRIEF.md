# Public Workshops Mirror — Project Brief

**Last updated:** 2026-10-01

## Current State

**2026-10-01. Live at https://workshops.senseandrespond.co. Definition of done item 1 met.**

The Action builds `public/` from the live API and commits it; Netlify deploys on push.
Latest build (`664e2fb`): 14 workshops, 0 collapsed. Netlify site `sr-workshops.netlify.app`,
HTTPS working, HTTP redirects to HTTPS. Only the Squarespace nav link remains.

Live checks, 2026-10-01 12:38 UTC:
- `python3 verify.py https://workshops.senseandrespond.co`: OK. 14 titles in the raw HTML
  match `workshops.json`, 14 JSON-LD `Event`s, 27 `<time>` elements
- Fetched with the GPTBot user agent: full list in the raw HTML
- `robots.txt`, `sitemap.xml`, `llms.txt`, `workshops.json` all 200, text files served as
  UTF-8
- Live `index.html` is byte-identical to `public/index.html` at `664e2fb`

Done:
- `build.py` writes `index.html`, `workshops.json`, `robots.txt`, `sitemap.xml` and
  `llms.txt`. Every workshop is in the raw HTML with an `<h2>`, an anchor id from its slug,
  `<time datetime>` on every date, and one full JSON-LD `Event`. The only `<script>` on the
  page is the JSON-LD
- Data from the Ti.to Admin API v3 (v2 is retired). The date band shows date, then session
  times or time zone, then region, then place. Sold-out status and a "from" price that
  ignores sold-out tickets
- `main()` guards per the decisions below. `--from-json` and `--force`
- `verify.py` checks what a non-JS crawler sees. Takes a directory or the live URL
- `tests/`: 64 stdlib `unittest` tests. Run with `python3 -m unittest discover tests`
- `.github/workflows/build.yml`: daily at 11:00 UTC, plus a manual run with an optional
  "force" box. Tests, token check, build, verify, commit `public/` only if it changed
- `netlify.toml`: publishes `public/`, no build command, skips deploys that don't touch
  `public/`, UTF-8 charset on `llms.txt` and `robots.txt`
- Brand PDF kept local and gitignored

Live runs, 2026-09-30:
- 36785231040: HTTP 404, Ti.to v2 retired. Guards held, nothing written
- 36786181400: v3 and the repo token work. Showed midnight as session times, collapsed the
  regional cohorts as duplicates, and listed in-progress workshops
- 36787011791: all three fixed. 14 workshops, 10 regional cohorts detected

Live runs, 2026-10-01:
- 36863257348 (manual, no force): tests, token check, build, verify all passed. API returned
  14 events, unchanged since the 2026-09-30 22:41 UTC build, so the no-change guard wrote
  nothing and there was no commit or deploy
- 36863477460 (manual, force, Josh): committed `c09a93c` (timestamps only). Josh saw
  missing images on the live page. Cause: Ti.to v3's `banner_url` is the CloudFront URL with
  the full URL appended again (`.../banner/1164882/https://.../banner/1164882/x.png`), which
  CloudFront answers 403. Broken since the first v3 build on 2026-09-30, not caused by the
  force run. Fixed in `build.py` (`banner_url()`), see Decisions
- 36864063425 (manual, no force): after the fix (`a2b84b3`). Repaired banner URLs counted as
  a data change, so it wrote and committed `664e2fb`. Netlify deployed it within about 10
  seconds of the push, so deploy-on-push from an Action commit now works. Live: all 14
  images return 200, `verify.py` OK

Open, in order:
1. ~~Netlify~~ Done 2026-10-01 (Josh): Netlify GitHub App installed on the `Sense-Respond`
   org, scoped to this repo; site created from the repo in the josh@senseandrespond.co
   account, build command empty
2. ~~DNS~~ Done 2026-10-01: `workshops.senseandrespond.co` CNAME to
   `sr-workshops.netlify.app`, created at iwantmyname (where the senseandrespond.co
   nameservers are). Netlify verified it and issued the HTTPS certificate
3. ~~Verify live~~ Done 2026-10-01: `verify.py` OK against the live URL (see above)
4. Repoint the "Public Workshops" nav item on Squarespace (Natalia)

Also open:
- Logo is a text placeholder until Natalia supplies the SVG
- No session times are entered in Ti.to for any event. When they are, the band shows them
  (e.g. "9:00–11:00 AM CDT") instead of the time zone
- The ten regional cohorts carry Ti.to's default time zone, UTC, so they show a region but
  no time zone. Their real session times (e.g. 11:00 ET / 12:00 BRT / 17:00 CET) are only
  in the Ti.to description text
- First scheduled run (2026-10-01 11:00 UTC) had not started by 12:40 UTC. GitHub delays
  scheduled runs, sometimes by hours. Check it ran later today; if not, check the Actions tab
- GitHub disables scheduled workflows after 60 days with no repo activity. The Action's own
  commits count, and the list changes at least as often as a workshop starts, so this should
  not bite. If the Action ever stops running, re-enable it on the Actions tab

Found on 2026-09-30:
- The ti.to public timeline no longer server-renders its events (`docs/FINDINGS.md`
  section 5). The scrape fallback returns nothing, so without a token a build gets zero
  events
- Ti.to API v2 is retired (`docs/FINDINGS.md` section 4)
- The "duplicate" events are regional cohorts (`docs/FINDINGS.md` section 6)
- The p.21 gradient's middle stop is `#008F23`, not `#00A651` as `BRAND-SPEC.md` said
  (corrected there)

---

## Goals

1. Present S&R Learning's public workshops on our own domain, one click from the home page.
2. Make the workshop list readable by standard search engines **and by LLM crawlers**, so
   people asking ChatGPT, Claude, Gemini or Perplexity about product management training find
   our classes.

Goal 2 drives every technical decision. It is the reason a first version of this project was
scrapped. See `docs/FINDINGS.md`.

## Technical decisions

- **Stack:** Python standard library only, no dependencies. `build.py` reads the Ti.to API and
  writes static files
- **Publish directory:** `public/`
- **Hosting:** Netlify, in the **josh@senseandrespond.co** account, at
  `workshops.senseandrespond.co`
- **Build trigger:** GitHub Action, daily at 11:00 UTC, commits the output. Netlify deploys on
  push. Netlify's own build command stays empty
- **The page must be server-rendered HTML.** No client-side rendering of workshop data, at all,
  for any reason

## Decisions Made

- **2026-10-01. Repair Ti.to's doubled banner URLs.** `banner_url()` keeps the last
  `https://` URL in the string. All 14 repaired URLs return 200. A normal URL passes
  through unchanged, so if Ti.to fixes this the code needs no change. A small addition to
  `fetch_from_api()`, which is otherwise kept as-is.
- **2026-09-30. The "duplicates" are regional cohorts; show both.** Each
  `updated-product-training-for-2027-*-1`/`-2` pair is one course run for Americas & Europe
  and again for Asia-Pacific, Middle East & Africa, on the same dates (`docs/FINDINGS.md`
  section 6). The region comes from the globe-icon line in the Ti.to description. It is shown
  in the date band, JSON-LD and `llms.txt`, and is part of the dedupe key. Narrows the
  2026-09-18 "collapse duplicate events" decision: only events identical in region too are
  collapsed.
- **2026-09-30. Don't list in-progress workshops.** An event is listed only if its start date
  is after today (UTC, at build time). A workshop starting today is already off the list.
- **2026-09-30. The "from" price is the cheapest ticket still on sale.** Sold-out releases no
  longer count, alongside archived, secret and not-a-ticket. If every public release is sold
  out there is no price and the card says "Sold out".
- **2026-09-30. Show the time zone even without session times.** E.g. "Time zone: CDT
  (Central Time, US & Canada)", from Ti.to's `timezone`, abbreviated for the event's own
  date so daylight saving is right. Zones with no abbreviation show a UTC offset. "UTC" is
  not shown: it is Ti.to's default, and every event marked UTC today is a regional cohort
  whose sessions span several zones. The region line covers those.
- **2026-09-30. Midnight means no time.** Ti.to returns midnight for `start_at`/`end_at`
  when no session time is entered, so midnight-to-midnight is treated as no time.
- **2026-09-30. Rupee symbol.** INR prices show as "₹1,400".
- **2026-09-30. Move `fetch_from_api()` to Ti.to Admin API v3.** v2 is retired (404). Same
  filter and pricing rules as before; only the endpoint, response shape and field names
  changed. Prices come from one releases call per event. Overrides the earlier "keep the data
  layer as-is" instruction for these two functions, by Josh's approval.
- **2026-09-30. Show sold-out status.** A workshop is sold out when every release the public
  can buy (not archived, secret or not-a-ticket) is sold out. Sold-out workshops show "Sold
  out" instead of a price and a "See details" button instead of "Register", and their
  JSON-LD offer says `SoldOut`. Others say `InStock`. With no public releases, availability
  is left out. The "from" price still includes sold-out releases, as before.
- **2026-09-30. Show session times.** From Ti.to's `start_at`, `end_at` and `timezone`,
  shown in the date band as e.g. "9:00–11:00 AM CDT", between the date and the place (guide
  p.21: "date, time and place"). JSON-LD `startDate`/`endDate` become full datetimes when
  times are known. Rails zone names are mapped to IANA zones for the abbreviation; unknown
  zones or zones without an abbreviation show a UTC offset. No times from Ti.to, no time line.
- **2026-09-30. Brand guide PDF stays out of git.** It is 20MB and a client-version document.
  It lives in `docs/` locally and is gitignored. Anyone working without it uses
  `docs/BRAND-SPEC.md`, which records what was checked against it.
- **2026-09-30. Date band: option c-alt.** The guide's p.21 gradient trimmed to the 8%-68%
  span where white text clears 3:1: `#04A6A4` to `#008F23` (at 70%) to `#45A928`, white text
  22px bold. Chosen over (a) the guide as written, which fails at 1.6:1; (b) guide colours with
  text squeezed into the middle; and (c) darkened ends, which turned the lime end olive.
- **2026-09-30. Page intro copy (Josh).** Headline "Build these skills, your way", then
  "Our training is available in person or online, live and interactive, delivered on-site or
  remotely, wherever you’re located. Created by Jeff Gothelf and Josh Seiden, and led by our
  Certified Training Partners worldwide, you get the same training, in the format that fits."
  The H1 stays "Public Workshops"; the headline sits under it as an H2 styled per guide p.18.
- **2026-09-30. Meta description (Josh).** "Upcoming workshops from Sense & Respond Learning:
  live training in Product Management, Lean UX, Product Discovery, OKRs, Outcomes, and
  Storytelling." Also used for `og:description` and the `llms.txt` summary.
- **2026-09-30. The brand guide PDF governs design.** `docs/S&R Brand Guidelines 2025 for
  client 20250611.pdf`. `docs/BRAND-SPEC.md` is a summary, and where they differ the PDF wins.
  Diverge only where the guide is silent or following it would cause a real problem, such as
  readability. Record each divergence, with the reason, under "Brand divergences" below so
  Josh can take it to Natalia. Supersedes the 2026-09-18 "match the live site" decision.
- **2026-09-30. With a token, the API is the only source.** If `TITO_API_TOKEN` is set and
  the API call fails for any reason (401, timeout, bad JSON), the build exits non-zero and
  writes nothing. The public-timeline scrape runs only when no token is set. Reason: the scrape
  has no dates or prices, so falling back published a worse page and let the Action pass.
- **2026-09-30. Design changes count as changes.** The no-change guard compares
  `TEMPLATE_VERSION` as well as the event data, so a new design still ships when the
  workshops haven't changed. Bump `TEMPLATE_VERSION` in `build.py` with every output change.
  `--force` writes regardless. The empty-page guard still applies under `--force`.
- **2026-09-30. Slug breaks sort ties.** Events sort on start date, title, then slug, so
  the same duplicate survives dedupe on every run and anchor ids stay stable.
- **2026-09-30. Keep the en dash in date ranges.** "September 17th–October 8th, 2026", as
  the tested `format_range()` already produces. An en dash, not an em-dash, so the voice rule
  is untouched.
- **2026-09-30. Online detection.** A workshop is online when its Ti.to location is empty,
  or contains "online" or "zoom" in any case. Online events get
  `OnlineEventAttendanceMode` and a `VirtualLocation`. Anything else gets
  `OfflineEventAttendanceMode` and a `Place` named after the location.
- **2026-09-29. Dev workflow: laptop (supervised).** Per `dev-workflow.md`. Claude Code in the
  terminal on Josh's laptop, Josh present and steering. Chosen over the AI Workshop because the
  build is short rather than an hours-long unattended job, it has a visual judgment component
  (the brand match and the date-band gradient), and the DNS work sits on the laptop anyway.
- **2026-09-29. Netlify account: josh@senseandrespond.co.** The company account, where the
  senseandrespond.co domain already lives. Not the personal josh@seiden.co account.
- **2026-09-29. GitHub org: `Sense-Respond`.** Created by Josh. This repo is
  `Sense-Respond/sr-workshops-mirror`. Chosen over a personal repo because the
  `TITO_API_TOKEN` secret lives here, and because Netlify's repo link is authorized by a person
  rather than an account, so a personal repo would make company infrastructure depend on one
  individual's GitHub login. Josh administers the org from his existing josh@seiden.co login.
  When connecting Netlify, install the Netlify GitHub App **on the org**, scoped to this repo
  only.
- **2026-09-18. Host on a subdomain, not the main site.** Squarespace 7.1 cannot serve an
  auto-updating page. See `docs/FINDINGS.md` section 2
- ~~**2026-09-18. Where the brand guide and the live site disagree, match the live site.**
  Type follows the guide.~~ Superseded 2026-09-30: the guide PDF governs. See above
- **2026-09-18. Collapse duplicate events by default**, keyed on title + start + end + location

## Brand divergences (for Natalia)

Where the page departs from the guide, or fills a gap in it, and why. Updated 2026-09-30.

| # | What | Guide | Page | Why |
|---|---|---|---|---|
| 1 | Date band gradient | p.21 gradient `#05AABC` to `#008F23` to `#BFD630`, white text | Same gradient trimmed to its 8%-68% span: `#04A6A4` to `#008F23` to `#45A928`. No Spring Green end | White text clears 3:1 only across that span of the full gradient and never reaches 4.5:1. The lime end is 1.6:1 |
| 2 | Date band text size | Silent | 22px Roboto Bold | 22px bold counts as "large text" under WCAG, which sets the contrast bar at 3:1 rather than 4.5:1 |
| 3 | H1 at phone width | 72px | Scales from 44px on phones up to 72px | Guide gives one size. 72px capitals overflow a phone screen |
| 4 | H2 at phone width | 36px | Scales from 26px on phones up to 36px | Same reason. Ti.to titles are long |
| 5 | Button colour | p.19 mockup uses `#343131`, not a palette value | Iron `#39393D` | Nearest palette colour. Looks the same |
| 6 | Link colour and button hover | Silent | Deep Teal `#345C60` | Palette secondary colour, used sparingly as the guide says. 7.4:1 on white |
| 7 | Keyboard focus ring | Silent | 3px Iron outline | Needed for keyboard users |
| 8 | Colour names | p.13 labels `#00A651` "Violet" and `#0072BC` "New Leaf" | Unaffected | The labels look mislabelled |
| 9 | Live site | Guide | Page follows the guide | The live site uses Deep Teal pill buttons and ~14px body text. The drift is on the live site's side now |

## Definition of done

In priority order. The first one is the project.

1. Fetch the published page with JavaScript disabled. Every workshop title appears in the raw
   HTML
2. Valid JSON-LD `Event` per workshop: name, start and end dates, price, registration URL,
   online attendance mode, organizer
3. `robots.txt` allows GPTBot, ClaudeBot, PerplexityBot, Google-Extended, CCBot
4. `sitemap.xml` and `llms.txt` at the site root
5. Anchor id per workshop
6. `<time datetime="YYYY-MM-DD">` on every date
7. Matches `docs/BRAND-SPEC.md`, works at phone width
8. A Ti.to outage or expired token leaves the previous list up and fails the Action loudly
9. The build only commits when workshop data actually changed

---

Companion planning doc: `claude-context/projects/public-workshops-page.md`

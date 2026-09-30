# Public Workshops Mirror — Project Brief

**Last updated:** 2026-09-30

## Current State

**2026-09-30. Renderer, Action and Netlify config written. Not yet committed or deployed.**

Done:
- `build.py` render layer replaced. It writes `index.html`, `workshops.json`, `robots.txt`,
  `sitemap.xml` and `llms.txt`. Every workshop is in the raw HTML with an `<h2>`, an anchor
  id from its slug, `<time datetime>` on every date, and one full JSON-LD `Event`. The only
  `<script>` on the page is the JSON-LD. The Ti.to data layer is byte-for-byte unchanged
- `main()` guards changed per the 2026-09-30 decisions below. New `--from-json` and `--force`
- `verify.py` checks what a non-JS crawler sees: titles in the raw HTML against
  `workshops.json`, JSON-LD Events, `<time>` values, and the sibling files. Takes a
  directory or the live URL
- `tests/`: 41 stdlib `unittest` tests. Run with `python3 -m unittest discover tests`
- `.github/workflows/build.yml`: daily at 11:00 UTC, plus a manual run with an optional
  "force" box. Runs the tests, fails early if `TITO_API_TOKEN` is missing, builds, runs
  `verify.py`, and commits `public/` only if it changed. The `TITO_API_TOKEN` secret is set
  on the repo (confirmed 2026-09-30)
- `netlify.toml`: publishes `public/`, no build command. Skips deploys for pushes that don't
  touch `public/` or `netlify.toml`. Sets a UTF-8 charset on `llms.txt` and `robots.txt`
- Brand PDF kept local and gitignored

Open, in order:
1. Commit and push this work (awaiting Josh's go-ahead)
2. Run the Action once by hand (Actions tab, "Build workshops page", Run workflow). This is
   the first real API call. It creates `public/`, which Netlify needs before its first deploy
3. Netlify, in the josh@senseandrespond.co account: install the Netlify GitHub App on the
   `Sense-Respond` org, scoped to this repo only; create the site from the repo. Leave the
   build command empty; `netlify.toml` sets the publish directory
4. DNS: add `workshops.senseandrespond.co` in Netlify and create the CNAME wherever the
   senseandrespond.co DNS is managed. Wait for HTTPS
5. `python3 verify.py https://workshops.senseandrespond.co`. Definition of done item 1
6. Re-check the duplicate count against the live data (`docs/FINDINGS.md` section 6)
7. Repoint the "Public Workshops" nav item on Squarespace (Natalia)

Also open:
- Logo is a text placeholder until Natalia supplies the SVG
- `public/` not generated yet. The sample data is a stale snapshot, so the first real build
  should come from the API (step 2 above)
- GitHub disables scheduled workflows after 60 days with no repo activity. The Action's own
  commits count, and the list changes at least as often as a workshop ends, so this should
  not bite. If the Action ever stops running, re-enable it on the Actions tab

Found on 2026-09-30:
- The ti.to public timeline no longer server-renders its events (`docs/FINDINGS.md`
  section 5). The scrape fallback returns nothing, so without a token a build gets zero
  events
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

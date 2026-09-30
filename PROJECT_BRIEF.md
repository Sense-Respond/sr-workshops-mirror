# Public Workshops Mirror — Project Brief

**Last updated:** 2026-09-29

## Current State

[not yet built]

Planning is complete. Claude Code fills this section in as building starts.

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
- **2026-09-18. Where the brand guide and the live site disagree, match the live site.**
  Type follows the guide. See `docs/BRAND-SPEC.md`
- **2026-09-18. Collapse duplicate events by default**, keyed on title + start + end + location

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

# Public Workshops Mirror — Project Brief

**Last updated:** 2026-10-07

## Current State

**2026-10-06. Live at https://workshops.senseandrespond.co with the design from the
2026-10-01 review, GA4 behind a consent banner, and click tracking to Ti.to. Jeff worked
through the analytics handoff on 2026-10-06 (results below). "Accept all" now re-sends the
page view so first visits keep their traffic source (template version 7), confirmed by
Josh in GA Realtime on 2026-10-07. Still waiting on the nav and site links.**

The Action builds `public/` from the live API and commits it; Netlify deploys on push.

Analytics, 2026-10-06 (Jeff's report, "2026 Oct 6 status update and next Steps.md" in the
Cowork folder; status per item in `docs/ANALYTICS-HANDOFF.md`):
- Done: Realtime shows page views, `click` and `tito_click` for this hostname; the "AI
  assistants" channel sits above Referral; outbound clicks on, no change; no self-referral
  from senseandrespond.co; GA consent settings say "Your setup is good"
- `tito_click` existed as a key event with the wrong trigger (`event_name = page_view` and
  `page_location` contains ti.to, which can never fire, since GA doesn't run on ti.to). Jeff
  changed it to `event_name = click` and `link_domain = ti.to`, copying parameters so
  `link_url` carries over. Confirmed in Realtime
- Workshops report built in Explore: "Workshops – Ti.to clicks" (private to Jeff)
- Found: first visits lost their traffic source. Fixed in `build.py`, see Decisions
- `G-6MMTGMY8G1` isn't on the main site's page itself: it's loaded through the old Universal
  Analytics tag (`UA-145067854-1`) in Squarespace's Google Analytics field

Live checks, 2026-10-06 18:20 UTC, after the first-visit fix (`6462598`, Action run
37510471939, build commit `bd71859`): live `index.html` byte-identical to `public/index.html`;
the new line is in it; exactly three scripts; `verify.py` OK against the live URL, 12 titles
(two workshops have started since the 2026-10-01 count).
Latest build (`7e6088b`, template version 6, with GA4 and consent): 14 workshops, 0 collapsed. Netlify site
`sr-workshops.netlify.app`, HTTPS working, HTTP redirects to HTTPS. The design pass
(`098875e`) was previewed locally at 1440 and 390px wide and approved by Josh before push.

Live checks, 2026-10-01 18:05 UTC, after the design pass:
- `python3 verify.py https://workshops.senseandrespond.co`: OK. 14 titles in the raw HTML
  match `workshops.json`, 14 JSON-LD `Event`s, 27 `<time>` elements
- Fetched with the GPTBot user agent: all 14 workshop titles in the raw HTML
- Live `index.html` was byte-identical to `public/index.html` at `491763c`, and again at
  `7e6088b` after the analytics deploy. No gradient band; back link "← Back to
  senseandrespond.co" to /individuals
- `assets/sr-logo.svg`, `assets/sr-logomark.svg`, `assets/hero-gradient.jpg` all 200 with the
  right content types. All 14 banners 200 (checked 12:47 UTC)
- Earlier, 12:38 UTC: `robots.txt`, `sitemap.xml`, `llms.txt`, `workshops.json` all 200,
  text files served as UTF-8

Done:
- `build.py` writes `index.html`, `workshops.json`, `robots.txt`, `sitemap.xml` and
  `llms.txt`. Every workshop is in the raw HTML with an `<h2>`, an anchor id from its slug,
  `<time datetime>` on every date, and one full JSON-LD `Event`. The only scripts are the
  JSON-LD, GA4's gtag.js and one small inline consent script (since 2026-10-01). None of
  them renders workshop data
- Google Analytics 4 on the main site's property, behind a cookie-consent banner styled like
  the live site's (Consent Mode v2, denied by default). Links to Ti.to events carry
  `?source=workshops-page`
- Data from the Ti.to Admin API v3 (v2 is retired). Each card shows the Ti.to banner, the
  title, then date, session times or time zone, region and place in Slate. Sold-out status
  and a "from" price that ignores sold-out tickets
- Design from the live site (2026-10-01): top bar with logo and back link, gradient hero,
  Deep Teal pill buttons, one workshop per row. Assets committed in `public/assets/`
- `main()` guards per the decisions below. `--from-json` and `--force`
- `verify.py` checks what a non-JS crawler sees. Takes a directory or the live URL
- `tests/`: 68 stdlib `unittest` tests. Run with `python3 -m unittest discover tests`
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
- Scheduled run, 17:16 UTC: the first unattended run, about six hours after its 11:00 UTC
  slot. Passed; no change in the data, so nothing written. GitHub's schedule delays are
  normal, so a late run isn't a failure
- 36903987959 (manual, no force): after the design pass (`098875e`). TEMPLATE_VERSION 5
  counted as a change, so it wrote and committed `491763c`; Netlify deployed it. Live checks
  above
- 36928707371 (manual, no force): after GA4, consent and source tags (`c1b69b8`).
  TEMPLATE_VERSION 6, so it wrote and committed `7e6088b`; Netlify deployed it. Live page
  byte-identical to the build, `verify.py` OK, exactly three scripts, 42 tagged Ti.to links
  (3 per workshop)
- GA post-check, 21:27 and 21:29 UTC, headless Chrome on the live page: banner shown on a
  first visit; a cookieless `page_view` (`gcs=G100`) before consent; after "Accept all",
  `_ga` and `_ga_WPJMQ52FEF` cookies set on `.senseandrespond.co` (shared with the main
  site) and hits with `gcs=G111`; after a reload, a granted `page_view`. Every hit has
  `tid=G-WPJMQ52FEF` and `dl=https://workshops.senseandrespond.co/`. DevTools reports the
  collect requests as `ERR_ABORTED`, but it reports the main site's working GA hits the
  same way, so that's how it shows GA's fire-and-forget beacons. GA Realtime itself not
  checked (no GA access): handed off, see `docs/ANALYTICS-HANDOFF.md`
- Outbound click check, about 21:40 UTC: a click on the first Register button sent a GA
  `click` event with `outbound=true`, `link_domain=ti.to`, `link_url` (the event URL) and
  `link_classes=btn`, `gcs=G111`

Open, in order:
1. ~~Netlify~~ Done 2026-10-01 (Josh): Netlify GitHub App installed on the `Sense-Respond`
   org, scoped to this repo; site created from the repo in the josh@senseandrespond.co
   account, build command empty
2. ~~DNS~~ Done 2026-10-01: `workshops.senseandrespond.co` CNAME to
   `sr-workshops.netlify.app`, created at iwantmyname (where the senseandrespond.co
   nameservers are). Netlify verified it and issued the HTTPS certificate
3. ~~Verify live~~ Done 2026-10-01: `verify.py` OK against the live URL (see above)
4. ~~Design review~~ Done 2026-10-01: the live design was approved by the team
5. Nav and site links: repoint the "Public Workshops" nav item on Squarespace, and other
   links on senseandrespond.co that go to ti.to's timeline, to
   https://workshops.senseandrespond.co (Natalia)
6. ~~Realtime check of the first-visit fix~~ Done 2026-10-07 (Josh): private window,
   https://workshops.senseandrespond.co/?utm_source=test, "Accept all"; a `page_view` with
   source "test" appeared in Realtime

Also open:
- **Analytics, Josh's items (from Jeff, 2026-10-06).**
  - Add Jeff as an Owner of the senseandrespond.co Search Console property (Settings → Users
    and permissions), so he can link it in GA. Or link it yourself
  - Remove `UA-145067854-1` from Squarespace's Google Analytics field, leaving
    `G-WPJMQ52FEF`. That also stops data to `G-6MMTGMY8G1`; check first that nobody uses it.
    A Squarespace task (Josh/Natalia), not this repo
  - Send Jeff the AI-answer question set (`ai-answer-check.md` in the Cowork folder) for the
    monthly check
- **Analytics, still open with Jeff.** Item 10, banner wording and a privacy link: optional,
  Jeff and legal to decide
- **Out of scope here: ad consent on the main site.** The Google Ads tag
  (`AW-18321099953`) in Squarespace Code Injection sets no consent default, so it can set ad
  cookies and send `user_data` before anyone accepts. S&R is a US company (New York), but EU
  rules and Google's EU consent policy apply to EU visitors. Jeff's report has a suggested
  consent-default snippet. A Squarespace task, not this repo. This page already sets all
  four consent types
- Typo in the Ti.to banner for the OKR cohorts: "OBJECTVES & KEY RESULTS". It's in the image
  file, so it has to be fixed wherever the banners are made
- **"Go back" button (Natalia, next pass).** A button that returns visitors to the page they
  came from. It needs a small script (`history.back()` or `document.referrer`). Since
  2026-10-01 the script test allows exactly the JSON-LD, gtag.js and the consent script, so
  this would be one more change to that rule, or a few lines added to the consent script. Keep a plain link to senseandrespond.co as the
  fallback for visitors who arrive directly. The top bar has that link now: "← Back to
  senseandrespond.co", to https://www.senseandrespond.co/individuals (Josh, 2026-10-01)
- Ti.to banners are full-size PNGs, about 4,170px wide and 12.6MB for today's 14. They
  lazy-load, so only the ones scrolled to are fetched, but each is about 900KB on a phone.
  Smaller exports from wherever the banners are made would fix it
- No session times are entered in Ti.to for any event. When they are, the card shows them
  (e.g. "9:00–11:00 AM CDT") instead of the time zone
- The ten regional cohorts carry Ti.to's default time zone, UTC, so they show a region but
  no time zone. Their real session times (e.g. 11:00 ET / 12:00 BRT / 17:00 CET) are only
  in the Ti.to description text
- GitHub disables scheduled workflows after 60 days with no repo activity. The Action's own
  commits count, and the list changes at least as often as a workshop starts, so this should
  not bite. If the Action ever stops running, re-enable it on the Actions tab

- `docs/TEAM-BRIEF.md` was deleted on 2026-10-01 (Josh): no longer needed, and a copy that
  could drift. This brief is the record. It's in git history if needed

Found on 2026-10-01:
- The live site's body text is 1.1rem, 19.7px at desktop width, not "about 14px" as noted
  in September. Measured values are in `docs/BRAND-SPEC.md`
- Ti.to v3 returns doubled `banner_url`s (fixed in `build.py`)
- Scheduled runs can start hours late (the first ran at 17:16 UTC for an 11:00 slot)
- The Ti.to Admin API can't create Source Tracking sources, and Ti.to's docs don't say
  whether an unsaved `?source=` is recorded (`docs/FINDINGS.md` section 9)
- GA: the stream has outbound clicks on; the main site also reports to a second property
  (`docs/FINDINGS.md` section 8)

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
  for any reason. Scripts allowed since 2026-10-01: the JSON-LD, Google's gtag.js and the
  inline consent script, and no others. See Decisions

## Decisions Made

Analytics, 2026-10-06:

- **2026-10-06. Re-send the page view on "Accept all".** In the consent script's click
  handler, right after `gtag("consent", "update", consent(v))`:
  `if (v === "granted") gtag("event", "page_view");`. Reason (Jeff's finding, 2026-10-06): a
  first visit's page view goes out before consent as a cookieless ping, which GA doesn't
  report, and "Accept all" only updated consent, so nothing new was sent. A first visit's
  `tito_click` arrived with no source. No double count, since the cookieless page view isn't
  reported. Returning visitors are unaffected: their stored choice is the consent default
  before `config`, and the banner script returns early. Decline sends nothing. Still exactly
  three scripts. Template version 7.

Analytics, 2026-10-01 (Josh):

- **2026-10-01. AI assistants channel (Josh).** A custom channel group in GA with an "AI
  assistants" channel (Source matches regex
  `chatgpt|openai|perplexity|claude|anthropic|gemini|copilot`), for Goal 2: seeing visits
  from AI assistants in Traffic acquisition
- **2026-10-01. Measure click-throughs to Ti.to with GA outbound clicks, not Ti.to sources.**
  Saving a Ti.to source on every event is not practical: the admin creates events and can't
  be asked to do it each time, and the Ti.to Admin API has no endpoint to create sources.
  GA4's enhanced measurement already records each click to ti.to as a `click` event with
  `outbound=true`, `link_domain=ti.to` and `link_url` (the event URL, so the slug says which
  workshop). `link_classes` tells the button (`btn`) from the title and banner links. Checked
  2026-10-01: the stream's tag has `enableOutboundClick` on and doesn't list ti.to as an own
  domain, and a test click on the live page sent the event (`gcs=G111`). In GA:
  Explore, event name `click`, dimensions Link URL and Link classes, filter Link domain =
  ti.to. This counts clicks through to Ti.to, not completed purchases; Ti.to's purchase
  events reach GA only through its checkout widget, which would mean loading Ti.to's script
  here. The `?source=workshops-page` tags stay on the links: they cost nothing and would
  start counting if Ti.to turns out to record unsaved sources, which its docs don't say.

- **2026-10-01. Google Analytics 4, on the main site's property.** Measurement ID
  `G-WPJMQ52FEF`, the same property as senseandrespond.co, so both report in one view. The
  standard gtag.js snippet with default cookie settings (`cookie_domain` auto): the `_ga`
  cookies are set on `.senseandrespond.co`, so a visitor's sessions are shared with the main
  site. No cross-domain config needed. Reason: one unified view of the site and this page.
- **2026-10-01. Cookie consent with Google Consent Mode v2.** All four consent types
  (`ad_storage`, `ad_user_data`, `ad_personalization`, `analytics_storage`) default to
  denied, before `gtag('config')`. "Accept all" grants all four; "Decline" keeps them
  denied. The choice is kept in `localStorage` (`sr-consent`) and reapplied on later visits,
  so the banner shows once. While denied, GA gets cookieless pings only. No third-party
  consent platform. The banner is the live site's: a fixed Chalk bar, 14.5px text, a
  "Decline" text button and an "Accept all" Deep Teal pill, both 12px Roboto 600. The live
  site has "Manage cookies" where this has "Decline": there is only one kind of cookie
  here, so a settings panel would offer nothing more. The banner is `hidden` in the HTML and
  shown by the script, so visitors and crawlers without JavaScript never see it. The choice
  isn't shared with the main site: Squarespace keeps its own consent record, so a visitor
  is asked on each.
- **2026-10-01. The no-JavaScript rule now allows analytics and consent.** The page may load
  gtag.js and run the inline consent script. Still no client-side rendering of workshop
  data: every workshop stays in the raw HTML, and `verify.py` still checks every title. The
  test allows exactly three scripts (JSON-LD, the inline consent script, gtag.js), checks the
  inline script is `ANALYTICS_JS` from `build.py`, and checks it holds no workshop data.
  Reason: analytics is needed and doesn't change what crawlers read. Amends the "must be
  server-rendered" technical decision.
- **2026-10-01. Ti.to source tracking: `?source=workshops-page`.** Added to every link on the
  page that goes to an event: banner, title and Register / See details button. The JSON-LD
  and `llms.txt` keep the plain event URL, so crawlers and assistants see the canonical
  address. Ti.to's parameter is `source`
  (https://help.tito.io/en/articles/3846161-source-tracking). Ti.to's docs say a source is
  saved per event in the dashboard, which generates the link. Whether orders through an
  unsaved source are still recorded is not confirmed. Per-event setup was ruled out the
  same day; GA outbound clicks are the measure (see above).

Design review with Natalia, 2026-10-01 (items 1 to 9):

- **2026-10-01. The live site is the design reference.** senseandrespond.co, not the brand
  guide. Where they conflict, follow the live site. The guide still applies where the live
  site is silent. Reverses the 2026-09-30 "guide governs" decision. Natalia will update the
  guide to match the live site. `docs/BRAND-SPEC.md` and the divergences table below follow
  this rule.
- **2026-10-01. References.** Three screenshots in `docs/reference/` (`srl_home_reference.jpg`,
  `srl_training_reference.jpg`, `srl_tito_reference.jpg`) set the overall look. Exact values
  (colours, radius, hover, sizes, spacing) come from the live site's computed CSS, measured
  in headless Chrome on 2026-10-01 at 390, 768, 1024 and 1440px wide. Recorded in
  `docs/BRAND-SPEC.md`, "Live site values". Where no CSS value exists (the live cards are
  Squarespace shape blocks, drawn as SVG), the screenshots decide.
- **2026-10-01. Body text matches the live site.** Roboto 400, 1.1rem: 19.7px at desktop
  width, 17px on phones, line height 1.6. The "about 14px" noted in September was wrong.
- **2026-10-01. Buttons and links match the live site.** Buttons are its primary button: a
  Deep Teal `#345C60` pill (`border-radius: 300px`), white Roboto 600 at 16.3px desktop /
  14.9px phone, capitalized, hover fades to 80% opacity. Text links like "Upskill on
  your own →" are its tertiary button: Deep Teal Roboto 600, no underline, and on
  hover a Deep Teal fill with white text.
- **2026-10-01. Header: top bar, then hero.** No copy of the site nav. A white top bar with
  the full colour logo on the left, 50px tall as on the live site, linked to
  senseandrespond.co, with the guide's clear space (25px, half its height) around it. Then a
  hero with Natalia's gradient image behind the H1 and intro. On the right of the top bar,
  "← Back to senseandrespond.co" (arrow on the left, pointing left, as back links do) goes to
  https://www.senseandrespond.co/individuals, the page that lists public workshops (Josh). Assets in `public/assets/`:
  `sr-logo.svg`, `sr-logomark.svg` (now the favicon) and `hero-gradient.jpg` (1600x1025).
  They are committed, not generated; `build.py` never deletes them.
- **2026-10-01. Cards follow ti.to's layout.** One workshop per row, in a 960px column on a
  Chalk `#F9FAF0` section. The Ti.to banner runs across the full card width, with title and
  details below on white. White card, 16px radius, soft shadow. Drops the trainer-portrait
  idea raised earlier today.
- **2026-10-01. No gradient date band.** Date, time, region and place in Slate `#58585A`
  (the live site's grey, used for its eyebrow labels; 7.1:1 on white) under the black Oswald
  title. The date line is bold. Reason (Natalia): the courses use different gradients.
  Supersedes the 2026-09-30 "option c-alt" decision.
- **2026-10-01. Live-site touches, used sparingly.** One eyebrow label, "FLEXIBLE FORMATS"
  (Roboto Bold, Slate, body size, as on the live Individuals page), above "Build these
  skills, your way". One Key Lime `#E2F46F` highlight in the intro, on "you get the same
  training, in the format that fits".
- **2026-10-01. "Go back" button: not this pass.** Recorded under "Also open". Plain link to
  senseandrespond.co as the fallback.
- **2026-10-01. Type scale from the live site.** Oswald Regular (400) throughout, no
  capitals: H1 78.5px desktop / 48px phone, the intro H2 61.2px / 38px, workshop titles at
  the live H4 size, 26.6px / 23px. Gutters 4vw, 6vw under 768px. Template version 5.

Earlier:

- **2026-10-01. Repair Ti.to's doubled banner URLs.** `banner_url()` keeps the last
  `https://` URL in the string. All 14 repaired URLs return 200. A normal URL passes
  through unchanged, so if Ti.to fixes this the code needs no change. A small addition to
  `fetch_from_api()`, which is otherwise kept as-is.
- **2026-09-30. The "duplicates" are regional cohorts; show both.** Each
  `updated-product-training-for-2027-*-1`/`-2` pair is one course run for Americas & Europe
  and again for Asia-Pacific, Middle East & Africa, on the same dates (`docs/FINDINGS.md`
  section 6). The region comes from the globe-icon line in the Ti.to description. It is shown
  on the card (the date band until 2026-10-01), JSON-LD and `llms.txt`, and is part of the dedupe key. Narrows the
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
  shown on the card (in the date band until 2026-10-01) as e.g. "9:00–11:00 AM CDT", between the date and the place (guide
  p.21: "date, time and place"). JSON-LD `startDate`/`endDate` become full datetimes when
  times are known. Rails zone names are mapped to IANA zones for the abbreviation; unknown
  zones or zones without an abbreviation show a UTC offset. No times from Ti.to, no time line.
- **2026-09-30. Brand guide PDF stays out of git.** It is 20MB and a client-version document.
  It lives in `docs/` locally and is gitignored. Anyone working without it uses
  `docs/BRAND-SPEC.md`, which records what was checked against it.
- ~~**2026-09-30. Date band: option c-alt.** The guide's p.21 gradient trimmed to the 8%-68%
  span where white text clears 3:1: `#04A6A4` to `#008F23` (at 70%) to `#45A928`, white text
  22px bold. Chosen over (a) the guide as written, which fails at 1.6:1; (b) guide colours with
  text squeezed into the middle; and (c) darkened ends, which turned the lime end olive.~~
  Superseded 2026-10-01: no date band
- **2026-09-30. Page intro copy (Josh).** Headline "Build these skills, your way", then
  "Our training is available in person or online, live and interactive, delivered on-site or
  remotely, wherever you’re located. Created by Jeff Gothelf and Josh Seiden, and led by our
  Certified Training Partners worldwide, you get the same training, in the format that fits."
  The H1 stays "Public Workshops"; the headline sits under it as an H2 (styled from the live
  site since 2026-10-01).
- **2026-09-30. Meta description (Josh).** "Upcoming workshops from Sense & Respond Learning:
  live training in Product Management, Lean UX, Product Discovery, OKRs, Outcomes, and
  Storytelling." Also used for `og:description` and the `llms.txt` summary.
- ~~**2026-09-30. The brand guide PDF governs design.** `docs/S&R Brand Guidelines 2025 for
  client 20250611.pdf`. `docs/BRAND-SPEC.md` is a summary, and where they differ the PDF wins.
  Diverge only where the guide is silent or following it would cause a real problem, such as
  readability. Record each divergence, with the reason, under "Brand divergences" below so
  Josh can take it to Natalia. Supersedes the 2026-09-18 "match the live site" decision.~~
  Reversed 2026-10-01: the live site is the reference
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
  Type follows the guide.~~ Superseded 2026-09-30: the guide PDF governs. That was itself
  reversed on 2026-10-01: the live site is the reference again, type included
- **2026-09-18. Collapse duplicate events by default**, keyed on title + start + end + location

## Brand divergences (for Natalia)

Since 2026-10-01 the page follows the live site. This table lists where the live site, and so
the page, departs from the 2025 guide, for Natalia's guide update, plus the gaps both leave
that the page had to fill. Updated 2026-10-01.

| # | What | Guide | Live site and page | Note |
|---|---|---|---|---|
| 1 | H1 | Oswald **Bold** 72px, capitals in the samples | Oswald **Regular** 78.5px at 1440px wide, 48px on phones, sentence case | Live H1 is 4.5rem on an 18px root |
| 2 | H2 | Oswald Regular 36px | Oswald Regular 61.2px desktop, 38px phone | Live H2 is 3.5rem |
| 3 | Body text | Roboto 18px | Roboto 1.1rem: 19.7px desktop, 17px phone, line height 1.6 | |
| 4 | Text colour | Mockups use dark grey `#343131` | Black `#000000` for body and headings; Slate `#58585A` for eyebrows and secondary text | |
| 5 | Buttons | Dark rectangle, Roboto Bold 24px (p.19 mockup) | Deep Teal `#345C60` pill, radius 300px, Roboto 600 16.3px, capitalized, hover to 80% opacity | |
| 6 | Deep Teal's role | Secondary, sparing accent | Main action colour: buttons and links | |
| 7 | Text links | Silent | Deep Teal Roboto 600, no underline; hover fills Deep Teal, white text | The live tertiary button |
| 8 | Workshop date gradient | p.21: date, time and place on a gradient, white text | Not used. Slate text on white | Courses use different gradients (Natalia) |
| 9 | Eyebrow labels | Silent | Roboto Bold, body size, Slate, typed in capitals | Live Individuals page |
| 10 | Hero background | Silent | White fading to Key Lime and cyan, as an image (`hero-gradient.jpg`) | Supplied by Natalia |
| 11 | Card radius | Silent | 16px (page only) | Live cards are SVG shapes with no CSS radius; chosen to match ti.to |
| 12 | Keyboard focus ring | Silent | 3px Iron outline (page only) | Needed for keyboard users. Live site removes the outline on hover only |
| 13 | Colour names | p.13 labels `#00A651` "Violet" and `#0072BC` "New Leaf" | Unaffected | The labels look mislabelled |

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

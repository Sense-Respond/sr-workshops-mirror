# Analytics handoff: workshops.senseandrespond.co

**For:** Jeff
**From:** Josh
**Date:** 1 October 2026
**Status updated:** 7 October 2026

---

## Status, 6 October 2026

Jeff worked through the list on 6 October 2026 (his report: "2026 Oct 6 status update and
next Steps.md"). Items 1, 2, 4, 5 and 7 are done; item 3 is fixed; items 6 and 8 are with
Josh; 9 and 10 are open. Jeff also found that first visits lost their traffic source; the
page fix is live and confirmed in Realtime on 7 October 2026 (see "First-visit traffic source" at
the end of the action items).

| Item | Status | Owner |
|---|---|---|
| 1. Realtime check, AI assistants channel order | Done | — |
| 2. Outbound clicks | Done, no change | — |
| 3. `tito_click` key event | Fixed: wrong trigger | — |
| 4. Workshops report | Done, in Explore | — |
| 5. Main site as referral | Done, not happening | — |
| 6. Extra tags | Remove the UA ID in Squarespace | Josh |
| 7. Consent settings | Done, "Your setup is good" | — |
| 8. Search Console link | Add Jeff as Owner | Josh |
| 9. Monthly AI-answer check | Open: question set | Josh → Jeff |
| 10. Banner wording | Open, optional | Jeff / legal |
| First-visit traffic source | Done: fixed, confirmed in Realtime | — |

## Summary

The workshops page reports to the same Google Analytics property as senseandrespond.co. It
tracks visits, where they came from (including AI assistants), and every click through to a
workshop on ti.to. It doesn't track purchases, which happen on ti.to. Jeff: please work
through the action items below, starting with the Realtime check.

## What's set up

The public workshops page at **https://workshops.senseandrespond.co** sends data to the
**same GA4 property as senseandrespond.co**, so both appear in one view. Josh has also added
a channel for visits from AI assistants.

### Details

- **Measurement ID:** `G-WPJMQ52FEF`, standard gtag.js snippet, default settings
- **Cookies:** `_ga` and `_ga_WPJMQ52FEF` are set on `.senseandrespond.co`, the same domain
  the main site uses. A visitor's ID and sessions carry across the two. No cross-domain
  setup is needed or configured
- **Consent:** Google Consent Mode v2. All four consent types (`ad_storage`, `ad_user_data`,
  `ad_personalization`, `analytics_storage`) start as denied. Until a visitor clicks
  "Accept all", GA gets cookieless pings only (`gcs=G100`); after, full hits (`gcs=G111`).
  The choice is remembered in the visitor's browser. The page has its own banner, separate
  from the Squarespace one, so a visitor who accepted on the main site is asked again here
- **Clicks to Ti.to:** every Register / See details button, title and banner links to a
  Ti.to event page. GA4's enhanced measurement records each one as a `click` event with
  `outbound = true`, `link_domain = ti.to`, `link_url` (which includes the event's slug, so
  it says which workshop) and `link_classes` (`btn` for the button). This is the measure
  of interest in each workshop. Purchases happen on Ti.to and are **not** in GA
- **Ti.to links** also carry `?source=workshops-page`. Not relied on: Ti.to only reports
  sources that are saved on each event, and nobody will do that per event
- **AI assistants channel:** on 2026-10-01 Josh created a custom channel group with an "AI
  assistants" channel: Source matches regex
  `chatgpt|openai|perplexity|claude|anthropic|gemini|copilot`. In Reports > Acquisition >
  Traffic acquisition, switch the primary dimension to this channel group to see visits
  from AI assistants separately from other referrals

Checked on 1 October 2026 from a test browser:

| Check | Result |
|---|---|
| Page view sent, before consent | Yes, cookieless, hostname `workshops.senseandrespond.co` |
| Page view sent, after "Accept all" | Yes, with cookies |
| Cookie domain | `.senseandrespond.co` |
| Outbound click on Register | Yes: `click`, `outbound=true`, `link_domain=ti.to` |
| Enhanced measurement, outbound clicks | On, according to the tag Google serves for this stream |

Not checked: anything inside the GA interface. That's the list below.

## Action items

In priority order.

**1. Confirm the page appears in Realtime.** *Done 2026-10-06 (Jeff): page views, `click`
and `tito_click` arrive; "AI assistants" is at position 15, Referral at 17.*
Reports > Realtime. Open https://workshops.senseandrespond.co in a normal browser, click
"Accept all", and look for the visit. Add a comparison or filter on **Hostname =
workshops.senseandrespond.co**. Our test visits were on 1 October 2026 at about 21:27,
21:29 and 21:40 UTC (headless Chrome, so they may show as an unusual browser).

Quick check while you're in GA: Admin > Data display > Channel groups > the custom group.
The **AI assistants** channel must sit **above Referral**. GA evaluates channels top to
bottom and uses the first match, so below Referral it would never receive any traffic.

**2. Confirm enhanced measurement's outbound clicks stay on.** *Done 2026-10-06 (Jeff): on,
no ti.to domain configured, no change.*
Admin > Data streams > the web stream for `G-WPJMQ52FEF` > Enhanced measurement. "Outbound
clicks" must be on. Turning it off stops the workshop click data. Don't add ti.to under
"Configure your domains": that would make clicks to it stop counting as outbound.

**3. Make clicks to Ti.to a key event.** *Fixed 2026-10-06 (Jeff): `tito_click` already
existed as a key event, but triggered on `event_name = page_view` and `page_location`
contains ti.to, which can never fire, because GA doesn't run on ti.to. Now `event_name =
click` and `link_domain` equals ti.to (case-insensitive), with "Copy parameters from the
source event" ticked so `link_url` carries over. Confirmed in Realtime.*
So they show up as conversions in standard reports:
- Admin > Events > Create event. Name it e.g. `tito_click`. Conditions:
  `event_name equals click` and `link_domain equals ti.to`
- Then Admin > Key events: mark `tito_click` as a key event
- Optional: register `link_url` and `link_classes` as event-scoped custom dimensions
  (Admin > Custom definitions) if they're not already available in your reports. In
  Explorations, "Link URL" and "Link domain" are built-in dimensions

**4. Build a workshops report.** *Done 2026-10-06 (Jeff): Explore → "Workshops – Ti.to
clicks", private to Jeff. Tabs "By workshop" and "Traffic by site".*
An Exploration (free form) with:
- Rows: Link URL (one row per workshop), optionally Link classes
- Values: Event count, Total users
- Filter: Event name = `click` (or `tito_click`), Link domain = ti.to
- Optionally break down by Session source / medium to see where interested visitors came
  from (search, the main site, AI assistants, email)

**5. Check the main site isn't showing up as a referral.** *Done 2026-10-06 (Jeff): not
happening, no change.*
Visitors arrive from www.senseandrespond.co (the "Public Workshops" nav item, once it's
repointed). Because both sites share cookies, the session should carry on. If
`senseandrespond.co` starts appearing as a referral source for this hostname, add it under
Admin > Data streams > Configure tag settings > **List unwanted referrals** (referral domain
contains `senseandrespond.co`).

**6. Decide about the main site's extra tags.** *Josh's (Squarespace). Jeff found
`G-6MMTGMY8G1` is loaded through the UA tag `UA-145067854-1` in Squarespace's Google
Analytics field. Remove the UA ID there, leaving `G-WPJMQ52FEF`; that also stops data to
`G-6MMTGMY8G1`, so check nobody uses it first. Not a repo task.*
Found while testing: the main site also sends every hit to a second GA4 property,
`G-6MMTGMY8G1`, and sets a Universal Analytics cookie (`_gat_gtag_UA_145067854_1`;
Google stopped processing Universal Analytics data in 2023 and 2024). The workshops page sends only to
`G-WPJMQ52FEF`, so the second property sees the main site but not this page. Confirm
whether `G-6MMTGMY8G1` is intended, and remove the UA tag from Squarespace if it's left
over.

**7. Check consent settings in GA.** *Done 2026-10-06 (Jeff): "Your setup is good".
Analytics consent signals active.*
Admin > Data collection and modification > consent settings (or the "Consent settings"
status on the data stream). Confirm GA shows consent signals as received for this stream.
If you use behavioural modelling for consented-out visitors, this page now supplies the
cookieless pings it needs.

**8. Link Search Console to this property.** *Josh's. Blocked: Jeff isn't a verified owner
of the Search Console property. Josh to add Jeff as an Owner (Search Console → Settings →
Users and permissions), or link it himself.*
Admin > Product links > Search Console links > Link, then choose the senseandrespond.co
property. It's a Domain property, so it already covers workshops.senseandrespond.co. This
brings Google search queries and impressions for the page into GA.

**9. Run a monthly AI-answer check.** *Open: Josh is sending Jeff the question set.*
Once a month, run a fixed set of buyer questions in ChatGPT, Claude, Perplexity and Gemini,
and record for each answer whether S&R is cited and which link it gives (this page, the main
site, ti.to or none). Use the same questions every month so the results compare. Josh has the
question set. GA shows the visits that result; this shows whether we're in the answers at all.

**10. Optional: privacy and banner wording.** *Open, optional.*
The banner reads: "Select “Accept all” to agree to our use of cookies and similar
technologies for analytics. Select “Decline” to opt out." It has no privacy-policy link,
matching the main site's banner. If you or legal want a link or different wording, tell
Josh; it's a one-line change in `build.py`.

**First-visit traffic source (found by Jeff, 2026-10-06).** A first visit's page view went
out before consent as a cookieless ping, which GA doesn't report, and "Accept all" only
updated consent, so the visit and its clicks had no source. Fixed in `build.py`: "Accept all"
now sends `gtag("event", "page_view")` right after the consent update. Live since 6 October
2026 (template version 7). *Done: confirmed by Josh in Realtime on 7 October 2026. A
private window on `?utm_source=test`, then "Accept all", showed a `page_view` with source
"test".*

## Who to ask

Code and page: Josh (the page is built daily from Ti.to by a GitHub Action in
`Sense-Respond/sr-workshops-mirror`). Decisions and their reasons are in `PROJECT_BRIEF.md`
in that repo, under "Analytics, 2026-10-01".

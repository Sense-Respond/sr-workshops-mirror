# Analytics handoff: workshops.senseandrespond.co

**For:** S&R analytics
**From:** Josh
**Date:** 1 October 2026

---

## What's set up

The public workshops page at **https://workshops.senseandrespond.co** sends data to the
**same GA4 property as senseandrespond.co**, so both appear in one view.

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

**1. Confirm the page appears in Realtime.**
Reports > Realtime. Open https://workshops.senseandrespond.co in a normal browser, click
"Accept all", and look for the visit. Add a comparison or filter on **Hostname =
workshops.senseandrespond.co**. Our test visits were on 1 October 2026 at about 21:27,
21:29 and 21:40 UTC (headless Chrome, so they may show as an unusual browser).

**2. Confirm enhanced measurement's outbound clicks stay on.**
Admin > Data streams > the web stream for `G-WPJMQ52FEF` > Enhanced measurement. "Outbound
clicks" must be on. Turning it off stops the workshop click data. Don't add ti.to under
"Configure your domains": that would make clicks to it stop counting as outbound.

**3. Make clicks to Ti.to a key event.**
So they show up as conversions in standard reports:
- Admin > Events > Create event. Name it e.g. `tito_click`. Conditions:
  `event_name equals click` and `link_domain equals ti.to`
- Then Admin > Key events: mark `tito_click` as a key event
- Optional: register `link_url` and `link_classes` as event-scoped custom dimensions
  (Admin > Custom definitions) if they're not already available in your reports. In
  Explorations, "Link URL" and "Link domain" are built-in dimensions

**4. Build a workshops report.**
An Exploration (free form) with:
- Rows: Link URL (one row per workshop), optionally Link classes
- Values: Event count, Total users
- Filter: Event name = `click` (or `tito_click`), Link domain = ti.to
- Optionally break down by Session source / medium to see where interested visitors came
  from (search, the main site, AI assistants, email)

**5. Check the main site isn't showing up as a referral.**
Visitors arrive from www.senseandrespond.co (the "Public Workshops" nav item, once it's
repointed). Because both sites share cookies, the session should carry on. If
`senseandrespond.co` starts appearing as a referral source for this hostname, add it under
Admin > Data streams > Configure tag settings > **List unwanted referrals** (referral domain
contains `senseandrespond.co`).

**6. Decide about the main site's extra tags.**
Found while testing: the main site also sends every hit to a second GA4 property,
`G-6MMTGMY8G1`, and sets a Universal Analytics cookie (`_gat_gtag_UA_145067854_1`;
Google stopped processing Universal Analytics data in 2023 and 2024). The workshops page sends only to
`G-WPJMQ52FEF`, so the second property sees the main site but not this page. Confirm
whether `G-6MMTGMY8G1` is intended, and remove the UA tag from Squarespace if it's left
over.

**7. Check consent settings in GA.**
Admin > Data collection and modification > consent settings (or the "Consent settings"
status on the data stream). Confirm GA shows consent signals as received for this stream.
If you use behavioural modelling for consented-out visitors, this page now supplies the
cookieless pings it needs.

**8. Optional: privacy and banner wording.**
The banner reads: "Select “Accept all” to agree to our use of cookies and similar
technologies for analytics. Select “Decline” to opt out." It has no privacy-policy link,
matching the main site's banner. If you or legal want a link or different wording, tell
Josh; it's a one-line change in `build.py`.

## Who to ask

Code and page: Josh (the page is built daily from Ti.to by a GitHub Action in
`Sense-Respond/sr-workshops-mirror`). Decisions and their reasons are in `PROJECT_BRIEF.md`
in that repo, under "Analytics, 2026-10-01".

# Public Workshops Page: Briefing Note

**For:** Jeff, Natalia
**From:** Josh
**Date:** 18 September 2026, updated 1 October 2026 (after design review with Natalia, and analytics)

---

## Where it stands

The page is live at **workshops.senseandrespond.co**. A script pulls our workshops from ti.to every day and publishes the page. We tested it the way an AI crawler sees it, with no JavaScript, and every workshop is there. The design pass from the 1 October review is live. Natalia will repoint the nav once she has approved it. The page now also reports to Google Analytics.

## Goals

1. **Make our public workshops easy to find.** Today the nav item "Public Workshops" sends people off our site to ti.to. We want a workshops page on our own domain, one click from the home page.

2. **Make the workshop list readable by search engines and by AI assistants.** We want people who ask ChatGPT, Claude, Gemini or Perplexity about product management training to find our classes. Our ti.to page is built with JavaScript, so those crawlers can't read it. We are invisible to them right now.

Goal 2 is the one that shapes everything below.

## The constraint we hit

AI crawlers do not run JavaScript. Per Vercel's crawler study, GPTBot downloads JavaScript files but never runs them, and ClaudeBot and PerplexityBot behave the same way. They read the raw HTML a server sends and move on. Googlebot is the one exception.

That rules out the obvious fix. We are on Squarespace 7.1, which has no API for writing page content, no Developer Mode, and no way to route a page to another host. So nothing can put an auto-updating, server-rendered workshop list on senseandrespond.co/workshops. Any solution that injects the list with JavaScript would just move our invisibility problem onto our own domain.

## The solution

Host it on Netlify, where webinar.senseandrespond.co already lives, with a GitHub repo driving the daily build.

- A script reads our workshops from the ti.to API once a day
- It writes a complete, plain HTML page, with every workshop in the markup
- Netlify serves it at **workshops.senseandrespond.co**
- Our Squarespace nav points there

Because the page is real HTML, a crawler gets the full list on its first request. No JavaScript involved.

We also add what our webinar subdomain doesn't have today:

- **Structured data** on every workshop (name, dates, price, registration link) so an assistant can answer "what OKR training is running in November" with facts rather than guesses
- **robots.txt** that explicitly welcomes GPTBot, ClaudeBot, PerplexityBot and Google-Extended
- **sitemap.xml** and **llms.txt** for the subdomain

Design follows the live senseandrespond.co site, so the page looks like the rest of our site. Where the live site is silent, we use the 2025 brand guidelines.

## What we learned along the way

**The "duplicate" ti.to events are regional cohorts.** Six pairs of events share a title and dates. Each pair is one run for Americas & Europe and one for Asia-Pacific, Middle East & Africa. The new page shows both, labelled by region. On ti.to itself they still look like duplicates, because the titles are identical. Adding the region to the titles in ti.to would fix that.

## What we agreed in the design review (Natalia, 1 October)

- **The live site is the design reference.** Where the live site and the brand guide differ, the page follows the live site. Natalia will update the guide to match the choices she has made on the site
- **Buttons** match the live site: rounded, dark green
- **Header:** no copy of the full site menu. The page gets the logo and the live site's white-to-gradient background
- **Workshop images:** keep the ti.to images and make them larger, closer to ti.to's own layout. We dropped the idea of trainer portraits
- **Date, time and place** sit in dark gray text on white, lighter than the title. No gradient band, because our courses use different gradients
- Natalia supplied the corrected logo and the background image

## Analytics

The page reports to the same Google Analytics property as senseandrespond.co, so both show up in one view, and visitors' sessions carry across. It asks for cookie consent first, with a banner like the one on our main site. GA counts every click from the page to a workshop on ti.to, so we can see which workshops draw interest and where those visitors came from. Purchases happen on ti.to and don't show in GA.

The setup tasks inside GA are listed in `docs/ANALYTICS-HANDOFF.md` in the project repo, for our analytics person.

## Still open

**1. A way back to the main site. (Natalia, Josh)**
Natalia suggested a "Go back" button that returns visitors to the page they came from. We'll try it in the next pass. It needs a small script, so we'll also keep a plain link to senseandrespond.co for anyone who arrives directly.

**2. What goes on senseandrespond.co/workshops. (Jeff)**
A subdomain is weaker than our main domain for Google. The fix is a short evergreen page on Squarespace about the workshop catalogue, built once by hand, linking to the live schedule. That copy overlaps the repositioning work, where /courses is already the canonical course page. It should probably be scoped into that project rather than decided separately.

## Next steps

| # | Step | Owner | Status |
|---|---|---|---|
| 1 | Build the page and the daily update | Josh | Done |
| 2 | Put it live at workshops.senseandrespond.co | Josh | Done |
| 3 | Design pass from the 1 October review | Josh | Done |
| 4 | Review the new version | Natalia | After step 3 |
| 5 | Repoint the "Public Workshops" nav item | Natalia | After step 4 |
| 6 | Update the brand guide to match the live site | Natalia | Open |
| 7 | Decide where the evergreen /workshops copy belongs | Jeff | Open |
| 8 | Add the region to the cohort titles in ti.to, and set their time zones | Josh | Open |
| 9 | Google Analytics on the page, with cookie consent | Josh | Done |
| 10 | GA setup: key event for clicks to ti.to, workshops report | Analytics | Open |

Every daily update re-checks that each workshop title is readable with JavaScript switched off.

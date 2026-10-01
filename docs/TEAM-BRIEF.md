# Public Workshops Page: Briefing Note

**For:** Jeff, Natalia
**From:** Josh
**Date:** 18 September 2026

---

## Goals

1. **Make our public workshops easy to find.** Today the nav item "Public Workshops" sends people off our site to ti.to. We want a workshops page on our own domain, one click from the home page.

2. **Make the workshop list readable by search engines and by AI assistants.** We want people who ask ChatGPT, Claude, Gemini or Perplexity about product management training to find our classes. Our ti.to page is built with JavaScript, so those crawlers can't read it. We are invisible to them right now.

Goal 2 is the one that shapes everything below.

## The constraint we hit

AI crawlers do not run JavaScript. Per Vercel's crawler study, GPTBot downloads JavaScript files but never runs them, and ClaudeBot and PerplexityBot behave the same way. They read the raw HTML a server sends and move on. Googlebot is the one exception.

That rules out the obvious fix. We are on Squarespace 7.1, which has no API for writing page content, no Developer Mode, and no way to route a page to another host. So nothing can put an auto-updating, server-rendered workshop list on senseandrespond.co/workshops. Any solution that injects the list with JavaScript would just move our invisibility problem onto our own domain.

## The solution

Host it on Netlify, where webinar.senseandrespond.co already lives. Same host, different deploy mechanism: the webinar site isn't connected to GitHub, so linking this one to GitHub is a first-time step.

- A script reads our workshops from the ti.to API once a day
- It writes a complete, plain HTML page, with every workshop in the markup
- Netlify serves it at **workshops.senseandrespond.co**
- Our Squarespace nav points there

Because the page is real HTML, a crawler gets the full list on its first request. No JavaScript involved.

We also add what our webinar subdomain doesn't have today:

- **Structured data** on every workshop (name, dates, price, registration link) so an assistant can answer "what OKR training is running in November" with facts rather than guesses
- **robots.txt** that explicitly welcomes GPTBot, ClaudeBot, PerplexityBot and Google-Extended
- **sitemap.xml** and **llms.txt** for the subdomain

Design follows the 2025 brand guidelines: Oswald and Roboto at the specified sizes, and the Cerulean-to-Spring-Green gradient the guide prescribes for workshop date blocks.

## What we need to decide

**1. The brand guide and the live site disagree. (Natalia)**
The guide shows dark Iron rectangular buttons and lists Deep Teal `#345C60` as a sparing accent. Our live site uses Deep Teal pill buttons everywhere as the main action color. Body copy is 18px in the guide and about 14px on the site. For now we match the live site so the new page doesn't look foreign. The real question is whether we correct the site or update the guide.

*Update, 30 September 2026: decided. The brand guide governs the new page, not the live site. Where the page departs from the guide, the reasons are listed for Natalia under "Brand divergences" in `PROJECT_BRIEF.md`.*

**2. Six of our 21 upcoming ti.to events are exact duplicates. (Josh)**
Six pairs share a title and dates, with slugs differing only by a trailing -1 and -2, all under the `updated-product-training-for-2027` family. Visitors to our ti.to page see each of these listed twice today. If they are separate cohorts or time zones they need distinct titles. If they are mistakes they should be deleted.

*Update, 30 September 2026: resolved. They are not duplicates. Each pair is one course run twice, once for Americas & Europe and once for Asia-Pacific, Middle East & Africa. The page lists both and shows the region on each.*

**3. What goes on senseandrespond.co/workshops. (Jeff)**
A subdomain is weaker than our main domain for Google. The fix is a short evergreen page on Squarespace about the workshop catalogue, built once by hand, linking to the live schedule. That copy overlaps the repositioning work, where /courses is already the canonical course page. It should probably be scoped into that project rather than decided separately.

## Next steps

| # | Step | Owner |
|---|---|---|
| 1 | Generate a ti.to API token | Josh |
| 2 | Create the repo, connect it to Netlify, point the `workshops` subdomain | Josh (done 1 Oct: live at workshops.senseandrespond.co) |
| 3 | Confirm the brand approach for the new page | Natalia |
| 4 | Resolve the six duplicate ti.to events | Josh (done: regional cohorts, 30 Sep) |
| 5 | Repoint the "Public Workshops" nav item once the page is live | Natalia |
| 6 | Decide where the evergreen /workshops copy belongs | Jeff |

Steps 1 and 2 unblock everything else. Once the page is live we will verify it by loading it with JavaScript switched off and confirming every workshop title is still there.

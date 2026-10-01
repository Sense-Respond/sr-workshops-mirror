"""Tests for the render layer and main() guards. Run: python3 -m unittest discover tests"""

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
import urllib.error
import xml.dom.minidom
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build  # noqa: E402
import verify  # noqa: E402

SAMPLE = os.path.join(ROOT, "docs", "sample-workshops.json")


def sample_events():
    with open(SAMPLE, encoding="utf-8") as fh:
        return json.load(fh)["events"]


def run_main(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = build.main(list(argv))
    return code, out.getvalue()


def ev(slug, title="Lean Product Strategy", start="2026-11-03", end="2026-11-05", **kw):
    e = {"title": title, "slug": slug, "url": f"https://ti.to/sense-respond-learning/{slug}",
         "start": start, "end": end, "date_label": "x", "location": None, "banner": None,
         "price_from": None, "currency": "USD"}
    e.update(kw)
    return e


class DateMarkup(unittest.TestCase):
    CASES = [("2026-10-13", "2026-10-27"), ("2026-09-17", "2026-10-08"),
             ("2026-12-30", "2027-01-02"), ("2026-09-22", "2026-09-22"), ("2026-09-22", None)]

    def test_text_matches_format_range(self):
        for start, end in self.CASES:
            got = re.sub(r"<[^>]+>", "", build.date_range_html({"start": start, "end": end}))
            want = build.format_range(build.parse_date(start), build.parse_date(end))
            self.assertEqual(got, want)

    def test_every_date_has_time_element(self):
        h = build.date_range_html({"start": "2026-09-17", "end": "2026-10-08"})
        self.assertEqual(re.findall(r'datetime="([^"]+)"', h), ["2026-09-17", "2026-10-08"])
        h = build.date_range_html({"start": "2026-09-22", "end": "2026-09-22"})
        self.assertEqual(re.findall(r'datetime="([^"]+)"', h), ["2026-09-22"])

    def test_no_dates_falls_back_to_label(self):
        self.assertEqual(build.date_range_html({"date_label": "Soon & later"}), "Soon &amp; later")


class Online(unittest.TestCase):
    def test_online_detection(self):
        for loc in (None, "", "Online", "ONLINE", "Live online", "Zoom", "zoom (link sent)"):
            self.assertTrue(build.is_online(loc), loc)
        for loc in ("Berlin", "Zoomania Hall", "London, UK"):
            self.assertFalse(build.is_online(loc), loc)

    def test_schema_by_location(self):
        online = build.event_schema(ev("a", location="Zoom"), "a")
        self.assertEqual(online["eventAttendanceMode"], "https://schema.org/OnlineEventAttendanceMode")
        self.assertEqual(online["location"]["@type"], "VirtualLocation")
        offline = build.event_schema(ev("b", location="Berlin"), "b")
        self.assertEqual(offline["eventAttendanceMode"], "https://schema.org/OfflineEventAttendanceMode")
        self.assertEqual(offline["location"], {"@type": "Place", "name": "Berlin", "address": "Berlin"})


class Page(unittest.TestCase):
    def render(self, events):
        return build.render_page(events, "30 Sep 2026, 11:00 UTC", "2026-09-30T11:00:00+00:00")

    def jsonld(self, page):
        return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',
                                    page, re.S).group(1))

    def test_every_title_in_raw_html(self):
        events = sample_events()
        p = verify.PageParser()
        p.feed(self.render(events))
        self.assertEqual(p.titles, [e["title"] for e in events])
        self.assertEqual(p.article_ids, [e["slug"] for e in events])

    def test_only_jsonld_analytics_and_consent_scripts(self):
        # Rule since 2026-10-01: JSON-LD, the inline consent/GA script and gtag.js, nothing
        # else. No script may carry or render workshop data.
        events = sample_events()
        page = self.render(events)
        scripts = re.findall(r"<script\b[^>]*>", page)
        self.assertEqual(scripts, [
            '<script type="application/ld+json">',
            '<script>',
            '<script async src="https://www.googletagmanager.com/gtag/js?id=G-WPJMQ52FEF">',
        ])
        inline = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
        self.assertEqual(inline, build.ANALYTICS_JS)
        for e in events:
            self.assertNotIn(e["title"], inline)
        self.assertNotIn("innerHTML", inline)
        self.assertNotIn("fetch(", inline)

    def test_consent_mode_defaults_denied(self):
        js = build.ANALYTICS_JS
        self.assertLess(js.index('gtag("consent", "default"'), js.index('gtag("config", "G-WPJMQ52FEF")'))
        self.assertIn('choice === "granted" ? "granted" : "denied"', js)
        for key in ("ad_storage", "ad_user_data", "ad_personalization", "analytics_storage"):
            self.assertIn(key, js)
        page = self.render([ev("a")])
        self.assertIn('<section class="consent" id="consent" aria-label="Cookie consent" hidden>', page)

    def test_links_to_tito_carry_source(self):
        e = ev("okr", banner="https://example.com/b.png")
        page = self.render([e])
        tagged = e["url"] + "?source=workshops-page"
        self.assertEqual(page.count(f'href="{tagged}"'), 3)  # banner, title, button
        self.assertNotIn(f'href="{e["url"]}"', page)
        event = [n for n in self.jsonld(page)["@graph"] if n["@type"] == "Event"][0]
        self.assertEqual(event["url"], e["url"])  # structured data keeps the plain URL
        self.assertEqual(build.tracked_url("https://ti.to/a/b?source=x&discount_code=y"),
                         "https://ti.to/a/b?discount_code=y&source=workshops-page")

    def test_full_event_jsonld(self):
        e = ev("okr", price_from=1200.0, banner="https://example.com/b.png")
        graph = self.jsonld(self.render([e]))["@graph"]
        event = [n for n in graph if n["@type"] == "Event"][0]
        self.assertEqual(event["name"], "Lean Product Strategy")
        self.assertEqual(event["startDate"], "2026-11-03")
        self.assertEqual(event["endDate"], "2026-11-05")
        self.assertEqual(event["offers"], {"@type": "Offer", "url": e["url"],
                                           "price": "1200.00", "priceCurrency": "USD"})
        self.assertEqual(event["eventAttendanceMode"], "https://schema.org/OnlineEventAttendanceMode")
        self.assertEqual(event["organizer"], {"@id": "https://senseandrespond.co/#org"})
        self.assertIn({"@type": "Organization", "@id": "https://senseandrespond.co/#org",
                       "name": "Sense & Respond Learning", "url": "https://senseandrespond.co"}, graph)
        self.assertEqual(event["@id"], "https://workshops.senseandrespond.co/#okr")

    def test_jsonld_cannot_close_script_tag(self):
        evil = ev("x", title="Bad </script><script>alert(1)</script>")
        page = self.render([evil])
        block = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1)
        self.assertNotIn("<", block)
        self.assertEqual(self.jsonld(page)["@graph"][1]["name"], evil["title"])
        self.assertIn("Bad &lt;/script&gt;", page)  # escaped in the visible HTML too

    def test_anchor_ids_unique_and_safe(self):
        self.assertEqual(build.assign_anchors([ev("A b/c"), ev("a-b-c"), ev("")]),
                         ["a-b-c", "a-b-c-2", "workshop"])

    def test_empty_page(self):
        page = self.render([])
        self.assertIn("No public workshops are scheduled right now", page)
        self.assertEqual(self.jsonld(page)["@graph"][0]["@type"], "Organization")

    def test_header_and_lede(self):
        page = self.render([ev("a")])
        # Live-site design (2026-10-01): logo linked home, hero image, no gradient date band.
        self.assertIn('<a class="logo" href="https://senseandrespond.co"><img src="assets/sr-logo.svg"', page)
        self.assertIn('url("assets/hero-gradient.jpg")', page)
        self.assertIn('<link rel="icon" href="assets/sr-logomark.svg"', page)
        self.assertNotIn("linear-gradient", page)
        self.assertIn('<a class="link" href="https://www.senseandrespond.co/individuals">'
                      '← Back to senseandrespond.co</a>', page)
        self.assertIn('<h2 class="lede-head">Build these skills, your way</h2>', page)
        self.assertIn("wherever you’re located", page)
        self.assertIn("<mark>you get the same training, in the format that fits</mark>.", page)

    def test_assets_exist(self):
        root = os.path.join(os.path.dirname(__file__), "..", "public", "assets")
        for name in ("sr-logo.svg", "sr-logomark.svg", "hero-gradient.jpg"):
            self.assertTrue(os.path.isfile(os.path.join(root, name)), name)

class TimesAndSoldOut(unittest.TestCase):
    TIMED = dict(start_at="2026-11-03T09:00:00.000-06:00", end_at="2026-11-05T11:00:00.000-06:00",
                 timezone="Central Time (US & Canada)")

    def render(self, events):
        return build.render_page(events, "30 Sep 2026, 11:00 UTC", "2026-09-30T11:00:00+00:00")

    def event_ld(self, e):
        return build.event_schema(e, "a")

    def test_time_line_in_band(self):
        page = self.render([ev("a", **self.TIMED)])
        self.assertIn('<p class="ws-time"><time datetime="2026-11-03T09:00-06:00">9:00</time>–'
                      '<time datetime="2026-11-05T11:00-06:00">11:00 AM CST</time></p>', page)

    def test_no_time_line_without_times_or_zone(self):
        self.assertNotIn("ws-time", self.render([ev("a")]))
        self.assertNotIn("ws-time", self.render([ev("a", timezone="UTC")]))

    def test_zone_line_when_no_times(self):
        page = self.render([ev("a", timezone="New Delhi", start_at="2026-11-03T00:00:00+05:30",
                               end_at="2026-11-05T00:00:00+05:30")])
        self.assertIn('<p class="ws-time">Time zone: IST (New Delhi)</p>', page)

    def test_region_shown_and_in_jsonld(self):
        e = ev("a", region="Asia-Pacific, Middle East & Africa")
        page = self.render([e])
        self.assertIn('<p class="ws-region">Asia-Pacific, Middle East &amp; Africa</p>', page)
        self.assertEqual(build.event_schema(e, "a")["description"],
                         "Asia-Pacific, Middle East & Africa cohort.")
        self.assertIn("Asia-Pacific, Middle East & Africa", build.render_llms([e], "x"))

    def test_jsonld_uses_datetimes_when_known(self):
        ld = self.event_ld(ev("a", **self.TIMED))
        self.assertEqual(ld["startDate"], "2026-11-03T09:00:00-06:00")
        self.assertEqual(ld["endDate"], "2026-11-05T11:00:00-06:00")
        self.assertEqual(self.event_ld(ev("b"))["startDate"], "2026-11-03")

    def test_availability(self):
        self.assertEqual(self.event_ld(ev("a", sold_out=True))["offers"]["availability"],
                         "https://schema.org/SoldOut")
        self.assertEqual(self.event_ld(ev("a", sold_out=False))["offers"]["availability"],
                         "https://schema.org/InStock")
        self.assertNotIn("availability", self.event_ld(ev("a"))["offers"])

    def test_sold_out_card(self):
        page = self.render([ev("a", sold_out=True, price_from=900.0)])
        self.assertIn('<p class="ws-price">Sold out</p>', page)
        self.assertIn(">See details<span", page)
        self.assertNotIn("From $900", page)
        self.assertIn(">Register<span", self.render([ev("b", sold_out=False)]))

    def test_llms_has_times_and_sold_out(self):
        text = build.render_llms([ev("a", sold_out=True, **self.TIMED)], "x")
        self.assertIn("9:00–11:00 AM CST", text)
        self.assertIn("Sold out", text)


class Siblings(unittest.TestCase):
    def test_robots_allows_ai_crawlers(self):
        robots = build.render_robots()
        for bot in ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "CCBot"):
            self.assertIn(f"User-agent: {bot}\nAllow: /\n", robots)
        self.assertNotIn("Disallow", robots)
        self.assertIn("Sitemap: https://workshops.senseandrespond.co/sitemap.xml", robots)

    def test_sitemap_is_valid_xml(self):
        doc = xml.dom.minidom.parseString(build.render_sitemap("2026-09-30T11:00:00+00:00"))
        self.assertEqual(doc.getElementsByTagName("loc")[0].firstChild.data,
                         "https://workshops.senseandrespond.co/")
        self.assertEqual(doc.getElementsByTagName("lastmod")[0].firstChild.data, "2026-09-30")

    def test_llms_lists_every_workshop(self):
        events = sample_events()
        text = build.render_llms(events, "30 Sep 2026")
        self.assertTrue(text.startswith("# Sense & Respond Learning"))
        for e in events:
            self.assertIn(e["url"], text)
        self.assertIn(r"[Odd \[title\]]", build.render_llms([ev("o", title="Odd [title]")], "x"))


class MainGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "public")
        self.patches = [mock.patch.object(build, "OUT_DIR", self.out),
                        mock.patch.object(build, "TOKEN", "")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def snapshot(self):
        files = {}
        for name in sorted(os.listdir(self.out)):
            with open(os.path.join(self.out, name), encoding="utf-8") as fh:
                files[name] = fh.read()
        return files

    def test_writes_all_files(self):
        code, _ = run_main("--from-json", SAMPLE)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(os.listdir(self.out)),
                         ["index.html", "llms.txt", "robots.txt", "sitemap.xml", "workshops.json"])
        self.assertEqual(verify.main(["verify.py", self.out]), 0)

    def test_no_op_guard_holds_timestamp(self):
        run_main("--from-json", SAMPLE)
        before = self.snapshot()
        code, out = run_main("--from-json", SAMPLE)
        self.assertEqual(code, 0)
        self.assertIn("Nothing written", out)
        self.assertEqual(self.snapshot(), before)

    def test_template_version_change_rewrites(self):
        run_main("--from-json", SAMPLE)
        with mock.patch.object(build, "TEMPLATE_VERSION", build.TEMPLATE_VERSION + 1):
            code, out = run_main("--from-json", SAMPLE)
        self.assertEqual(code, 0)
        self.assertIn("Wrote", out)
        with open(os.path.join(self.out, "workshops.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["template_version"], build.TEMPLATE_VERSION + 1)

    def test_force_rewrites(self):
        run_main("--from-json", SAMPLE)
        code, out = run_main("--from-json", SAMPLE, "--force")
        self.assertEqual(code, 0)
        self.assertIn("Wrote", out)

    def test_empty_page_guard(self):
        run_main("--from-json", SAMPLE)
        before = self.snapshot()
        with mock.patch.object(build, "fetch_from_timeline", return_value=[]):
            code, out = run_main()
        self.assertEqual(code, 1)
        self.assertIn("Keeping the existing files", out)
        self.assertEqual(self.snapshot(), before)

    def test_empty_page_guard_beats_force(self):
        run_main("--from-json", SAMPLE)
        with mock.patch.object(build, "fetch_from_timeline", return_value=[]):
            code, _ = run_main("--force")
        self.assertEqual(code, 1)

    def test_api_failure_with_token_writes_nothing_and_does_not_scrape(self):
        run_main("--from-json", SAMPLE)
        before = self.snapshot()
        err = urllib.error.HTTPError("https://api.tito.io", 401, "Unauthorized", {}, None)
        with mock.patch.object(build, "TOKEN", "expired"), \
                mock.patch.object(build, "fetch_from_api", side_effect=err), \
                mock.patch.object(build, "fetch_from_timeline") as scrape:
            code, out = run_main()
        self.assertEqual(code, 1)
        self.assertIn("ERROR: Ti.to API fetch failed", out)
        scrape.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_api_timeout_with_token_fails(self):
        with mock.patch.object(build, "TOKEN", "t"), \
                mock.patch.object(build, "fetch_from_api", side_effect=TimeoutError("timed out")):
            code, _ = run_main()
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(self.out))

    def test_same_duplicate_survives_whatever_the_order(self):
        pair = [ev("lps-2"), ev("lps-1")]
        survivors = set()
        for events in (pair, list(reversed(pair))):
            with mock.patch.object(build, "fetch_from_timeline", return_value=[dict(e) for e in events]):
                run_main("--force")
            with open(os.path.join(self.out, "workshops.json"), encoding="utf-8") as fh:
                survivors.add(tuple(e["slug"] for e in json.load(fh)["events"]))
        self.assertEqual(survivors, {("lps-1",)})


if __name__ == "__main__":
    unittest.main()

"""Tests for the kept Ti.to data layer of build.py. Run: python3 -m unittest discover tests"""

import datetime as dt
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return fh.read()


class Ordinals(unittest.TestCase):
    def test_ordinals(self):
        cases = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 11: "11th", 12: "12th",
                 13: "13th", 21: "21st", 22: "22nd", 23: "23rd", 31: "31st"}
        for n, want in cases.items():
            self.assertEqual(build.ordinal(n), want)


class DateRanges(unittest.TestCase):
    D = dt.date

    def test_same_month(self):
        self.assertEqual(build.format_range(self.D(2026, 10, 13), self.D(2026, 10, 27)),
                         "October 13th–27th, 2026")

    def test_cross_month(self):
        self.assertEqual(build.format_range(self.D(2026, 9, 17), self.D(2026, 10, 8)),
                         "September 17th–October 8th, 2026")

    def test_cross_year(self):
        self.assertEqual(build.format_range(self.D(2026, 12, 30), self.D(2027, 1, 2)),
                         "December 30th, 2026–January 2nd, 2027")

    def test_single_day(self):
        self.assertEqual(build.format_range(self.D(2026, 9, 22), self.D(2026, 9, 22)),
                         "September 22nd, 2026")
        self.assertEqual(build.format_range(self.D(2026, 9, 22), None), "September 22nd, 2026")

    def test_missing(self):
        self.assertEqual(build.format_range(None, None), "")

    def test_parse_date(self):
        self.assertEqual(build.parse_date("2026-10-13T09:00:00-05:00"), self.D(2026, 10, 13))
        self.assertIsNone(build.parse_date("not a date"))
        self.assertIsNone(build.parse_date(None))


class Prices(unittest.TestCase):
    def test_whole(self):
        self.assertEqual(build.format_price(1200.0, "USD"), "$1,200")

    def test_decimal(self):
        self.assertEqual(build.format_price(99.5, "EUR"), "€99.50")

    def test_null(self):
        self.assertIsNone(build.format_price(None, "USD"))

    def test_rupee(self):
        self.assertEqual(build.format_price(1400, "INR"), "₹1,400")

    def test_unknown_currency(self):
        self.assertEqual(build.format_price(500, "CHF"), "500 CHF")


def api_fixture(today):
    """Ti.to Admin API v3 responses, keyed by path: the events list and each event's releases."""
    iso = lambda d: d.isoformat()  # noqa: E731
    later = today + dt.timedelta(days=30)

    def event(slug, **attrs):
        base = {"id": slug, "title": f"Event {slug}", "slug": slug,
                "start_date": iso(later), "end_date": iso(later + dt.timedelta(days=2)),
                "start_at": iso(later) + "T09:00:00.000-05:00",
                "end_at": iso(later + dt.timedelta(days=2)) + "T11:00:00.000-05:00",
                "timezone": "Central Time (US & Canada)",
                "live": True, "private": False, "test_mode": False, "currency": "USD",
                "location": None, "banner_url": f"https://example.com/{slug}.png"}
        base.update(attrs)
        return base

    events = [
        event("public"),
        event("private", private=True),
        event("test", test_mode=True),
        event("not-live", live=False),
        event("finished", start_date=iso(today - dt.timedelta(days=5)),
              end_date=iso(today - dt.timedelta(days=1))),
        event("in-progress", start_date=iso(today - dt.timedelta(days=2)),
              end_date=iso(today + dt.timedelta(days=2))),
        event("starts-today", start_date=iso(today), end_date=iso(today + dt.timedelta(days=1))),
        event("sold-out", description='<i class="fa-light fa-globe"></i> Americas &amp; Europe\n'
                                      "Course 3 of 6"),
    ]
    releases = {
        "public": [
            {"id": 1, "price": "1200.0", "sold_out": False},
            {"id": 7, "price": "800.0", "sold_out": True},  # sold out: not the "from" price
            {"id": 2, "price": "100.0", "secret": True},
            {"id": 3, "price": "50.0", "archived": True},
            {"id": 4, "price": "0.0", "not_a_ticket": True},
        ],
        "sold-out": [
            {"id": 5, "price": 900, "sold_out": True},
            {"id": 6, "price": 50, "secret": True, "sold_out": False},  # secret: doesn't count
        ],
    }
    responses = {"events": {"events": events, "meta": {"next_page": None}}}
    for slug in [e["slug"] for e in events]:
        responses[f"{slug}/releases"] = {"releases": releases.get(slug, []),
                                         "meta": {"next_page": None}}
    return responses


def fake_get(responses, calls=None):
    """Stand-in for build.get that serves v3 fixtures by path and page number."""
    def get(url, headers=None, timeout=30):
        assert url.startswith("https://api.tito.io/v3/sense-respond-learning/"), url
        assert headers["Authorization"].startswith("Token token=")
        assert headers["Accept"] == "application/json"
        path, _, query = url[len("https://api.tito.io/v3/sense-respond-learning/"):].partition("?")
        page = int(dict(p.split("=") for p in query.split("&"))["page%5Bnumber%5D"])
        if calls is not None:
            calls.append((path, page))
        body = responses[path]
        return json.dumps(body[page - 1] if isinstance(body, list) else body)
    return get


class ApiPath(unittest.TestCase):
    def test_filters_and_pricing(self):
        today = dt.date.today()
        calls = []
        with mock.patch.object(build, "get", fake_get(api_fixture(today), calls)):
            events = build.fetch_from_api()
        # private, test, not-live, finished, in-progress and starts-today are all excluded.
        self.assertEqual([e["slug"] for e in events], ["public", "sold-out"])
        public = events[0]
        # secret, archived, not_a_ticket and sold-out releases are ignored for the price.
        self.assertEqual(public["price_from"], 1200.0)
        self.assertEqual(public["currency"], "USD")
        self.assertEqual(public["url"], "https://ti.to/sense-respond-learning/public")
        self.assertEqual(public["start"], (today + dt.timedelta(days=30)).isoformat())
        self.assertEqual(public["banner"], "https://example.com/public.png")
        self.assertEqual(public["timezone"], "Central Time (US & Canada)")
        self.assertIs(public["sold_out"], False)
        self.assertIs(events[1]["sold_out"], True)
        self.assertIsNone(events[1]["price_from"])  # every public release is sold out
        self.assertIsNone(public["region"])
        self.assertEqual(events[1]["region"], "Americas & Europe")
        # Releases are fetched only for the events that survive the filters.
        self.assertEqual([c[0] for c in calls],
                         ["events", "public/releases", "sold-out/releases"])

    def test_follows_next_page(self):
        today = dt.date.today()
        responses = api_fixture(today)
        everything = responses["events"]["events"]
        responses["events"] = [{"events": everything[:3], "meta": {"next_page": 2}},
                               {"events": everything[3:], "meta": {"next_page": None}}]
        calls = []
        with mock.patch.object(build, "get", fake_get(responses, calls)):
            events = build.fetch_from_api()
        self.assertIn("sold-out", [e["slug"] for e in events])
        self.assertEqual(calls[:2], [("events", 1), ("events", 2)])


class Regions(unittest.TestCase):
    def test_extraction(self):
        r = build.region_from_description
        self.assertEqual(r('<p><i class="fa-light fa-globe"></i> Americas &amp; Europe\n<br>'),
                         "Americas & Europe")
        self.assertEqual(r('<i class="fa-light fa-globe"></i> Asia-Pacific, Middle East &amp; Africa'),
                         "Asia-Pacific, Middle East & Africa")
        self.assertEqual(r('<i class="fa-globe"></i>**Americas & Europe**'), "Americas & Europe")
        for nothing in (None, "", "Just a description.", {"html": "x"}):
            self.assertIsNone(r(nothing))


class Banners(unittest.TestCase):
    def test_doubled_v3_url(self):
        good = "https://do3z7e6uuakno.cloudfront.net/uploads/event/banner/1164882/264e.png"
        doubled = "https://do3z7e6uuakno.cloudfront.net/uploads/event/banner/1164882/" + good
        self.assertEqual(build.banner_url(doubled), good)

    def test_normal_and_missing(self):
        self.assertEqual(build.banner_url("https://example.com/b.png"), "https://example.com/b.png")
        self.assertIsNone(build.banner_url(None))
        self.assertIsNone(build.banner_url(""))


class SoldOut(unittest.TestCase):
    def test_rules(self):
        self.assertIsNone(build.sold_out([]))
        self.assertIsNone(build.sold_out([{"secret": True, "sold_out": True}]))
        self.assertTrue(build.sold_out([{"sold_out": True}, {"state_name": "sold_out"}]))
        self.assertFalse(build.sold_out([{"sold_out": True}, {"sold_out": False}]))
        self.assertTrue(build.sold_out([{"sold_out": True}, {"archived": True}]))


class Zones(unittest.TestCase):
    def z(self, tz, start="2026-10-19"):
        return build.format_zone({"timezone": tz, "start": start})

    def test_zone_without_times(self):
        self.assertEqual(self.z("Central Time (US & Canada)"), "Time zone: CDT (Central Time, US & Canada)")
        self.assertEqual(self.z("Central Time (US & Canada)", "2026-12-02"),
                         "Time zone: CST (Central Time, US & Canada)")
        self.assertEqual(self.z("Berlin", "2026-12-02"), "Time zone: CET (Berlin)")
        self.assertEqual(self.z("New Delhi"), "Time zone: IST (New Delhi)")
        self.assertEqual(self.z("Buenos Aires"), "Time zone: UTC-03:00 (Buenos Aires)")
        self.assertEqual(self.z("America/Chicago"), "Time zone: CDT (Chicago)")
        self.assertEqual(self.z("Somewhere Odd"), "Time zone: Somewhere Odd")

    def test_utc_default_and_missing_skipped(self):
        self.assertEqual(self.z("UTC"), "")
        self.assertEqual(self.z(None), "")
        self.assertEqual(self.z("Berlin", None), "")


class Times(unittest.TestCase):
    def label(self, start_at, end_at, tz):
        return build.format_times(*build.local_times(
            {"start_at": start_at, "end_at": end_at, "timezone": tz}))

    def test_rails_zone_name(self):
        self.assertEqual(self.label("2026-10-13T09:00:00.000-05:00", "2026-10-27T11:00:00.000-05:00",
                                    "Central Time (US & Canada)"), "9:00–11:00 AM CDT")

    def test_iana_zone_and_meridiem_change(self):
        self.assertEqual(self.label("2026-12-02T10:00:00+01:00", "2026-12-02T16:30:00+01:00",
                                    "Europe/Berlin"), "10:00 AM–4:30 PM CET")

    def test_utc_input_converted_to_event_zone(self):
        self.assertEqual(self.label("2026-10-13T14:00:00Z", "2026-10-13T16:00:00Z",
                                    "America/Chicago"), "9:00–11:00 AM CDT")

    def test_zone_without_abbreviation_uses_offset(self):
        self.assertEqual(self.label("2026-10-10T18:00:00+05:30", "2026-10-10T22:00:00+05:30",
                                    "Chennai"), "6:00–10:00 PM IST")
        self.assertEqual(self.label("2026-10-28T17:00:00-03:00", "2026-10-28T19:30:00-03:00",
                                    "Buenos Aires"), "5:00–7:30 PM UTC-03:00")

    def test_unknown_zone_uses_timestamp_offset(self):
        self.assertEqual(self.label("2026-10-13T09:00:00-05:00", "2026-10-13T11:00:00-05:00",
                                    "Somewhere Odd"), "9:00–11:00 AM UTC-05:00")

    def test_midnight_to_midnight_means_no_time_entered(self):
        # What the live v3 data returned on 30 September 2026 for every event.
        self.assertEqual(self.label("2026-10-13T00:00:00.000Z", "2026-10-27T00:00:00.000Z", "UTC"), "")
        self.assertEqual(self.label("2026-09-17T00:00:00.000-05:00", "2026-10-08T00:00:00.000-05:00",
                                    "Central Time (US & Canada)"), "")
        self.assertEqual(build.local_times({"start_at": "2026-10-13T00:00:00Z",
                                            "end_at": "2026-10-13T00:00:00Z",
                                            "timezone": "UTC"}), (None, None))

    def test_missing_or_naive_gives_nothing(self):
        self.assertEqual(self.label(None, None, "UTC"), "")
        self.assertEqual(self.label("2026-10-13T09:00:00", "2026-10-13T11:00:00", "UTC"), "")


class TimelineScrape(unittest.TestCase):
    def test_synthetic_markup(self):
        with mock.patch.object(build, "get", return_value=read_fixture("timeline-synthetic.html")):
            events = build.fetch_from_timeline()
        self.assertEqual([e["title"] for e in events],
                         ["Lean Product Management & Friends", "Objectives & Key Results"])
        self.assertEqual(events[0]["date_label"], "October 13th–27th, 2026")
        self.assertEqual(events[0]["banner"], "https://example.com/b1.png")
        self.assertIsNone(events[0]["location"])
        self.assertEqual(events[1]["location"], "Berlin Mitte")
        self.assertEqual(events[1]["url"], "https://ti.to/sense-respond-learning/okr-berlin?a=1&b=2")

    def test_client_rendered_page_yields_nothing(self):
        # What ti.to/sense-respond-learning/ actually returned on 30 September 2026.
        with mock.patch.object(build, "get",
                               return_value=read_fixture("timeline-2026-09-30-client-rendered.html")):
            self.assertEqual(build.fetch_from_timeline(), [])


class Dedupe(unittest.TestCase):
    def ev(self, slug, location=None):
        return {"title": "Lean Product Strategy", "slug": slug, "start": "2026-09-29",
                "end": "2026-10-01", "date_label": "x", "location": location}

    def test_collapses_identical(self):
        kept, dropped = build.dedupe([self.ev("lps-1"), self.ev("lps-2")])
        self.assertEqual([e["slug"] for e in kept], ["lps-1"])
        self.assertEqual([e["slug"] for e in dropped], ["lps-2"])

    def test_different_regions_kept(self):
        # The 2027 sequence runs each course twice on the same dates, once per region.
        kept, dropped = build.dedupe([dict(self.ev("lps-1"), region="Americas & Europe"),
                                      dict(self.ev("lps-2"), region="Asia-Pacific, Middle East & Africa")])
        self.assertEqual(len(kept), 2)
        self.assertEqual(dropped, [])

    def test_different_locations_kept(self):
        kept, dropped = build.dedupe([self.ev("a", "Berlin"), self.ev("b", "London")])
        self.assertEqual(len(kept), 2)
        self.assertEqual(dropped, [])


if __name__ == "__main__":
    unittest.main()

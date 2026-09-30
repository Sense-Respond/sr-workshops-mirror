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

    def test_unknown_currency(self):
        self.assertEqual(build.format_price(500, "CHF"), "500 CHF")


def api_fixture(today):
    """A JSON:API payload shaped like Ti.to v2 /events?include=releases."""
    iso = lambda d: d.isoformat() + "T09:00:00.000-05:00"  # noqa: E731
    later = today + dt.timedelta(days=30)

    def event(eid, slug, releases=(), **attrs):
        base = {"title": f"Event {slug}", "slug": slug, "start-date": iso(later),
                "end-date": iso(later + dt.timedelta(days=2)), "live": True,
                "private": False, "test-mode": False, "currency": "USD", "location": None}
        base.update(attrs)
        return {"id": eid, "type": "events", "attributes": base,
                "relationships": {"releases": {"data": [
                    {"id": r, "type": "releases"} for r in releases]}}}

    events = [
        event("1", "public", releases=["r1", "r2", "r3", "r4"]),
        event("2", "private", private=True),
        event("3", "test", **{"test-mode": True}),
        event("4", "not-live", live=False),
        event("5", "finished", **{"start-date": iso(today - dt.timedelta(days=5)),
                                   "end-date": iso(today - dt.timedelta(days=1))}),
        event("6", "ends-today", **{"start-date": iso(today - dt.timedelta(days=2)),
                                     "end-date": iso(today)}),
    ]
    included = [
        {"id": "r1", "type": "releases", "attributes": {"price": "1200.0"}},
        {"id": "r2", "type": "releases", "attributes": {"price": "100.0", "secret": True}},
        {"id": "r3", "type": "releases", "attributes": {"price": "50.0", "archived": True}},
        {"id": "r4", "type": "releases", "attributes": {"price": "0.0", "not-a-ticket": True}},
    ]
    return {"data": events, "included": included, "links": {}}


class ApiPath(unittest.TestCase):
    def test_filters_and_pricing(self):
        today = dt.date.today()
        payload = json.dumps(api_fixture(today))
        with mock.patch.object(build, "get", return_value=payload):
            events = build.fetch_from_api()
        slugs = [e["slug"] for e in events]
        self.assertEqual(slugs, ["public", "ends-today"])
        public = events[0]
        self.assertEqual(public["price_from"], 1200.0)  # secret, archived, not-a-ticket ignored
        self.assertEqual(public["currency"], "USD")
        self.assertEqual(public["url"], "https://ti.to/sense-respond-learning/public")
        self.assertEqual(public["start"], (today + dt.timedelta(days=30)).isoformat())

    def test_follows_next_link(self):
        today = dt.date.today()
        page1 = api_fixture(today)
        page2 = {"data": [page1["data"].pop()], "included": [], "links": {}}
        page1["links"] = {"next": "https://api.tito.io/v2/x/events?page=2"}
        responses = iter([json.dumps(page1), json.dumps(page2)])
        with mock.patch.object(build, "get", side_effect=lambda *a, **k: next(responses)):
            events = build.fetch_from_api()
        self.assertIn("ends-today", [e["slug"] for e in events])


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

    def test_different_locations_kept(self):
        kept, dropped = build.dedupe([self.ev("a", "Berlin"), self.ev("b", "London")])
        self.assertEqual(len(kept), 2)
        self.assertEqual(dropped, [])


if __name__ == "__main__":
    unittest.main()
